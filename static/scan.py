from datetime import datetime

# --- 1. DATA MODELS (Structure) ---
class ProductModel:
    def __init__(self, product_id, name, price, stock):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.stock = stock

class CartItem:
    def __init__(self, product_id, name, price, quantity=1):
        self.product_id = product_id
        self.name = name
        self.price = price
        self.quantity = quantity
        self.item_total = price * quantity

# --- 2. ZOY DATABASE (Abhi ke liye local data) ---
class ZoyDatabase:
    def __init__(self):
        # Yeh hamara temporary Zoy Cloud database hai
        self.products = {
            "QR_ZOY_001": ProductModel("QR_ZOY_001", "Premium Hoodie", 2499.00, 15),
            "QR_ZOY_002": ProductModel("QR_ZOY_002", "Tech Mug", 499.00, 42),
            "QR_ZOY_003": ProductModel("QR_ZOY_003", "Wireless Earbuds", 4999.00, 8)
        }

    def fetch_product_by_qr(self, qr_code):
        return self.products.get(qr_code)

# --- 3. SCAN & GO ENGINE (Main Logic) ---
class ScanAndGoEngine:
    def __init__(self):
        self.user_carts = {} 

    def process_scan(self, user_id, qr_payload, db_connection):
        product_data = db_connection.fetch_product_by_qr(qr_payload)
        
        if not product_data:
            return {"success": False, "message": "Invalid QR Code - Item not found!"}
        
        if product_data.stock < 1:
            return {"success": False, "message": f"{product_data.name} is Out of Stock!"}
        
        if user_id not in self.user_carts:
            self.user_carts[user_id] = []
            
        cart = self.user_carts[user_id]
        
        # Check if item already exists in cart
        existing_item = next((item for item in cart if item.product_id == qr_payload), None)
        
        if existing_item:
            existing_item.quantity += 1
            existing_item.item_total = existing_item.price * existing_item.quantity
        else:
            new_item = CartItem(product_data.product_id, product_data.name, product_data.price)
            cart.append(new_item)
            
        product_data.stock -= 1 # Reduce stock
        total_basket_value = sum(item.item_total for item in cart)
        
        return {
            "success": True,
            "added_item": product_data.name,
            "cart_count": sum(item.quantity for item in cart),
            "basket_total": total_basket_value
        }

# --- 4. TERMINAL EXECUTION (Test karne ke liye) ---
if __name__ == "__main__":
    print("🚀 Zoy Cloud 'Scan & Go' Terminal Started...\n")
    
    db = ZoyDatabase()
    engine = ScanAndGoEngine()
    current_user = "Shashi_User_01" # Tera system ID
    
    while True:
        qr_input = input("📷 Product ka QR Code scan karein (type QR_ZOY_001) ya 'exit' likhein: ")
        
        if qr_input.lower() == 'exit':
            print("Zoy Cloud Terminal Closed. Bye! 🚀")
            break
            
        result = engine.process_scan(user_id=current_user, qr_payload=qr_input, db_connection=db)
        
        if result["success"]:
            print(f"✅ Success! '{result['added_item']}' cart mein add ho gaya.")
            print(f"🛒 Total Items: {result['cart_count']} | Bill Amount: ₹{result['basket_total']}\n")
        else:
            print(f"❌ Error: {result['message']}\n")