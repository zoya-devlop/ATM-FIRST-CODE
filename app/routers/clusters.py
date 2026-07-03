from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_connection
from datetime import datetime
import docker

router = APIRouter()

try:
    client = docker.from_env()
except:
    pass

class ClusterCreate(BaseModel):
    project_id: int
    name: str
    region: str
    node_count: int
    kubernetes_version: str

@router.post("/api/clusters")
def create_real_cluster(cluster: ClusterCreate):
    try:
        # 1. Asli Docker Containers (Nodes) banana!
        for i in range(cluster.node_count):
            node_name = f"zoy-{cluster.name}-node-{i+1}"
            try:
                client.containers.run("nginx:alpine", name=node_name, detach=True)
            except Exception as docker_err:
                print(f"⚠️ Dhyan de: Container '{node_name}' pehle se chalu hai!")

        # 2. Database mein Cluster ka record save karna
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # 💥 JADU: Purani kharab table ko delete karo! 💥
            cursor.execute("DROP TABLE IF EXISTS kubernetes_clusters")
            
            # 🏗️ Nayi fresh table banao (Jisme 'version' column ho)
            cursor.execute("""
            CREATE TABLE kubernetes_clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                name TEXT,
                region TEXT,
                node_count INTEGER,
                version TEXT,
                status TEXT,
                created_at TEXT
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                actor TEXT,
                action TEXT,
                resource_type TEXT,
                resource_name TEXT,
                created_at TEXT
            )
            """)

            # Naya record save karo
            cursor.execute(
                """
                INSERT INTO kubernetes_clusters (project_id, name, region, node_count, version, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cluster.project_id, cluster.name, cluster.region, cluster.node_count, cluster.kubernetes_version, "HEALTHY", datetime.now().isoformat())
            )
            
            # Activity Track karna
            cursor.execute(
                """
                INSERT INTO activity_events (project_id, actor, action, resource_type, resource_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cluster.project_id, "admin@orbitcloud.local", "created k8s", "cluster", cluster.name, datetime.now().isoformat())
            )
            
        return {"message": f"Real Cluster '{cluster.name}' successfully created!"}

    except Exception as e:
        print("🚨 DATABASE ERROR:", str(e))
        raise HTTPException(status_code=400, detail=str(e))