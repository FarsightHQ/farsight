"""
Comprehensive CSV validation service with detailed error reporting
"""
import csv
import io
import chardet
from typing import Dict, List, Optional, Tuple, Any
from app.utils.csv_errors import (
    CSVValidationError, CSVColumnError, CSVEncodingError, CSVFileError
)


class CSVValidationService:
    """Service for validating CSV files before processing"""
    
    # Required columns (case-insensitive)
    REQUIRED_COLUMNS = {
        'source': ['source', 'sources'],
        'destination': ['destination', 'destinations'],
        'service': ['service', 'services']
    }
    
    # Optional columns
    OPTIONAL_COLUMNS = {
        'action': ['action'],
        'direction': ['direction']
    }
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_ROWS = 1000000  # 1 million rows
    MAX_COLUMNS = 100
    
    @staticmethod
    def validate_file_structure(
        file_content: bytes,
        filename: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Validate CSV file structure and detect encoding
        
        Args:
            file_content: Raw file content as bytes
            filename: Optional filename for error messages
            
        Returns:
            Tuple of (decoded_content, metadata)
            
        Raises:
            CSVFileError: If file is empty or too large
            CSVEncodingError: If encoding cannot be detected or file cannot be decoded
        """
        # Check file size
        file_size = len(file_content)
        if file_size == 0:
            raise CSVFileError(
                "CSV file is empty",
                filename=filename,
                file_size=file_size
            )
        
        if file_size > CSVValidationService.MAX_FILE_SIZE:
            raise CSVFileError(
                f"CSV file too large: {file_size} bytes. Maximum: {CSVValidationService.MAX_FILE_SIZE} bytes",
                filename=filename,
                file_size=file_size
            )
        
        # Detect encoding
        try:
            detected = chardet.detect(file_content)
            encoding = detected.get('encoding', 'utf-8')
            confidence = detected.get('confidence', 0)
            
            if confidence < 0.7:
                # Try common encodings
                for enc in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                    try:
                        file_content.decode(enc)
                        encoding = enc
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise CSVEncodingError(
                        "Could not detect file encoding",
                        detected_encoding=encoding
                    )
        except Exception as e:
            raise CSVEncodingError(
                f"Error detecting file encoding: {str(e)}"
            )
        
        # Decode content
        try:
            decoded_content = file_content.decode(encoding)
        except UnicodeDecodeError as e:
            raise CSVEncodingError(
                f"Failed to decode file with {encoding} encoding: {str(e)}",
                detected_encoding=encoding
            )
        
        metadata = {
            "encoding": encoding,
            "file_size": file_size,
            "confidence": confidence
        }
        
        return decoded_content, metadata
    
    @staticmethod
    def validate_csv_structure(
        csv_content: str,
        filename: Optional[str] = None
    ) -> Tuple[List[str], Dict[str, str]]:
        """
        Validate CSV structure and return column mapping
        
        Args:
            csv_content: Decoded CSV content as string
            filename: Optional filename for error messages
            
        Returns:
            Tuple of (fieldnames, column_mapping)
            
        Raises:
            CSVValidationError: If CSV structure is invalid
            CSVColumnError: If required columns are missing or duplicates exist
        """
        try:
            # Try to read CSV
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            fieldnames = csv_reader.fieldnames
            
            if not fieldnames:
                raise CSVValidationError(
                    "CSV file has no header row",
                    details={"filename": filename}
                )
            
            # Clean column names (remove BOM, whitespace)
            clean_fieldnames = [
                col.strip().lstrip('\ufeff').strip() 
                for col in fieldnames
            ]
            
            # Check for duplicate columns
            seen = {}
            duplicates = []
            for i, col in enumerate(clean_fieldnames):
                col_lower = col.lower()
                if col_lower in seen:
                    duplicates.append(col)
                else:
                    seen[col_lower] = i
            
            if duplicates:
                raise CSVColumnError(
                    f"Duplicate columns found: {', '.join(duplicates)}",
                    found_columns=clean_fieldnames
                )
            
            # Check column count
            if len(clean_fieldnames) > CSVValidationService.MAX_COLUMNS:
                raise CSVColumnError(
                    f"Too many columns: {len(clean_fieldnames)}. Maximum: {CSVValidationService.MAX_COLUMNS}",
                    found_columns=clean_fieldnames
                )
            
            # Find required columns
            column_mapping = {}
            missing_columns = []
            
            for logical_name, possible_names in CSVValidationService.REQUIRED_COLUMNS.items():
                found = False
                for i, col in enumerate(clean_fieldnames):
                    if col.lower() in [n.lower() for n in possible_names]:
                        column_mapping[logical_name] = fieldnames[i]  # Use original name
                        found = True
                        break
                
                if not found:
                    missing_columns.append(f"{logical_name} ({'/'.join(possible_names)})")
            
            if missing_columns:
                raise CSVColumnError(
                    f"Missing required columns: {', '.join(missing_columns)}",
                    missing_columns=missing_columns,
                    found_columns=clean_fieldnames
                )
            
            # Find optional columns
            for logical_name, possible_names in CSVValidationService.OPTIONAL_COLUMNS.items():
                for i, col in enumerate(clean_fieldnames):
                    if col.lower() in [n.lower() for n in possible_names]:
                        column_mapping[logical_name] = fieldnames[i]
                        break
            
            return fieldnames, column_mapping
            
        except csv.Error as e:
            raise CSVValidationError(
                f"CSV parsing error: {str(e)}",
                details={"filename": filename, "error_type": type(e).__name__}
            )
        except Exception as e:
            if isinstance(e, (CSVValidationError, CSVColumnError)):
                raise
            raise CSVValidationError(
                f"Unexpected error validating CSV structure: {str(e)}",
                details={"filename": filename}
            )
    
    @staticmethod
    def validate_row_count(csv_content: str) -> int:
        """
        Validate and count rows in CSV
        
        Args:
            csv_content: Decoded CSV content as string
            
        Returns:
            Number of data rows (excluding header)
            
        Raises:
            CSVValidationError: If CSV has no data rows or too many rows
        """
        try:
            reader = csv.reader(io.StringIO(csv_content))
            row_count = sum(1 for row in reader) - 1  # Subtract header
            
            if row_count == 0:
                raise CSVValidationError(
                    "CSV file contains no data rows (only header)",
                    details={"row_count": 0}
                )
            
            if row_count > CSVValidationService.MAX_ROWS:
                raise CSVValidationError(
                    f"CSV file has too many rows: {row_count}. Maximum: {CSVValidationService.MAX_ROWS}",
                    details={"row_count": row_count}
                )
            
            return row_count
            
        except csv.Error as e:
            raise CSVValidationError(
                f"Error counting CSV rows: {str(e)}"
            )

