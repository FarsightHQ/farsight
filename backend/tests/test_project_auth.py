"""Unit tests for project authorization helpers."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.project_auth import require_project_access, user_has_platform_admin_bypass


@patch("app.core.project_auth.get_project_or_404")
def test_legacy_unrestricted_skips_membership(mock_get_project):
    mock_get_project.return_value = MagicMock(legacy_unrestricted=True)
    db = MagicMock()
    project = require_project_access(db, 1, {"sub": "user-1"}, "admin")
    assert project.legacy_unrestricted is True


@patch("app.core.project_auth.get_project_or_404")
def test_platform_admin_bypass(mock_get_project):
    mock_get_project.return_value = MagicMock(legacy_unrestricted=False)
    db = MagicMock()
    project = require_project_access(
        db, 1, {"sub": "user-1", "roles": ["farsight-admin"]}, "owner"
    )
    assert project is not None


@patch("app.core.project_auth.get_project_or_404")
def test_member_insufficient_role(mock_get_project):
    mock_get_project.return_value = MagicMock(legacy_unrestricted=False)
    db = MagicMock()
    member_q = MagicMock()
    member_q.filter.return_value.first.return_value = MagicMock(role="viewer")
    db.query.return_value = member_q

    with pytest.raises(HTTPException) as ei:
        require_project_access(db, 1, {"sub": "user-1"}, "admin")
    assert ei.value.status_code == 403


@patch("app.core.project_auth.get_project_or_404")
def test_not_a_member(mock_get_project):
    mock_get_project.return_value = MagicMock(legacy_unrestricted=False)
    db = MagicMock()
    member_q = MagicMock()
    member_q.filter.return_value.first.return_value = None
    db.query.return_value = member_q

    with pytest.raises(HTTPException) as ei:
        require_project_access(db, 1, {"sub": "user-1"}, "viewer")
    assert ei.value.status_code == 403


def test_user_has_platform_admin_bypass():
    assert user_has_platform_admin_bypass({"roles": ["farsight-admin"]}) is True
    assert user_has_platform_admin_bypass({"roles": ["admin"]}) is True
    assert user_has_platform_admin_bypass({"roles": ["viewer"]}) is False
