"""
Centralized FAR request deletion (upload file + DB row; rules cascade via ORM).
"""
from __future__ import annotations

import logging
import os

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.project_auth import get_far_request_in_project_or_404
from app.models.far_request import FarRequest
from app.utils.csv_errors import DatabaseConnectionError, FileSystemError

logger = logging.getLogger(__name__)


def delete_far_request(db: Session, project_id: int, request_id: int) -> None:
    """
    Delete one FAR request for a project: optional upload file, then DB row.
    Commits on success. Caller should not hold expectations across rollback —
    filesystem deletes are not transactional with the DB.

    Raises HTTPException (400/404), FileSystemError, DatabaseConnectionError.
    """
    far_request = get_far_request_in_project_or_404(db, request_id, project_id)

    if far_request.status == "processing":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot delete request {request_id} while it is being processed. "
                "Please wait for processing to complete."
            ),
        )

    file_path = None
    if far_request.storage_path:
        file_path = os.path.join(settings.UPLOAD_DIR, far_request.storage_path)

    try:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("Deleted file: %s for request %s", file_path, request_id)
            except FileNotFoundError:
                logger.warning(
                    "File not found for deletion: %s (request %s)", file_path, request_id
                )
            except (PermissionError, OSError) as e:
                logger.error(
                    "Filesystem error deleting file %s: %s", file_path, str(e), exc_info=True
                )
                raise FileSystemError(
                    message=f"Failed to delete file {file_path}: {str(e)}",
                    details={"filename": far_request.source_filename, "path": file_path},
                )
            except Exception as e:
                logger.warning("Error deleting file %s: %s", file_path, str(e))
        elif file_path:
            logger.warning("File path specified but file does not exist: %s", file_path)

        db.delete(far_request)
        db.commit()
        logger.info("Successfully deleted FAR request %s", request_id)
    except (HTTPException, FileSystemError):
        raise
    except OperationalError as e:
        db.rollback()
        logger.error(
            "Database connection error deleting FAR request %s: %s",
            request_id,
            str(e),
            exc_info=True,
        )
        raise DatabaseConnectionError(
            message="Database connection failed during request deletion",
            details={"error": str(e), "request_id": request_id},
        )
    except Exception as e:
        db.rollback()
        logger.error("Error deleting FAR request %s: %s", request_id, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete request: {str(e)}")


def delete_all_far_requests_for_project(db: Session, project_id: int) -> None:
    """
    Delete every FAR request for project_id using the same rules as delete_far_request.
    Stops and re-raises on first failure; DB state may reflect successfully deleted requests.
    """
    ids = (
        db.query(FarRequest.id)
        .filter(FarRequest.project_id == project_id)
        .order_by(FarRequest.id)
        .all()
    )
    for (rid,) in ids:
        delete_far_request(db, project_id, rid)
