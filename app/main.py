import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
import docker
import random

# Database aur Models Connection (Direct from Folder Init)
from app.services.database import engine, Base, get_db
import app.models as models
from app.models import StoreItem, Project, Instance, Bucket, EdgeNode, FileShard

# Routers Setup
from app.routers.dashboard import router as dashboard_router
from app.routers.projects import router as projects_router
from app.routers.auth import router as auth_router
from app.routers.instances import router as instances_router
from app.routers.buckets import router as buckets_router
from app.routers.clusters import router as clusters_router

# ⭐ SAKSHAT APP SWITCH (Jise Uvicorn Dhoondh Raha Hai)
app = FastAPI(title="Zoy Omni-Matrix Core Engine", version="3.0.0")

# Database Table Initialization
models.Base.metadata.create_all(bind=engine)

# Real Docker client connector
try:
    docker_client = docker.from_env()
    print("✅ Docker Engine Connected Successfully!")
except Exception as e:
    print(f"⚠️ Docker Engine Error: {e}")
    docker_client = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(buckets_router)
app.include_router(clusters_router)
app.include_router(dashboard_router)
app.include_router(projects_router)
app.include_router(auth_router)
app.include_router(instances_router)


def get_current_tenant(x_tenant_id: str = Header(None)):
    if not x_tenant_id:
        raise HTTPException(
            status_code=400, 
            detail="❌ Header 'X-Tenant-ID' missing! Kripya Tenant (e.g. 'genx') ka naam batayein."
        )
    return x_tenant_id.lower()


# =====================================================================
# 🚀 CORE CLOUD LOGIC (DOCKER COMPUTE ENGINE)
# =====================================================================

