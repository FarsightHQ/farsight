# Error Handling Test Guide

This document provides comprehensive instructions for testing all error handling scenarios in the Farsight application.

## Overview

The error handling system covers:
- **CSV File Errors**: Empty files, wrong file types, file size limits
- **CSV Encoding Errors**: Invalid or corrupted encoding
- **CSV Validation Errors**: Missing headers, malformed structure, duplicate columns
- **CSV Column Errors**: Missing required columns, wrong column names
- **CSV Row Errors**: Invalid IP addresses, invalid ports, empty required fields
- **Database Connection Errors**: Database connectivity issues
- **File System Errors**: File system permission or access issues
- **Insufficient Storage Errors**: Disk space limitations

## Test Files

All test files are located in `tests/test_files/error_scenarios/`:

### 1. CSV File Error Tests

#### 1.1 `empty_file.csv`
- **Purpose**: Test empty file validation
- **Expected Error**: `CSVFileError` - "CSV file is empty"
- **HTTP Status**: 400
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/empty_file.csv"
  ```

#### 1.2 `not_a_csv.txt`
- **Purpose**: Test invalid file type validation
- **Expected Error**: `CSVFileError` - File type validation failure
- **HTTP Status**: 400
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/not_a_csv.txt"
  ```

#### 1.3 `too_large.csv` (Manual Creation)
- **Purpose**: Test file size limit validation
- **Expected Error**: `CSVFileError` - File exceeds maximum size (default: 50MB)
- **HTTP Status**: 400
- **Note**: Create a file larger than 50MB:
  ```bash
  # Create a 60MB file
  dd if=/dev/zero of=tests/test_files/error_scenarios/too_large.csv bs=1M count=60
  ```
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/too_large.csv"
  ```

### 2. CSV Encoding Error Tests

#### 2.1 `invalid_encoding.csv`
- **Purpose**: Test invalid encoding detection
- **Expected Error**: `CSVEncodingError` - Unreadable encoding
- **HTTP Status**: 400
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/invalid_encoding.csv"
  ```

#### 2.2 `corrupted_utf8.csv`
- **Purpose**: Test corrupted UTF-8 encoding
- **Expected Error**: `CSVEncodingError` - Decoding failure
- **HTTP Status**: 400
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/corrupted_utf8.csv"
  ```

### 3. CSV Validation Error Tests

#### 3.1 `no_header.csv`
- **Purpose**: Test missing header row validation
- **Expected Error**: `CSVValidationError` - "CSV file has no header row"
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/no_header.csv"
  ```

#### 3.2 `malformed.csv`
- **Purpose**: Test invalid CSV structure (unclosed quotes, mismatched delimiters)
- **Expected Error**: `CSVValidationError` - Invalid CSV structure
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/malformed.csv"
  ```

#### 3.3 `duplicate_columns.csv`
- **Purpose**: Test duplicate column names validation
- **Expected Error**: `CSVValidationError` - Duplicate column names
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/duplicate_columns.csv"
  ```

### 4. CSV Column Error Tests

#### 4.1 `missing_source.csv`
- **Purpose**: Test missing required column (source)
- **Expected Error**: `CSVColumnError` - Missing required columns: ['source']
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/missing_source.csv"
  ```

#### 4.2 `missing_multiple.csv`
- **Purpose**: Test missing multiple required columns
- **Expected Error**: `CSVColumnError` - Missing required columns: ['source', 'destination']
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/missing_multiple.csv"
  ```

#### 4.3 `wrong_columns.csv`
- **Purpose**: Test completely wrong column names
- **Expected Error**: `CSVColumnError` - Wrong column names (found vs required)
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/wrong_columns.csv"
  ```

### 5. CSV Row Error Tests

#### 5.1 `invalid_ips.csv`
- **Purpose**: Test invalid IP addresses in rows
- **Expected Error**: `CSVRowError` - Invalid IP addresses with row numbers and field errors
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/invalid_ips.csv"
  ```

#### 5.2 `invalid_ports.csv`
- **Purpose**: Test invalid port ranges in rows
- **Expected Error**: `CSVRowError` - Invalid port ranges with row numbers and field errors
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/invalid_ports.csv"
  ```

#### 5.3 `empty_fields.csv`
- **Purpose**: Test empty required fields in rows
- **Expected Error**: `CSVRowError` - Empty required fields with row numbers and field errors
- **HTTP Status**: 422
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/empty_fields.csv"
  ```

### 6. Valid CSV for Comparison

#### 6.1 `valid_sample.csv`
- **Purpose**: Reference file showing correct format
- **Expected**: Should process successfully (HTTP 201)
- **Test Command**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/far" \
    -F "title=Test Request" \
    -F "file=@tests/test_files/error_scenarios/valid_sample.csv"
  ```

## API Endpoints

### FAR Request Upload
- **Endpoint**: `POST /api/v1/far`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `title` (form field): Request title
  - `file` (form field): CSV file to upload
  - `external_id` (optional form field): External identifier

### Asset Registry Upload
- **Endpoint**: `POST /api/v1/assets/upload-csv`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file` (form field): CSV file to upload
  - `uploaded_by` (query parameter): User uploading the file

