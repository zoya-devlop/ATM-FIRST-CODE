from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.database import get_db
from models import StoreItem

app = FastAPI(title="Zoy Super App API")

# --- API REQUEST MODEL ---
class ScanRequest(BaseModel):
    user_id: str
    barcode: str

# --- TEMPORARY CART MEMORY ---
user_carts = {}

# --- SCAN & GO API ROUTE ---
@app.post("/api/scan")
def api_scan(request: ScanRequest, db: Session = Depends(get_db)):
    
    # Step 1: Fetch item from the database
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