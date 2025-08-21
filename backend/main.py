from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import os

# Import our database components
from database import get_db
from models import Item

# FastAPI app
app = FastAPI(
    title="Farsight API", 
    version="1.0.0",
    description="A FastAPI application with PostgreSQL and Alembic migrations"
)

# Dependency to get DB session (removed since it's now in database.py)

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
