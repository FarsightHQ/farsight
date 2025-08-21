# 🧪 API Testing Guide

## Methods to Test Your Farsight API

### 1. 🌐 FastAPI Interactive Docs (Easiest)
**URL:** http://localhost:8000/docs

- **Pros:** Built-in, interactive, no setup required
- **Features:** Try requests directly, see schemas, automatic validation
- **Best for:** Quick testing, exploring API structure

### 2. 🖥️ Browser Testing (GET only)
**URLs to test:**
- Root: http://localhost:8000/
- Health: http://localhost:8000/health  
- Items: http://localhost:8000/items
- Specific item: http://localhost:8000/items/1

### 3. 🔧 Command Line (cURL)
**Run the test script:**
```bash
./test_api.sh
```

**Manual cURL examples:**
```bash
# Get all items
curl http://localhost:8000/items

# Create an item
curl -X POST "http://localhost:8000/items?name=My%20Item&description=Test%20item"

# Get specific item
curl http://localhost:8000/items/1
```

### 4. 🐍 Python Script (Advanced)
**Install requests first:**
```bash
pip install requests
```

**Run the Python test:**
```bash
python test_api.py
```

### 5. 📱 HTTP Clients (Professional)
**Popular options:**
- **Postman** - Full-featured GUI
- **Insomnia** - Lightweight alternative  
- **HTTPie** - Command line tool
- **VS Code REST Client** - Extension for VS Code

#### VS Code REST Client Example:
Create a file `api_tests.http`:
```http
### Get root
GET http://localhost:8000/

### Get health
GET http://localhost:8000/health

### Get all items
GET http://localhost:8000/items

### Create item
POST http://localhost:8000/items?name=Test Item&description=A test item

### Get specific item
GET http://localhost:8000/items/1
```

## 🎯 Current API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/health` | Health check |
| GET | `/items` | Get all items |
| POST | `/items` | Create new item |
| GET | `/items/{id}` | Get specific item |

## 📊 Expected Responses

### Successful Item Creation:
```json
{
  "id": 1,
  "name": "Test Item",
  "description": "A test item",
  "created_at": "2025-08-21T10:29:20.420700"
}
```

### Error Response (404):
```json
{
  "detail": "Item not found"
}
```

## 🚀 Quick Start Testing

1. **Ensure services are running:**
   ```bash
   docker-compose ps
   ```

2. **Test basic connectivity:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Open interactive docs:**
   - Go to http://localhost:8000/docs
   - Click "Try it out" on any endpoint
   - Fill in parameters and click "Execute"

## 🛠️ Troubleshooting

### Service not responding:
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs backend

# Restart if needed
docker-compose restart backend
```

### Connection refused:
- Verify port 8000 is not in use by another service
- Check if Docker is running
- Ensure all containers are healthy
