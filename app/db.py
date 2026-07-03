import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "data/orbitcloud.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Servers table (user-specific)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'stopped' CHECK(status IN ('running', 'stopped', 'creating')),
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Dict-like rows
        try:
            yield conn
        finally:
            conn.close()
    
    # User methods
    def create_user(self, email: str, hashed_password: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
                (email, hashed_password)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            return cursor.fetchone()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return cursor.fetchone()
    
    # Server methods
    def create_server(self, name: str, user_id: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO servers (name, status, user_id) VALUES (?, 'creating', ?)",
                    (name, user_id)
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                raise Exception("Server name already exists")
    
    def get_servers(self, user_id: int) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM servers WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_server(self, server_id: int, user_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM servers WHERE id = ? AND user_id = ?",
                (server_id, user_id)
            )
            return cursor.fetchone()
    
    def update_server_status(self, server_id: int, user_id: int, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE servers SET status = ? WHERE id = ? AND user_id = ?",
                (status, server_id, user_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise Exception("Server not found")
    
    def delete_server(self, server_id: int, user_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM servers WHERE id = ? AND user_id = ?",
                (server_id, user_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise Exception("Server not found")

# Global database instance
db = Database()




# ========== TEST CODE - REMOVE AFTER TESTING ==========
if __name__ == "__main__":
    print("🧪 Testing Database...")
    
    # Test user
    user_id = db.create_user("test@example.com", "hashedpass123")
    print(f"✅ Created user ID: {user_id}")
    
    # Test server
    server_id = db.create_server("my-app", user_id)
    print(f"✅ Created server ID: {server_id}")
    
    # List servers
    servers = db.get_servers(user_id)
    print("✅ Servers:", servers)
    
    # Start server
    db.update_server_status(server_id, user_id, "running")
    print("✅ Server started!")
    
    print("🎉 Database working perfectly!")
    print("💡 Remove this test code after verifying!")
# =====================================================