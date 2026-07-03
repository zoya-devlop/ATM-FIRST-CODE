from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.services.database import Base

# ==========================================
# 🏢 TRADITIONAL MULTI-TENANT RESOURCES
# ==========================================

class StoreItem(Base):
    __tablename__ = "store_items"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    barcode = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    name = Column(String, index=True)
    region = Column(String)
    
    instances = relationship("Instance", back_populates="project", cascade="all, delete-orphan")
    buckets = relationship("Bucket", back_populates="project", cascade="all, delete-orphan")

class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    name = Column(String)
    vcpu = Column(Integer)
    memory_gb = Column(Integer)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    project = relationship("Project", back_populates="instances")

class Bucket(Base):
    __tablename__ = "buckets"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    name = Column(String)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    project = relationship("Project", back_populates="buckets")


# ==========================================
# 🌐 ZOY'S OMNI-MATRIX (ZOM) P2P NETWORK
# ==========================================

class EdgeNode(Base):
    __tablename__ = "edge_nodes"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)  
    device_id = Column(String, unique=True, index=True)     
    ip_address = Column(String)
    device_type = Column(String)                            
    total_storage_mb = Column(Float)
    available_storage_mb = Column(Float)
    health_score = Column(Float, default=100.0)             
    is_online = Column(Boolean, default=True)               

    shards = relationship("FileShard", back_populates="node", cascade="all, delete-orphan")


class FileShard(Base):
    __tablename__ = "file_shards"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    original_file_id = Column(String, index=True)           
    shard_index = Column(Integer)                           
    node_id = Column(Integer, ForeignKey("edge_nodes.id", ondelete="CASCADE"), nullable=False)
    is_safe = Column(Boolean, default=True)                 
    
    # 🌟 Nayi Fields: Shard ka real file path aur unique hash verification ke liye
    shard_path = Column(String, nullable=True)
    shard_hash = Column(String, nullable=True)

    node = relationship("EdgeNode", back_populates="shards")