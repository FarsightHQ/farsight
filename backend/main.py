from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://farsight_user:farsight_password@localhost:5432/farsight")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="Farsight API", version="1.0.0")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to Farsight API", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items

@app.post("/items")
def create_item(name: str, description: str | None = None, db: Session = Depends(get_db)):
    db_item = Item(name=name, description=description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
