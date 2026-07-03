import sys
import os

# Ensure Python reads from your root folder
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.database import SessionLocal, engine, Base
from sqlalchemy import Column, Integer, String, Float

print("Initializing Zoy Database Engine...")

class StoreItem(Base):
    __tablename__ = "store_items"
    __table_args__ = {'extend_existing': True} 
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)

# Connect to database
Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    # Instead of checking if the table is empty, we specifically check for OUR barcode
    zoy_item = db.query(StoreItem).filter(StoreItem.barcode == "QR_ZOY_001").first()

    if not zoy_item:
        print("Zoy products missing. Forcing Hoodies and Mugs into the database...")
        
        item1 = StoreItem(barcode="QR_ZOY_001", name="Premium Hoodie", price=2499.0)
        item2 = StoreItem(barcode="QR_ZOY_002", name="Zoy Tech Mug", price=499.0)
        item3 = StoreItem(barcode="QR_ZOY_003", name="Wireless Earbuds", price=4999.0)
        
        db.add_all([item1, item2, item3])
        db.commit()
        
        print("Success: Zoy items successfully injected into the database!")
    else:
        print("Success: Zoy items are already in the database.")

except Exception as e:
    print(f"Error occurred: {e}")

finally:
    db.close()
    print("Setup Complete.")