import sys
import os

# Ensure Python reads from your root folder
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.database import SessionLocal, engine
from app.models.models import StoreItem, Project, Instance, Bucket

print("Initializing Multi-Tenant Data Seeding...")

db = SessionLocal()

try:
    # 1. Clear old data to prevent conflicts during transition
    db.query(Instance).delete()
    db.query(Bucket).delete()
    db.query(Project).delete()
    db.query(StoreItem).delete()
    db.commit()
    print("Database cleared for fresh multi-tenant seeding.")

    # ---- TENANT 1: ZOY (Super App E-Commerce) ----
    print("\nSeeding Tenant: Zoy...")
    item1 = StoreItem(tenant_id="zoy", barcode="QR_ZOY_001", name="Premium Hoodie", price=2499.0)
    item2 = StoreItem(tenant_id="zoy", barcode="QR_ZOY_002", name="Zoy Tech Mug", price=499.0)
    db.add_all([item1, item2])

    # ---- TENANT 2: ZOMATO (Food Delivery Infra) ----
    print("Seeding Tenant: Zomato...")
    zomato_proj = Project(tenant_id="zomato", name="Zomato-Prod-Cluster", region="ap-south-1")
    db.add(zomato_proj)
    db.flush()  # Gets the project ID

    zomato_vm1 = Instance(tenant_id="zomato", project_id=zomato_proj.id, name="Delivery-API-Node-1", vcpu=4, memory_gb=16)
    zomato_bkt1 = Bucket(tenant_id="zomato", project_id=zomato_proj.id, name="zomato-restaurant-images")
    db.add_all([zomato_vm1, zomato_bkt1])

    # ---- TENANT 3: SWIGGY (Competitor Infra) ----
    print("Seeding Tenant: Swiggy...")
    swiggy_proj = Project(tenant_id="swiggy", name="Swiggy-Core-Backend", region="ap-south-1")
    db.add(swiggy_proj)
    db.flush()  # Gets the project ID

    swiggy_vm1 = Instance(tenant_id="swiggy", project_id=swiggy_proj.id, name="Swiggy-Instamart-DB", vcpu=8, memory_gb=32)
    swiggy_bkt1 = Bucket(tenant_id="swiggy", project_id=swiggy_proj.id, name="swiggy-user-bills-2026")
    db.add_all([swiggy_vm1, swiggy_bkt1])

    # Commit all changes permanently
    db.commit()
    print("\nSuccess: Multi-tenant data successfully injected into OrbitCloud PostgreSQL!")

except Exception as e:
    db.rollback()
    print(f"Error occurred during seeding: {e}")

finally:
    db.close()
    print("Seeding Process Complete.")