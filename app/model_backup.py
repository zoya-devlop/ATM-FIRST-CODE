import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, Header  # 👈 Added Header here
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Boolean
import docker
import random

# Database aur Models (Wapas sahi path par set kar diya)
from app.services.database import engine, Base, get_db
from app.services import models
from app.services.models import StoreItem, Project, Instance, Bucket

# Routers
from app.routers.dashboard import router as dashboard_router
from app.routers.projects import router as projects_router
from app.routers.auth import router as auth_router
from app.routers.instances import router as instances_router
from app.routers.buckets import router as buckets_router
from app.routers.clusters import router as clusters_router

app = FastAPI()

# Database Init
models.Base.metadata.create_all(bind=engine)

# 🚀 DOCKER ENGINE SETUP
try:
    docker_client = docker.from_env()
    print("✅ Docker Engine Connected Successfully!")
except Exception as e:
    print(f"⚠️ Docker Engine Error: {e}")
    docker_client = None

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Routers Setup
app.include_router(buckets_router)
app.include_router(clusters_router)
app.include_router(dashboard_router)
app.include_router(projects_router)
app.include_router(auth_router)
app.include_router(instances_router)


# --- 🛡️ MULTI-TENANT GATEWAY DEPENDENCY ---
# Yeh function har incoming request ka header scan karega
def get_current_tenant(x_tenant_id: str = Header(None)):
    if not x_tenant_id:
        raise HTTPException(
            status_code=400, 
            detail="❌ Header 'X-Tenant-ID' missing! Kripya apni Company (Tenant) ka naam batayein."
        )
    return x_tenant_id.lower()


# =====================================================================
# 🚀 CORE CLOUD & SCAN-&-GO LOGIC (NOW MULTI-TENANT SECURED)
# =====================================================================

# 1. THE REAL INSTANCE ENGINE (Compute powered by Docker)
@app.post("/api/instances/")
def create_instance(
    name: str, 
    project_id: int, 
    vcpu: int, 
    memory_gb: int, 
    tenant_id: str = Depends(get_current_tenant),  # 👈 Tenant captured from header
    db: Session = Depends(get_db)
):
    try:
        host_port = 0
        
        # Agar Docker chal raha hai toh real container banao
        if docker_client:
            host_port = random.randint(10000, 60000) 
            container = docker_client.containers.run(
                "nginx:alpine",
                name=f"zoy-cloud-{name}-{random.randint(100, 999)}",
                detach=True,
                ports={'80/tcp': host_port}
            )
        
        # Database mein record save karna with tenant encapsulation
        new_inst = Instance(
            tenant_id=tenant_id,  # 👈 Saved tenant context safely
            name=name, 
            project_id=project_id, 
            vcpu=vcpu, 
            memory_gb=memory_gb
        )
        db.add(new_inst)
        db.commit()
        db.refresh(new_inst)
        
        msg = f"Server '{name}' is LIVE on Port {host_port}! 🚀" if docker_client else "Mock Server Created (Docker not running)."
        return {"status": "success", "message": msg, "data": new_inst}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start real server: {str(e)}")


