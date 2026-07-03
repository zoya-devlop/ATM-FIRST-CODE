print("FILE RUNNING")
import os
<<<<<<< HEAD
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
=======
import subprocess
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status, Depends
from fastapi.responses import HTMLResponse
>>>>>>> c811f18c4885e1b1043028d003c48fa786ce2a85
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session
import docker
import random

<<<<<<< HEAD
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
=======
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

# ---------------- CONFIG ----------------
APP_NAME = os.getenv("APP_NAME", "Zoya Cloud")
APP_ENV = os.getenv("APP_ENV", "development")

DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@zoya.com")
DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "Admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "123456")
DEFAULT_API_TOKEN = os.getenv("DEFAULT_API_TOKEN", "zoya-token")


# ---------------- APP ----------------
app = FastAPI(
    title=APP_NAME,
    version="1.0.0"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "zoya_secret"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

users = []

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("sub")
 
# ---------------- UTILS ----------------
def utc_now():
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str):
    return "-".join(value.lower().strip().split())


# ---------------- DOCKER ----------------
def create_container():
    try:
        result = subprocess.run(
            ["docker", "run", "-d", "-p", "8090:80", "nginx"],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return str(e)


# ---------------- AUTH ----------------
def require_token(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "").strip()

    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, email, name, api_token FROM users WHERE api_token = ?",
            (token,),
        ).fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return dict(user)


# ---------------- ROUTES ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": APP_NAME,
        "default_email": DEFAULT_ADMIN_EMAIL,
        "default_password": DEFAULT_ADMIN_PASSWORD,
        "default_token": DEFAULT_API_TOKEN,
        "app_env": APP_ENV
    })


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "environment": APP_ENV,
        "time": utc_now()
    }


from datetime import datetime

servers = []

@app.post("/create-server")
def create_server(name: str):
    servers.append({"name": name})
    return {"message": "Server created"}

@app.get("/servers")
def get_servers():
    return servers


# ---------------- LOGIN ----------------
class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, email, name, password, api_token FROM users WHERE email = ?",
            (payload.email,),
        ).fetchone()

    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
>>>>>>> c811f18c4885e1b1043028d003c48fa786ce2a85

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
<<<<<<< HEAD
        "status": "success",
        "total_payable": total_amount,
        "security_exit_token": f"ZOY-EXIT-{total_amount}-ITEMS-{len(itemized_bill)}",
        "message": f"🔒 Payment Success for tenant: {tenant_id.upper()}!"
    }


# =====================================================================
# 🌐 ZOY'S OMNI-MATRIX (ZOM) P2P NETWORK APIs
# =====================================================================
=======
        "token": user["api_token"],
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }


# ---------------- USER ----------------
@app.get("/api/me")
def me(current_user: dict = Depends(require_token)):
    return {"user": current_user}
>>>>>>> c811f18c4885e1b1043028d003c48fa786ce2a85

class NodeJoinRequest(BaseModel):
    device_id: str
    device_type: str        
    ip_address: str
    total_storage_mb: float

<<<<<<< HEAD
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
=======
# ---------------- PROJECT CREATE ----------------
class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    region: str = Field(min_length=2, max_length=40)


@app.post("/api/projects")
def create_project(payload: ProjectCreate, current_user: dict = Depends(require_token)):
    created_at = utc_now()
    slug = f"{slugify(payload.name)}-{secrets.token_hex(2)}"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO projects (name, slug, region, owner_email, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.name, slug, payload.region, current_user["email"], created_at),
        )

    return {"status": "project created", "slug": slug}

@app.get("/servers")
def list_servers():
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.ID}} {{.Image}} {{.Status}}"],
            capture_output=True,
            text=True
        )
        servers = result.stdout.strip().split("\n")
        return {"servers": servers}
    except Exception as e:
        return {"error": str(e)}
    
    
@app.delete("/delete-server/{container_id}")
def delete_server(container_id: str):
    import docker

    client = docker.from_env()

    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
        return {"status": "deleted"}
    except Exception as e:
        return {"error": str(e)}
    
    @app.post("/register")
    def register(email: str, password: str):
        hashed = hash_password(password)
        users.append({"email": email, "password": hashed})
        return {"message": "User registered"}
   
from fastapi import Form

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    for user in users:
        if user["email"] == username and verify_password(password, user["password"]):
            token = create_token({"sub": username})
            return {"access_token": token}
    return {"error": "Invalid credentials"}

@app.get("/protected")
def protected(token: str = Depends(oauth2_scheme)):
    return {"message": "You are logged in"}

@app.post("/register")
def register(email: str, password: str):
    hashed = hash_password(password)
    users.append({"email": email, "password": hashed})
    return {"message": "User registered"}


@app.get("/")
def home():
    return {"msg": "Zoya Cloud running"}

@app.get("/servers")
def get_servers():
    return users

servers = []

@app.post("/create-server")
def create_server(name: str):
    servers.append({"name": name})
    return {"message": "Server created"}

@app.get("/servers")
def get_servers():
    return servers

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.delete("/delete-server")
def delete_server(name: str):
    global servers
    servers = [s for s in servers if s["name"] != name]
    return {"message": "Deleted"}
>>>>>>> c811f18c4885e1b1043028d003c48fa786ce2a85
