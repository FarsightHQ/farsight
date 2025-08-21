# 🗄️ Database Migration Guide

## Overview

This project uses **Alembic** for database migrations, providing version control for your database schema changes.

## 🚀 Quick Commands

### Using Docker (Recommended for Production)

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "Description of changes"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Check current migration
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history --verbose

# Downgrade to previous migration
docker-compose exec backend alembic downgrade -1

# Downgrade to specific revision
docker-compose exec backend alembic downgrade <revision_id>
```

### Using the Migration Script

```bash
# Navigate to backend directory
cd backend

# Create a new migration
python migrate.py create "Add user table"

# Apply all pending migrations
python migrate.py upgrade

# Show migration history
python migrate.py history

# Show current migration
python migrate.py current

# Downgrade to base (all down)
python migrate.py downgrade
```

## 📋 Migration Workflow

### 1. **Modify Your Models**
Edit `backend/models.py` to add/modify database models:

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

### 2. **Create Migration**
```bash
docker-compose exec backend alembic revision --autogenerate -m "Add users table"
```

### 3. **Review Migration**
Check the generated file in `backend/alembic/versions/` and edit if needed.

### 4. **Apply Migration**
```bash
docker-compose exec backend alembic upgrade head
```

### 5. **Verify Changes**
- Check database in pgAdmin: http://localhost:5050
- Test API endpoints
- Verify data integrity

## 🔧 Advanced Migration Commands

### **Create Empty Migration** (for custom SQL)
```bash
docker-compose exec backend alembic revision -m "Custom data migration"
```

### **SQL Execution in Migration**
```python
def upgrade() -> None:
    # Create custom index
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_users_email_active 
        ON users (email) WHERE active = true
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_email_active")
```

### **Data Migration Example**
```python
def upgrade() -> None:
    # Schema changes first
    op.add_column('users', sa.Column('full_name', sa.String(500)))
    
    # Then data migration
    connection = op.get_bind()
    connection.execute("""
        UPDATE users 
        SET full_name = CONCAT(first_name, ' ', last_name)
        WHERE full_name IS NULL
    """)

def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

## 🚨 Production Best Practices

### **Before Deployment**
1. **Backup Database**
   ```bash
   docker-compose exec postgres pg_dump -U farsight_user farsight > backup.sql
   ```

2. **Test Migration on Staging**
   ```bash
   # Apply to staging first
   docker-compose exec backend alembic upgrade head
   ```

3. **Review Migration SQL**
   ```bash
   # Generate SQL without applying
   docker-compose exec backend alembic upgrade head --sql
   ```

### **Zero-Downtime Migrations**
1. **Additive Changes First** (add columns, tables)
2. **Deploy Code** (backward compatible)
3. **Remove Old Code Dependencies** 
4. **Drop Unused Columns/Tables** (separate migration)

### **Emergency Rollback**
```bash
# Quick rollback to previous migration
docker-compose exec backend alembic downgrade -1

# Rollback to specific version
docker-compose exec backend alembic downgrade abc123def456
```

## 🏗️ Project Structure

```
backend/
├── alembic/                    # Migration configuration
│   ├── versions/              # Migration files
│   ├── env.py                 # Alembic environment
│   └── script.py.mako         # Migration template
├── alembic.ini                # Alembic configuration
├── database.py                # Database connection
├── models.py                  # SQLAlchemy models
├── migrate.py                 # Migration helper script
└── main.py                    # FastAPI application
```

## 🔍 Troubleshooting

### **Migration Conflicts**
```bash
# Check current state
docker-compose exec backend alembic current

# Merge conflicts manually
docker-compose exec backend alembic merge -m "Merge migrations" <rev1> <rev2>
```

### **Force Migration State**
```bash
# Mark migration as applied without running it
docker-compose exec backend alembic stamp <revision_id>

# Reset to head
docker-compose exec backend alembic stamp head
```

### **Reset Everything** (Development Only)
```bash
# Drop all tables and start fresh
docker-compose exec backend alembic downgrade base
docker-compose exec postgres psql -U farsight_user -d farsight -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker-compose exec backend alembic upgrade head
```

## 📊 Migration Status

Check your current migration status:

```bash
# Current version
docker-compose exec backend alembic current

# History with details
docker-compose exec backend alembic history --verbose

# Pending migrations
docker-compose exec backend alembic show --head
```

## ✅ Auto-Migration on Startup

The Docker Compose setup automatically runs migrations on backend startup:

```yaml
command: sh -c "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
```

This ensures your database is always up-to-date when the container starts! 🚀
