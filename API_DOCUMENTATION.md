# Farsight API Documentation

## 🚀 Available Documentation Interfaces

Your Farsight API now has **auto-updating Swagger documentation** available at multiple endpoints:

### **1. Built-in FastAPI Swagger UI** ✨
- **URL**: http://localhost:8000/docs
- **Features**: 
  - Interactive API testing
  - Auto-updates when you modify API endpoints
  - Built into FastAPI backend
  - Try API calls directly from the browser

### **2. Built-in ReDoc Documentation** 📚
- **URL**: http://localhost:8000/redoc
- **Features**:
  - Clean, readable documentation
  - Better for API reference
  - Auto-generated from OpenAPI schema

### **3. Standalone Swagger UI Service** 🐳
- **URL**: http://localhost:8080
- **Features**:
  - Dedicated Docker container
  - Independent of backend restarts
  - Custom styling options
  - Always available

### **4. OpenAPI Schema (JSON)** 🔧
- **URL**: http://localhost:8000/openapi.json
- **Features**:
  - Raw OpenAPI 3.1.0 specification
  - Use with external tools (Postman, Insomnia, etc.)
  - API client generation

## 🎯 Quick Start

1. **Start all services**:
   ```bash
   docker compose up -d
   ```

2. **Visit the documentation**:
   - Main Swagger UI: http://localhost:8000/docs
   - Standalone Swagger: http://localhost:8080
   - ReDoc: http://localhost:8000/redoc

3. **Test an API**:
   - Go to http://localhost:8000/docs
   - Click "Try it out" on any endpoint
   - Enter parameters and execute

## 📝 Documentation Features

### **Auto-Updating**
- Documentation automatically updates when you:
  - Add new endpoints
  - Modify existing endpoints
  - Change request/response models
  - Update descriptions or examples

### **Enhanced API Docs Include**:
- ✅ **Request/Response examples**
- ✅ **Error codes and descriptions** 
- ✅ **Parameter validation**
- ✅ **Interactive testing**
- ✅ **Model schemas**
- ✅ **Security requirements**

### **Current API Endpoints**:
- `POST /api/v1/ingest` - Upload CSV files
- `POST /api/v1/requests/{id}/facts/compute` - Compute rule facts
- `POST /api/v1/requests/{id}/facts/compute-hybrid` - Hybrid analysis
- `GET /api/v1/requests/{id}/analysis` - Get comprehensive analysis
- `GET /health` - Health check
- `GET /` - Root endpoint

## 🛠 Docker Services

Your `docker-compose.yml` now includes:

```yaml
swagger-ui:
  image: swaggerapi/swagger-ui:latest
  container_name: farsight_swagger
  ports:
    - "8080:8080"
  environment:
    API_URL: http://localhost:8000/openapi.json
```

## 🔄 Development Workflow

1. **Modify API endpoints** in your FastAPI code
2. **Restart backend**: `docker compose restart backend`
3. **Documentation auto-updates** at all URLs
4. **Test changes** interactively in Swagger UI

## 📱 External Tool Integration

Use the OpenAPI schema with:
- **Postman**: Import from http://localhost:8000/openapi.json
- **Insomnia**: Load OpenAPI spec
- **API Client Generation**: Use with swagger-codegen
- **Testing Tools**: Use with API testing frameworks

---

**Your API documentation is now live and auto-updating!** 🎉
