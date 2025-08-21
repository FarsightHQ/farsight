# 📄 FAR (File Analysis Request) System Documentation

## Overview

The FAR system provides a robust CSV file upload and management solution with PostgreSQL storage, file validation, and comprehensive metadata tracking.

## 🎯 Features

- ✅ **CSV File Upload** - Secure file upload with validation
- ✅ **File Validation** - Size limits, type checking, SHA-256 integrity
- ✅ **Metadata Management** - Titles, external IDs, creator tracking
- ✅ **Database Storage** - PostgreSQL with migration support
- ✅ **Organized Storage** - Date-based directory structure
- ✅ **Comprehensive Logging** - Full audit trail
- ✅ **RESTful API** - Clean, documented endpoints

## 📋 Database Schema

### `far_requests` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGSERIAL | Primary key |
| `title` | TEXT | Request title (NOT NULL) |
| `external_id` | TEXT | Optional external reference |
| `source_filename` | TEXT | Original filename (NOT NULL) |
| `source_sha256` | TEXT | File integrity hash (NOT NULL) |
| `source_size_bytes` | BIGINT | File size in bytes (NOT NULL) |
| `storage_path` | TEXT | Relative storage path (NOT NULL) |
| `status` | TEXT | Processing status (default: 'submitted') |
| `created_by` | TEXT | Creator identifier (default: 'system') |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

## 🚀 API Endpoints

### Upload CSV File

**`POST /ingest/far`**

Upload a CSV file for FAR processing.

**Request:**
- Content-Type: `multipart/form-data`
- **file** (required): CSV file (max 50MB)
- **title** (optional): Request title (derived from filename if not provided)
- **external_id** (optional): External reference ID
- **created_by** (optional): Creator identifier (defaults to "system")

**Response:**
```json
{
  "request_id": 123,
  "status": "submitted",
  "file": {
    "filename": "data.csv",
    "sha256": "abcdef123456...",
    "size_bytes": 12345,
    "storage_path": "2025/08/22/uuid__data.csv"
  },
  "metadata": {
    "title": "Data Analysis Request",
    "external_id": "EXT-001",
    "created_by": "user123"
  }
}
```

**Error Responses:**
- `400` - Invalid file type or validation error
- `413` - File too large (>50MB)
- `500` - Server error during processing

### Get FAR Request

**`GET /ingest/far/{request_id}`**

Retrieve details of a specific FAR request.

**Response:**
```json
{
  "request_id": 123,
  "status": "submitted",
  "title": "Data Analysis Request",
  "external_id": "EXT-001",
  "source_filename": "data.csv",
  "source_sha256": "abcdef123456...",
  "source_size_bytes": 12345,
  "storage_path": "2025/08/22/uuid__data.csv",
  "created_by": "user123",
  "created_at": "2025-08-22T10:30:00Z"
}
```

### List FAR Requests

**`GET /ingest/far`**

List FAR requests with pagination.

**Query Parameters:**
- `limit` (default: 100): Maximum number of records
- `offset` (default: 0): Number of records to skip

**Response:**
```json
{
  "requests": [
    {
      "request_id": 123,
      "status": "submitted",
      "title": "Data Analysis Request",
      "external_id": "EXT-001",
      "source_filename": "data.csv",
      "created_by": "user123",
      "created_at": "2025-08-22T10:30:00Z"
    }
  ],
  "limit": 100,
  "offset": 0
}
```

## 🧪 Testing Examples

### Basic Upload
```bash
curl -X POST "http://localhost:8000/ingest/far" \
  -F "file=@data.csv" \
  -F "title=My Analysis" \
  -F "external_id=EXT-123" \
  -F "created_by=user456"
```

### Minimal Upload (title derived from filename)
```bash
curl -X POST "http://localhost:8000/ingest/far" \
  -F "file=@employee_data.csv"
```

### List Requests
```bash
curl "http://localhost:8000/ingest/far?limit=10&offset=0"
```

### Get Specific Request
```bash
curl "http://localhost:8000/ingest/far/123"
```

## 📁 File Storage Structure

Files are stored in a date-based directory hierarchy:

```
uploads/
├── 2025/
│   ├── 08/
│   │   ├── 21/
│   │   │   ├── uuid1__filename1.csv
│   │   │   └── uuid2__filename2.csv
│   │   └── 22/
│   │       └── uuid3__filename3.csv
│   └── 09/
│       └── ...
└── 2024/
    └── ...
```

**Storage Path Format:** `YYYY/MM/DD/{uuid4()}__{safe_filename}`

## ⚙️ Configuration

Environment variables (in `.env`):

```bash
# File Upload Configuration
UPLOAD_DIR=./uploads          # Base upload directory
MAX_UPLOAD_MB=50              # Maximum file size in MB

# Logging
LOG_LEVEL=INFO                # Logging level
```

## 🔒 Security Features

- **File Type Validation** - Only `.csv` files accepted
- **Size Limits** - Configurable maximum file size (default 50MB)
- **Filename Sanitization** - Removes unsafe characters
- **SHA-256 Integrity** - File hash for integrity verification
- **Unique Storage Names** - UUIDs prevent filename collisions

## 📊 Monitoring & Logging

All uploads are logged with:
- Original filename
- SHA-256 hash
- Request ID
- User/creator information
- Upload timestamp
- File size

**Log Format:**
```
2025-08-22 10:30:00 - services - INFO - FAR request created successfully: ID=123, File=data.csv, SHA256=abcdef...
```

## 🛠️ Database Operations

### Create Migration
```bash
docker-compose exec backend alembic revision --autogenerate -m "Update far_requests table"
```

### Apply Migrations
```bash
docker-compose exec backend alembic upgrade head
```

### Check Database
Access the database via pgAdmin at http://localhost:5050 or connect directly:
```bash
docker-compose exec postgres psql -U farsight_user -d farsight -c "SELECT * FROM far_requests;"
```

## 🚨 Error Handling

The system provides comprehensive error handling:

1. **Validation Errors** (400)
   - Invalid file type
   - Missing required fields
   - Malformed requests

2. **Size Limit Errors** (413)
   - Files exceeding MAX_UPLOAD_MB

3. **Server Errors** (500)
   - Database connection issues
   - File system errors
   - Unexpected exceptions

All errors include descriptive messages and proper HTTP status codes.

## 🔄 Status Management

Current status values:
- `submitted` - Initial upload complete
- (Future: `processing`, `completed`, `failed`, etc.)

## 📈 Performance Considerations

- **Streaming Upload** - Files processed in 8KB chunks
- **Async Processing** - Non-blocking file operations
- **Database Indexing** - Optimized queries on common fields
- **File Organization** - Date-based directory structure for performance

## 🎯 Interactive API Documentation

Access the interactive API documentation at:
**http://localhost:8000/docs**

This provides:
- Live API testing
- Request/response schemas
- Parameter documentation
- Example requests