@app.post("/api/instances/")
def create_instance(name: str, project_id: int, vcpu: int, memory_gb: int, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    try:
        host_port = 0
        if docker_client:
            host_port = random.randint(10000, 60000) 
            docker_client.containers.run(
                "nginx:alpine",
                name=f"zoy-cloud-{name}-{random.randint(100, 999)}",
                detach=True,
                ports={'80/tcp': host_port}
            )
        
        new_inst = Instance(tenant_id=tenant_id, name=name, project_id=project_id, vcpu=vcpu, memory_gb=memory_gb)
        db.add(new_inst)
        db.commit()
        db.refresh(new_inst)
        
        msg = f"Server '{name}' is LIVE on Port {host_port}! 🚀" if docker_client else "Mock Server Created (Docker not running)."
        return {"status": "success", "message": msg, "data": new_inst}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start real server: {str(e)}")

@app.delete("/api/instances/{instance_id}")
def delete_instance(instance_id: int, pin: str, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    if pin != "ZOY-999":
        raise HTTPException(status_code=403, detail="❌ Incorrect Destruction PIN! Server is Safe.")
    try:
        inst = db.query(Instance).filter(Instance.id == instance_id, Instance.tenant_id == tenant_id).first()
        if not inst:
            raise HTTPException(status_code=404, detail="❌ Server not found or access denied!")

        if docker_client:
            try:
                for container in docker_client.containers.list(all=True):
                    if f"zoy-cloud-{inst.name}" in container.name:
                        container.stop()    
                        container.remove()  
                        break
            except Exception as e:
                print(f"⚠️ Docker delete error: {e}")

        db.delete(inst)
        db.commit()
        return {"status": "success", "message": f"Server '{inst.name}' Destroyed Permanently! 💥"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.post("/api/buckets/")
def create_bucket(name: str, project_id: int, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    new_bucket = Bucket(tenant_id=tenant_id, name=name, project_id=project_id)
    db.add(new_bucket)
    db.commit()
    db.refresh(new_bucket)
    return {"status": "success", "message": "Bucket Created!", "data": new_bucket}


# =====================================================================
# 🛒 SCAN & GO E-COMMERCE ENDPOINTS
# =====================================================================

class ItemCreate(BaseModel):
    barcode: str
    name: str
    price: float

@app.post("/api/add-item/")
def add_new_item(item: ItemCreate, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    new_db_item = StoreItem(tenant_id=tenant_id, barcode=item.barcode, name=item.name, price=item.price)
    db.add(new_db_item)
    db.commit()
    db.refresh(new_db_item)
    return {"status": "success", "data": new_db_item}

@app.get("/api/get-item/{barcode}")
def scan_item(barcode: str, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    try:
        item = db.query(StoreItem).filter(StoreItem.barcode == barcode, StoreItem.tenant_id == tenant_id).first()
        if not item: 
            raise HTTPException(status_code=404, detail=f"❌ Item nahi mila! Tenant '{tenant_id}' ke catalog mein barcode '{barcode}' nahi hai.")
        return {"status": "success", "data": item}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database Crash: {str(e)}")

class CheckoutRequest(BaseModel):
    barcodes: list[str]

@app.post("/api/checkout/")
def checkout_store_cart(request: CheckoutRequest, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    total_amount = 0.0
    itemized_bill = []
    for barcode in request.barcodes:
        item = db.query(StoreItem).filter(StoreItem.barcode == barcode, StoreItem.tenant_id == tenant_id).first()
        if item:
            total_amount += item.price
            itemized_bill.append({"name": item.name, "price": item.price, "barcode": item.barcode})
    if not itemized_bill:
        return {"status": "error", "message": "❌ Cart khali hai!"}
    return {
        "status": "success",
        "total_payable": total_amount,
        "security_exit_token": f"ZOY-EXIT-{total_amount}-ITEMS-{len(itemized_bill)}",
        "message": f"🔒 Payment Success for tenant: {tenant_id.upper()}!"
    }


# =====================================================================
# 🌐 ZOY'S OMNI-MATRIX (ZOM) P2P NETWORK APIs
# =====================================================================

class NodeJoinRequest(BaseModel):
    device_id: str
    device_type: str        
    ip_address: str
    total_storage_mb: float

@app.post("/api/v1/zom/node/join")
def join_zom_network(request: NodeJoinRequest, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    existing_node = db.query(EdgeNode).filter(EdgeNode.device_id == request.device_id).first()
    if existing_node:
        existing_node.is_online = True
        existing_node.ip_address = request.ip_address
        existing_node.available_storage_mb = request.total_storage_mb
        db.commit()
        return {"status": "success", "message": "Node re-connected!", "data": {"node_id": existing_node.id}}
    
    new_node = EdgeNode(
        tenant_id=tenant_id, device_id=request.device_id, device_type=request.device_type,
        ip_address=request.ip_address, total_storage_mb=request.total_storage_mb,
        available_storage_mb=request.total_storage_mb, is_online=True, health_score=100.0
    )
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    return {"status": "success", "message": "Welcome to ZOM Network!", "data": {"node_id": new_node.id}}

class AllocationRequest(BaseModel):
    file_size_mb: float
    shards_needed: int

@app.post("/api/v1/zom/network/allocate")
def allocate_shards(request: AllocationRequest, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    available_nodes = db.query(EdgeNode).filter(
        EdgeNode.tenant_id == tenant_id,
        EdgeNode.is_online == True,
        EdgeNode.health_score > 50.0  
    ).limit(request.shards_needed).all()

    if len(available_nodes) < request.shards_needed:
        raise HTTPException(
            status_code=503, 
            detail=f"Network low capacity! Need {request.shards_needed} nodes, but only {len(available_nodes)} are active."
        )
    node_list = [{"node_id": n.id, "ip": n.ip_address, "device": n.device_type} for n in available_nodes]
    return {
        "status": "success", 
        "message": "Traffic Routed Successfully. Shards allocated.",
        "allocated_nodes": node_list
    }


# =====================================================================
# 🖥️ DOMAIN & UI ROUTING
# =====================================================================

class DomainMapRequest(BaseModel):
    instance_id: str
    custom_domain: str
    internal_ip: str
    internal_port: int

@app.post("/api/v1/cloud/map-domain")
async def map_custom_domain(data: DomainMapRequest):
    return {"status": "success", "message": f"Domain {data.custom_domain} mapped!"}

@app.get("/")
def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/scanner")
def serve_scanner(request: Request):
    return templates.TemplateResponse("scanner.html", {"request": request})

# =====================================================================
# 🧠 ZOM AUTO-HEALING & FAILOVER ENGINE
# =====================================================================

class HeartbeatUpdate(BaseModel):
    device_id: str
    is_online: bool
    available_storage_mb: float

@app.post("/api/v1/zom/node/heartbeat")
def process_node_heartbeat(request: HeartbeatUpdate, db: Session = Depends(get_db)):
    """
    Har device har 5 second mein yeh signal bhejega.
    Agar koi device signal bhejna band karega, toh system use offline mark kar dega.
    """
    node = db.query(EdgeNode).filter(EdgeNode.device_id == request.device_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="❌ Node registered nahi hai!")
    
    node.is_online = request.is_online
    node.available_storage_mb = request.available_storage_mb
    
    # Agar device baar-baar disconnect ho rha hai toh health score kam karo
    if not request.is_online and node.health_score > 10:
        node.health_score -= 10.0  # Punishment for going offline
    
    db.commit()
    return {
        "status": "success", 
        "device": request.device_id, 
        "current_health": node.health_score,
        "state": "🟢 Online" if request.is_online else "🔴 Offline"
    }

@app.get("/api/v1/zom/network/failover/{original_file_id}")
def handle_node_failover(original_file_id: str, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    """
    Zomato Style Automatic Failover!
    Agar user ki file load hote waqt pata chale ki assigned node offline hai,
    toh yeh API turant doosra standby online node dhoondh ke degi.
    """
    # 1. Dekho ki backup ke liye kaunse nodes abhi ekdum online aur healthy hain
    backup_node = db.query(EdgeNode).filter(
        EdgeNode.tenant_id == tenant_id,
        EdgeNode.is_online == True,
        EdgeNode.health_score >= 80.0
    ).first()

    if not backup_node:
        raise HTTPException(
            status_code=503, 
            detail="⚠️ Critical: Pure network mein koi bhi backup node online nahi mila!"
        )

    return {
        "status": "🟢 Auto-Healing Success",
        "message": f"Purana device down tha. Traffic automatically re-routed!",
        "new_assigned_node": {
            "node_id": backup_node.id,
            "ip": backup_node.ip_address,
            "device": backup_node.device_type
        }
    }

# =====================================================================
# 📂 ZOM CRYPTOGRAPHIC SHARD SPLITTER ENGINE
# =====================================================================
import math
import hashlib

# Storage directory jahan physically shards simulate honge
UPLOAD_DIR = "zom_storage_shards"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/v1/zom/network/upload-file")
async def upload_and_split_file(
    file_id: str, 
    file_content: str, 
    shards_needed: int = 3, 
    tenant_id: str = Depends(get_current_tenant), 
    db: Session = Depends(get_db)
):
    """
    Real-time Splitter! Yeh API file content ko leti hai, use chunks mein divide
    karti hai, aur available active nodes par distribute karne ka logic set karti hai.
    """
    # 1. Check karo ki network mein required healthy nodes hain ya nahi
    active_nodes = db.query(EdgeNode).filter(
        EdgeNode.tenant_id == tenant_id,
        EdgeNode.is_online == True,
        EdgeNode.health_score >= 80.0
    ).limit(shards_needed).all()

    if len(active_nodes) < shards_needed:
        raise HTTPException(
            status_code=503, 
            detail=f"❌ Storage Allocation Failed! Network par kafi nodes online nahi hain."
        )

    # 2. File content ko encryption hash dena aur split karna
    data_bytes = file_content.encode('utf-8')
    total_size = len(data_bytes)
    chunk_size = math.ceil(total_size / shards_needed)
    
    saved_shards_info = []

    # 3. Physically chunks kaatna aur database mein metadata map karna
    for i in range(shards_needed):
        start = i * chunk_size
        end = min(start + chunk_size, total_size)
        chunk_data = data_bytes[start:end]
        
        # Har chunk ka ek unique cryptographic hash generate karna security ke liye
        chunk_hash = hashlib.sha256(chunk_data).hexdigest()
        
        # Local system par secure chunk file write karna
        shard_filename = f"{tenant_id}_{file_id}_part_{i}.zom"
        shard_file_path = os.path.join(UPLOAD_DIR, shard_filename)
        
        with open(shard_file_path, "wb") as f:
            f.write(chunk_data)
            
        # Target node select karna list se
        assigned_node = active_nodes[i % len(active_nodes)]
        
        # Database mein entry push karna
        new_shard = FileShard(
            tenant_id=tenant_id,
            original_file_id=file_id,
            shard_index=i,
            node_id=assigned_node.id,
            shard_path=shard_file_path,
            shard_hash=chunk_hash,
            is_safe=True
        )
        db.add(new_shard)
        
        saved_shards_info.append({
            "shard_index": i,
            "allocated_node_id": assigned_node.id,
            "node_device": assigned_node.device_type,
            "shard_hash_verified": chunk_hash[:10] + "..."
        })
        
    db.commit()
    
    return {
        "status": "🟢 Matrix Distribution Success",
        "file_id": file_id,
        "total_shards_created": shards_needed,
        "distribution_map": saved_shards_info
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
