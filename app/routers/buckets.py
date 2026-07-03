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

# Frontend se aane wale data ka format
class BucketCreate(BaseModel):
    project_id: int
    name: str
    region: str

@router.post("/api/buckets")
def create_real_bucket(bucket: BucketCreate):
    try:
        # 1. Asli Docker Volume banana (Real Storage Space)
        volume_name = f"zoy-bucket-{bucket.name}"
        client.volumes.create(name=volume_name)

        # 2. Database mein record save karna
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Default 100GB ka dummy size dikhayenge (storage_buckets table mein)
            cursor.execute(
                """
                INSERT INTO storage_buckets (project_id, name, region, size_gb, object_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (bucket.project_id, bucket.name, bucket.region, 100, 0, datetime.now().isoformat())
            )
            
            # Activity Event save karna
            cursor.execute(
                """
                INSERT INTO activity_events (project_id, actor, action, resource_type, resource_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (bucket.project_id, "admin@orbitcloud.local", "created storage", "bucket", bucket.name, datetime.now().isoformat())
            )
            
        return {"message": "Real Bucket created successfully!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))