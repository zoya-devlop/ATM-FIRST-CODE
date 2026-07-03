from fastapi import APIRouter, Depends
from app.db import get_connection
import docker
from app.routers.auth import get_current_user  # Tera Security Guard

router = APIRouter()

# Yeh function database ke data ko dictionary (JSON) mein convert karta hai
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# 🚨 GUARD BITHA DIYA: Ab bina Token koi dashboard nahi dekh payega!
@router.get("/api/dashboard")
def get_real_dashboard_data(user_id: int = Depends(get_current_user)):
    with get_connection() as conn:
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # 1. Asli Projects nikalna
        cursor.execute("SELECT * FROM projects")
        real_projects = cursor.fetchall()
        
        # 2. Asli Instances nikalna
        cursor.execute("SELECT * FROM compute_instances")
        real_instances = cursor.fetchall()

        # 🐳 MAGIC: THE DOCKER LIVE SCANNER
        try:
            client = docker.from_env()
            for inst in real_instances:
                try:
                    # Docker engine se pucho "Bhai ye container chal raha hai kya?"
                    container = client.containers.get(inst["name"])
                    
                    if container.status == "running":
                        inst["status"] = "RUNNING 🟢"
                    elif container.status == "exited":
                        inst["status"] = "STOPPED 🔴"
                    else:
                        inst["status"] = container.status.upper() + " 🟡"
                except:
                    # Agar Docker mein nahi mila (delete ho gaya)
                    inst["status"] = "MISSING ⚠️"
        except Exception as e:
            print("Docker connect nahi hua:", e)
        
        # 3. Asli Activity Feed nikalna
        cursor.execute("SELECT * FROM activity_events ORDER BY created_at DESC LIMIT 5")
        real_events = cursor.fetchall()
        
        # 4. Asli Buckets nikalna
        try:
            cursor.execute("SELECT * FROM storage_buckets")
            real_buckets = cursor.fetchall()
        except:
            real_buckets = []

        # 5. Asli Clusters nikalna
        try:
            cursor.execute("SELECT * FROM kubernetes_clusters")
            real_clusters = cursor.fetchall()
        except:
            real_clusters = []

        # 6. BILLING ENGINE: Asli cost calculate karna
        total_monthly_cost = (len(real_instances) * 10.0) + (len(real_buckets) * 5.0) + (len(real_clusters) * 50.0)
        
        real_invoices = [
            {
                "period": "2026-05", 
                "amount": total_monthly_cost,
                "status": "DUE" if total_monthly_cost > 0 else "PAID"
            }
        ]

        # 7. SABSE AAKHRI MEIN RETURN (Khana pak gaya, ab serve karo)
        return {
            "summary": {
                "projects": len(real_projects),
                "instances": len(real_instances),
                "clusters": len(real_clusters),
                "buckets": len(real_buckets),
                "healthy_projects": len(real_projects),
                "monthly_cost": total_monthly_cost
            },
            "projects": real_projects,
            "instances": real_instances,
            "clusters": real_clusters,
            "buckets": real_buckets,
            "invoices": real_invoices,
            "events": real_events
        }
    
    # 🖥️ THE MATRIX: Live Logs API
@router.get("/api/instances/{instance_name}/logs")
def get_instance_logs(instance_name: str, user_id: int = Depends(get_current_user)):
    import docker
    try:
        client = docker.from_env()
        container = client.containers.get(instance_name)
        # Container ke aakhri 50 line ke logs nikalo
        logs = container.logs(tail=50).decode('utf-8')
        if not logs:
            logs = "Server chal raha hai, par abhi tak koi output nahi aaya!"
        return {"logs": logs}
    except Exception as e:
        return {"logs": f"Error: Server nahi mila ya band hai. Details: {str(e)}"}