## Expected Error Response Format

All errors should return a consistent JSON response format:

```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_TYPE",
  "details": {
    "field": "value",
    "row_number": 2,
    "column_name": "source",
    "error": "Specific error message"
  }
}
```

### Error Codes

- `CSV_FILE_ERROR`: File-related issues (empty, wrong type, too large)
- `CSV_ENCODING_ERROR`: Encoding detection or decoding failures
- `CSV_VALIDATION_ERROR`: CSV structure validation failures
- `CSV_COLUMN_ERROR`: Missing or wrong column names
- `CSV_ROW_ERROR`: Invalid data in CSV rows
- `DATABASE_CONNECTION_ERROR`: Database connectivity issues
- `FILE_SYSTEM_ERROR`: File system permission or access issues
- `INSUFFICIENT_STORAGE_ERROR`: Disk space limitations

## Testing Database Connection Errors

Database connection errors cannot be easily triggered with test files. To test:

1. **Stop the database**:
   ```bash
   docker stop farsight_db
   ```

2. **Make any API call** that requires database access:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/far/requests"
   ```

3. **Expected Error**: `DatabaseConnectionError` with HTTP 503

4. **Restart the database**:
   ```bash
   docker start farsight_db
   ```

## Testing File System Errors

File system errors can be tested by:

1. **Remove write permissions** on the upload directory:
   ```bash
   chmod -w backend/uploads
   ```

2. **Try uploading a file**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/far" \
     -F "title=Test Request" \
     -F "file=@tests/test_files/error_scenarios/valid_sample.csv"
   ```

3. **Expected Error**: `FileSystemError` with HTTP 500

4. **Restore permissions**:
   ```bash
   chmod +w backend/uploads
   ```

## Testing Insufficient Storage Errors

Insufficient storage errors can be tested by:

1. **Fill up the disk** (use with caution):
   ```bash
   # Create a large file to fill disk (adjust size as needed)
   dd if=/dev/zero of=/tmp/large_file bs=1M count=1000
   ```

2. **Try uploading a file**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/far" \
     -F "title=Test Request" \
     -F "file=@tests/test_files/error_scenarios/valid_sample.csv"
   ```

3. **Expected Error**: `InsufficientStorageError` with HTTP 507

4. **Clean up**:
   ```bash
   rm /tmp/large_file
   ```

## Automated Testing Script

You can create a Python script to test all scenarios:

```python
import requests
import os
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"
TEST_DIR = Path("tests/test_files/error_scenarios")

test_files = {
    "empty_file.csv": 400,
    "not_a_csv.txt": 400,
    "invalid_encoding.csv": 400,
    "corrupted_utf8.csv": 400,
    "no_header.csv": 422,
    "malformed.csv": 422,
    "duplicate_columns.csv": 422,
    "missing_source.csv": 422,
    "missing_multiple.csv": 422,
    "wrong_columns.csv": 422,
    "invalid_ips.csv": 422,
    "invalid_ports.csv": 422,
    "empty_fields.csv": 422,
    "valid_sample.csv": 201,
}

for filename, expected_status in test_files.items():
    file_path = TEST_DIR / filename
    if not file_path.exists():
        print(f"SKIP: {filename} (file not found)")
        continue
    
    with open(file_path, 'rb') as f:
        files = {'file': (filename, f, 'text/csv')}
        data = {'title': f'Test: {filename}'}
        
        response = requests.post(f"{BASE_URL}/far", files=files, data=data)
        
        status_match = "✓" if response.status_code == expected_status else "✗"
        print(f"{status_match} {filename}: {response.status_code} (expected {expected_status})")
        
        if response.status_code != expected_status:
            print(f"  Response: {response.json()}")
```

## Notes

- All test files should be tested against the FAR request upload endpoint (`/api/v1/far`)
- The same files can also be tested against the asset registry upload endpoint (`/api/v1/assets/upload-csv`)
- Error messages should be clear and actionable
- All errors should include relevant context (row numbers, column names, etc.)
- Database and file system errors require manual intervention to trigger

## CSV Format Requirements

The application expects CSV files with the following columns:

**Required Columns**:
- `source` (or `sources`): Source IP address or CIDR range
- `destination` (or `destinations`): Destination IP address or CIDR range
- `service` (or `services`): Service definition (e.g., `tcp/80`, `udp/53`)

**Optional Columns**:
- `action`: Rule action (`allow` or `deny`)
- `direction`: Traffic direction (`ingress`, `egress`, `bidirectional`)

**Format**:
- Standard CSV with header row
- UTF-8 encoding preferred (but handles UTF-8-BOM, Latin-1, CP1252)
- Comma-separated values
- Properly quoted fields if they contain commas or quotes

## Configuration

Error handling behavior can be configured via environment variables:

- `MAX_UPLOAD_MB`: Maximum file size in MB (default: 50)
- `MIN_DISK_SPACE_MULTIPLIER`: Minimum free disk space multiplier (default: 2.0)
- `CSV_VALIDATION_SAMPLE_SIZE`: Sample size for CSV validation (default: 8192)

Set these in your `.env` file or as environment variables.
