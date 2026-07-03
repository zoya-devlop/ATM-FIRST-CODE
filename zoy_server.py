import sys
import os
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float

# Ensure Python reads from your root folder
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.database import get_db, Base

app = FastAPI(title="Zoy Super App API")

# --- THE OVERRIDE HACK (Database Model) ---
class StoreItem(Base):
    __tablename__ = "store_items"
    __table_args__ = {'extend_existing': True} 
    
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)

# --- API REQUEST MODEL ---
class ScanRequest(BaseModel):
    user_id: str
    barcode: str

# --- TEMPORARY CART MEMORY ---
user_carts = {}

# --- SCAN & GO API ROUTE ---
@app.post("/api/scan")
def api_scan(request: ScanRequest, db: Session = Depends(get_db)):
    
    # Step 1: Fetch item from the real OrbitCloud database
    item = db.query(StoreItem).filter(StoreItem.barcode == request.barcode).first()
    
    if not item:
        return {"success": False, "message": "Invalid Barcode - Item not found in database."}
    
    # Step 2: Initialize user cart if not exists
    if request.user_id not in user_carts:
        user_carts[request.user_id] = []
    
    cart = user_carts[request.user_id]
    
    # Step 3: Update quantity or add new item
    existing_item = next((i for i in cart if i["barcode"] == request.barcode), None)
    
    if existing_item:
        existing_item["quantity"] += 1
        existing_item["item_total"] = existing_item["price"] * existing_item["quantity"]
    else:
        cart.append({
            "barcode": item.barcode,
            "name": item.name,
            "price": item.price,
            "quantity": 1,
            "item_total": item.price
        })
        
    # Step 4: Calculate totals
    basket_total = sum(i["item_total"] for i in cart)
    cart_count = sum(i["quantity"] for i in cart)
    
    return {
        "success": True,
        "added_item": item.name,
        "cart_count": cart_count,
        "basket_total": basket_total
    }