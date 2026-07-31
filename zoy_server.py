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
    
# ===================================================================================
#                      ZOM CLOUD INFRASTRUCTURE NETWORK SECTION
# ===================================================================================
from app.models.zom_models import Node, IncentiveLedger # Jo file humne abhi banayi thi
import datetime

# --- INFRASTRUCTURE REQUEST SCHEMAS ---
class NodeRegisterRequest(BaseModel):
    node_uuid: str
    owner_wallet: str
    ip_address: str = None

class NodePingRequest(BaseModel):
    node_uuid: str

# --- NODE REGISTRATION ROUTE ---
@app.post("/api/infra/register")
def register_node(request: NodeRegisterRequest, db: Session = Depends(get_db)):
    # Check karo ki kya ye machine pehle se registered hai?
    existing_node = db.query(Node).filter(Node.node_uuid == request.node_uuid).first()
    
    if existing_node:
        return {"success": True, "message": "Node already registered. Active status synchronized."}
    
    # Nayi machine ko matrix network mein insert karo
    new_node = Node(
        node_uuid=request.node_uuid,
        owner_wallet=request.owner_wallet,
        ip_address=request.ip_address,
        current_status="online",
        last_ping=datetime.datetime.utcnow()
    )
    db.add(new_node)
    db.commit()
    
    return {"success": True, "message": f"Node registered successfully under wallet {request.owner_wallet[:8]}..."}

# --- NODE LIFE-SIGNAL (PING) & INCENTIVE TRACKER ---
@app.post("/api/infra/ping")
def node_ping(request: NodePingRequest, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.node_uuid == request.node_uuid).first()
    
    if not node:
        return {"success": False, "message": "Node footprint unrecognized. Please register first."}
    
    now = datetime.datetime.utcnow()
    
    # Simple Uptime Math: Kitni der baad doosra ping aaya
    time_diff = (now - node.last_ping).total_seconds()
    
    # Agar device lagatar connected tha (30-60 secs ke standard bracket mein), toh coins calculate karo
    if node.current_status == "online" and 0 < time_diff < 120:
        # Standard Formula: 1 second online = 0.001 ZOY Coins
        reward_amount = time_diff * 0.001
        
        # 1. Update system ledger passbook
        ledger_entry = IncentiveLedger(
            node_id=node.id,
            amount_credited=reward_amount,
            session_uptime_seconds=int(time_diff)
        )
        db.add(ledger_entry)
        
        # 2. Sync node status update
        node.last_ping = now
        db.commit()
        
        return {
            "success": True, 
            "status": "online", 
            "reward_credited": reward_amount,
            "message": "Uptime verified. Shard splitting capability secure."
        }
    else:
        # Agar bohot dino baad ping aaya ya pehli baar online ho rha hai
        node.current_status = "online"
        node.last_ping = now
        db.commit()
        
        return {"success": True, "status": "online", "reward_credited": 0.0, "message": "Session initialized."}

    return {
        "success": True,
        "added_item": item.name,
        "cart_count": cart_count,
        "basket_total": basket_total
    }