# --- 🛡️ THE INSTANCE KILLER (With Multi-Tenant + Sudo PIN Protection) ---
@app.delete("/api/instances/{instance_id}")
def delete_instance(
    instance_id: int, 
    pin: str, 
    tenant_id: str = Depends(get_current_tenant),  # 👈 Tenant authentication
    db: Session = Depends(get_db)
):
    # 🔐 SECURITY CHECK 1: Sudo PIN verification
    if pin != "ZOY-999":
        raise HTTPException(status_code=403, detail="❌ Incorrect Destruction PIN! Server is Safe.")

    try:
        # 🔐 SECURITY CHECK 2: Sirf wahi server milega jo is company (tenant) ka hai
        inst = db.query(Instance).filter(Instance.id == instance_id, Instance.tenant_id == tenant_id).first()
        if not inst:
            raise HTTPException(status_code=404, detail="❌ Server not found or you don't own this instance!")

        # Asli Docker Container ko dhoondh kar kill karna
        if docker_client:
            try:
                container_found = False
                for container in docker_client.containers.list(all=True):
                    if f"zoy-cloud-{inst.name}" in container.name:
                        container.stop()    
                        container.remove()  
                        container_found = True
                        break
                if not container_found:
                    print(f"⚠️ Container for {inst.name} not found in Docker. Deleting from DB only.")
            except Exception as e:
                print(f"⚠️ Docker delete error: {e}")

        # Database se permanently saaf karna
        db.delete(inst)
        db.commit()
        
        return {"status": "success", "message": f"Server '{inst.name}' Destroyed Permanently! 💥"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


# 2. Bucket Create (Storage)
@app.post("/api/buckets/")
def create_bucket(
    name: str, 
    project_id: int, 
    tenant_id: str = Depends(get_current_tenant),  # 👈 Added tenant safety
    db: Session = Depends(get_db)
):
    new_bucket = Bucket(tenant_id=tenant_id, name=name, project_id=project_id)
    db.add(new_bucket)
    db.commit()
    db.refresh(new_bucket)
    return {"status": "success", "message": "Bucket Created!", "data": new_bucket}


# 3. Scan & Go Routes
class ItemCreate(BaseModel):
    barcode: str
    name: str
    price: float

@app.post("/api/add-item/")
def add_new_item(
    item: ItemCreate, 
    tenant_id: str = Depends(get_current_tenant),  # 👈 Isolated item ingestion
    db: Session = Depends(get_db)
):
    new_db_item = StoreItem(tenant_id=tenant_id, barcode=item.barcode, name=item.name, price=item.price)
    db.add(new_db_item)
    db.commit()
    db.refresh(new_db_item)
    return {"status": "success", "data": new_db_item}

@app.get("/api/get-item/{barcode}")
def scan_item(
    barcode: str, 
    tenant_id: str = Depends(get_current_tenant), 
    db: Session = Depends(get_db)
):
    try:
        # Query check karegi ki item usi tenant ka hai ya nahi
        item = db.query(StoreItem).filter(StoreItem.barcode == barcode, StoreItem.tenant_id == tenant_id).first()
        if not item: 
            raise HTTPException(status_code=404, detail=f"❌ Item nahi mila! Tenant '{tenant_id}' ke catalog mein barcode '{barcode}' nahi hai.")
        return {"status": "success", "data": item}
    
    except HTTPException as http_err:
        # Agar humne khud 404 raise kiya hai, toh use seedha bahar jaane do (mask mat pehnao)
        raise http_err
    except Exception as e:
        # Agar sach mein database crash hua, toh hi 500 dikhao
        print(f"\n🔴 REAL DATABASE CRASH: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Database Crash: {str(e)}")

# --- SCAN & GO: MISSING CHECKOUT ADDED BACK ---
class CheckoutRequest(BaseModel):
    barcodes: list[str]

@app.post("/api/checkout/")
def checkout_store_cart(
    request: CheckoutRequest, 
    tenant_id: str = Depends(get_current_tenant),  # 👈 Scoped transaction tracking
    db: Session = Depends(get_db)
):
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


# 4. Domain Mapping
class DomainMapRequest(BaseModel):
    instance_id: str
    custom_domain: str
    internal_ip: str
    internal_port: int

@app.post("/api/v1/cloud/map-domain")
async def map_custom_domain(data: DomainMapRequest):
    return {"status": "success", "message": f"Domain {data.custom_domain} mapped!"}

# =====================================================================

@app.get("/")
def serve_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- SCAN & GO: THE CAMERA SCANNER UI ---
@app.get("/scanner")
def serve_scanner(request: Request):
    return templates.TemplateResponse("scanner.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)