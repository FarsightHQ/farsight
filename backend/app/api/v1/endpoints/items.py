"""
Items API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import Item
from app.schemas import ItemCreate, ItemResponse

# Create router
router = APIRouter(prefix="/items", tags=["Items"])


@router.get("", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    """Get all items"""
    items = db.query(Item).all()
    return items


@router.post("", response_model=ItemResponse)
def create_item(
    item_data: ItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new item"""
    db_item = Item(**item_data.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    """Get item by ID"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
