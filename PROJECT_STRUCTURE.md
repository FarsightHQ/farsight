# Project Structure Guide

## 📁 Clean Project Organization

```
farsight/
├── README.md                    # Main project documentation
├── docker-compose.yml           # Docker orchestration
├── .env                        # Environment configuration
├── .gitignore                  # Git ignore rules
├── backend/                    # Main application
│   ├── app/                    # Modular FastAPI application
│   ├── alembic/                # Database migrations
│   ├── uploads/                # File storage
│   └── requirements.txt        # Python dependencies
├── docs/                       # Project documentation
│   ├── API_TESTING_GUIDE.md    # API testing documentation
│   ├── FAR_SYSTEM_DOCS.md      # FAR system documentation
│   ├── MIGRATION_GUIDE.md      # Migration guide
│   └── MODULAR_STRUCTURE.md    # Architecture documentation
└── tests/                      # Test files and utilities
    ├── test_api.py             # Python API test script
    ├── test_api.sh             # Bash API test script
    └── sample_data/            # Test data files
        ├── test_data.csv       # Small test CSV
        ├── 338817.csv          # Network data sample
        ├── 339215.csv          # Network data sample
        └── test_file.txt       # Non-CSV test file
```

## 🚀 Quick Start

1. **Start the application:**
   ```bash
   docker-compose up -d
   ```

2. **Run tests:**
   ```bash
   cd tests
   chmod +x test_api.sh
   ./test_api.sh
   ```

3. **Access documentation:**
   - API Docs: http://localhost:8000/docs
   - Project Docs: See `docs/` directory

## 📚 Documentation

All project documentation is organized in the `docs/` directory:
- API testing guides and examples
- System architecture documentation
- Migration and setup guides

## 🧪 Testing

Test scripts and sample data are in the `tests/` directory:
- Python and bash test scripts
- Sample CSV files for testing uploads
- Test utilities and helpers
