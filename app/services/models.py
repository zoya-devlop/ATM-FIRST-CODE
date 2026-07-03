from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.services.database import Base

class StoreItem(Base):
    __tablename__ = "store_items"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)  # Identifies owner (e.g., 'zoy', 'swiggy')
    barcode = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)  # Identifies owner (e.g., 'zomato')
    name = Column(String, index=True)
    region = Column(String)
    
    # Relationships - Automatically deletes instances/buckets if project is deleted
    instances = relationship("Instance", back_populates="project", cascade="all, delete-orphan")
    buckets = relationship("Bucket", back_populates="project", cascade="all, delete-orphan")

class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)  # Direct tenant access for performance
    name = Column(String)
    vcpu = Column(Integer)
    memory_gb = Column(Integer)
    
    # Strict Enterprise Foreign Key
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    project = relationship("Project", back_populates="instances")

class Bucket(Base):
    __tablename__ = "buckets"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)  # Direct tenant access for performance
    name = Column(String)
    
    # Strict Enterprise Foreign Key
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    project = relationship("Project", back_populates="buckets")