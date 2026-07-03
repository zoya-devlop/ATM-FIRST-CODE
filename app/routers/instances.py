from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db import get_connection
from app.routers.auth import get_current_user  # 🔒 Tera Security Guard
from datetime import datetime
import docker

router = APIRouter()

# 🐳 Docker Engine Setup
try:
    client = docker.from_env()
except Exception as e:
    print("Docker engine connect nahi ho paaya. Kya Docker Desktop chalu hai?")
    client = None

class InstanceCreate(BaseModel):
    project_id: int
    name: str
    region: str
    vcpu: int
    memory_gb: int

# 🚀 1. SECURE CREATE ENGINE (Server banana aur Website install karna)
@router.post("/api/instances")
def create_real_instance(
    instance: InstanceCreate,
    user_id: int = Depends(get_current_user)
):
    try:
        # 1. Asli Nginx Container Create Karna (Bina kisi extra prefix ke)
        container = client.containers.run(
            "nginx:latest", 
            name=instance.name,
            detach=True,
            ports={'80/tcp': None} 
        )
        
        # 2. Port nikalna
        container.reload()
        ports = container.attrs['NetworkSettings']['Ports']
        assigned_port = ports['80/tcp'][0]['HostPort'] if ports and '80/tcp' in ports else "Pending"
        public_ip = f"127.0.0.1:{assigned_port}"

        # 🌟 3. JADOO: Nginx ke andar Zoy Cloud ki Live Website Inject karna!
        # 🌟 3. JADOO: Nginx ke andar Zoy Cloud ki Live Website Inject karna (UTF-8 ke saath)
        custom_html = f"<meta charset='UTF-8'><h1>🚀 Welcome to Zoy Cloud!</h1><h2>Tera server '{instance.name}' ekdum mast chal raha hai The Boss!</h2>"
        container.exec_run(f"sh -c 'echo \"{custom_html}\" > /usr/share/nginx/html/index.html'")

        # 4. Database mein record save karna
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO compute_instances (project_id, name, region, vcpu, memory_gb, status, public_ip, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (instance.project_id, instance.name, instance.region, instance.vcpu, instance.memory_gb, "RUNNING", public_ip, datetime.now().isoformat())
            )
            
            cursor.execute(
                """
                INSERT INTO activity_events (project_id, actor, action, resource_type, resource_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (instance.project_id, f"User_{user_id}", "provisioned real", "instance", instance.name, datetime.now().isoformat())
            )
            
        return {"message": "Real Instance created securely!", "ip": public_ip}

    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# 💥 2. SECURE DESTROY ENGINE
@router.delete("/api/instances/{instance_name}")
def delete_real_instance(
    instance_name: str,
    user_id: int = Depends(get_current_user)
):
    try:
        # Asli Docker Container ko dhoondh kar roko aur UDA do!
        try:
            container = client.containers.get(instance_name)
            container.stop()    
            container.remove()  
            print(f"🗑️ Docker se '{instance_name}' poori tarah delete ho gaya!")
        except Exception as docker_err:
            print(f"⚠️ Container Docker mein nahi mila. Error: {docker_err}")

        # Database se nishani mita do
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM compute_instances WHERE name = ?", (instance_name,))
            cursor.execute(
                """
                INSERT INTO activity_events (project_id, actor, action, resource_type, resource_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (1, f"User_{user_id}", "deleted server", "instance", instance_name, datetime.now().isoformat())
            )
            
        return {"message": f"Server '{instance_name}' securely destroy ho gaya! Bill kam ho gaya! 📉"}

    except Exception as e:
        print("🚨 DESTROY ERROR:", str(e))
        raise HTTPException(status_code=400, detail=str(e))