print("FILE RUNNING")
import os
import sys
import math
import random
import hashlib
import datetime
import secrets
import docker
from typing import Any

from fastapi import FastAPI, Request, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Ensure Python reads from your root folder
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Database aur Models Connection
from app.services.database import engine, Base, get_db
import app.models as models
from app.models import StoreItem, Project, Instance, Bucket, EdgeNode, FileShard, DataShard

# APP INITIALIZATION
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

# Static and Templates Setup (Fallbacks handled gracefully)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates") if os.path.exists("templates") else None

def get_current_tenant(x_tenant_id: str = Header(None)):
    if not x_tenant_id:
        raise HTTPException(
            status_code=400, 
            detail="❌ Header 'X-Tenant-ID' missing! Kripya Tenant (e.g. 'genx') ka naam batayein."
        )
    return x_tenant_id.lower()

# =====================================================================
# 🚀 CORE CLOUD LOGIC (QUANTUM-READY COMPUTE ENGINE WITH IPC)
# =====================================================================

class InstanceCreate(BaseModel):
    name: str
    project_id: int
    vcpu: int
    memory_gb: int
    is_isolated: bool = False  

SECURE_STORAGE_PATH = os.path.abspath("zom_storage_shards")
os.makedirs(SECURE_STORAGE_PATH, exist_ok=True)

@app.post("/api/instances/")
def create_instance(data: InstanceCreate, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    try:
        host_port = 0
        container_msg = "Mock Server Created (Docker not running)."
        
        if docker_client:
            if data.is_isolated:
                docker_client.containers.run(
                    "python:3.10-slim",
                    name=f"zoy-quantum-sandbox-{data.name}-{random.randint(100, 999)}",
                    detach=True,
                    network_disabled=True, 
                    mem_limit=f"{data.memory_gb}g",
                    cpu_quota=data.vcpu * 100000,
                    volumes={SECURE_STORAGE_PATH: {'bind': '/secure_data', 'mode': 'rw'}},
                    command="tail -f /dev/null" 
                )
                container_msg = f"🔒 Zero-Trust Quantum Sandbox '{data.name}' is LIVE! (IPC Tunnel Active)"
            else:
                host_port = random.randint(10000, 60000) 
                docker_client.containers.run(
                    "nginx:alpine",
                    name=f"zoy-cloud-{data.name}-{random.randint(100, 999)}",
                    detach=True,
                    ports={'80/tcp': host_port}
                )
                container_msg = f"🌐 Web Server '{data.name}' is LIVE on Port {host_port}! 🚀"
        
        proj_exists = db.query(Project).filter(Project.id == data.project_id).first()
        if not proj_exists:
            default_proj = Project(id=data.project_id, tenant_id=tenant_id, name=f"Quantum-Lab-{data.project_id}", region="Default-Region")
            db.add(default_proj)
            db.commit()

        new_inst = Instance(
            tenant_id=tenant_id, 
            name=data.name, 
            project_id=data.project_id, 
            vcpu=data.vcpu, 
            memory_gb=data.memory_gb
        )
        db.add(new_inst)
        db.commit()
        db.refresh(new_inst)
        
        return {"status": "success", "message": container_msg, "data": new_inst}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start compute engine: {str(e)}")

# =====================================================================
# 📂 NEW: DATA SHARDS TRACKING ENDPOINT (DECENTRALIZED STORAGE MAP)
# =====================================================================

class DataShardCreate(BaseModel):
    instance_id: int
    shard_index: int
    node_location: str
    checksum: str

@app.post("/api/v1/zom/shards/create")
def create_data_shard(data: DataShardCreate, tenant_id: str = Depends(get_current_tenant), db: Session = Depends(get_db)):
    try:
        new_shard = DataShard(
            tenant_id=tenant_id,
            instance_id=data.instance_id,
            shard_index=data.shard_index,
            node_location=data.node_location,
            checksum=data.checksum
        )
        db.add(new_shard)
        db.commit()
        db.refresh(new_shard)
        return {"status": "success", "message": "Data shard registered successfully!", "data": new_shard}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shard creation failed: {str(e)}")

@app.get("/")
def home(request: Request):
    if templates:
        return templates.TemplateResponse("index.html", {"request": request, "app_name": "Zoy Engine"})
    return {"msg": "Zoy Cloud running directly"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)