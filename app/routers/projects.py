from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_connection
from datetime import datetime

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    region: str

@router.post("/api/projects")
def create_project(project: ProjectCreate):
    with get_connection() as conn:
        cursor = conn.cursor()
        slug = project.name.lower().replace(" ", "-")
        
        try:
            cursor.execute(
                """
                INSERT INTO projects (name, slug, region, owner_email, monthly_cost, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (project.name, slug, project.region, "admin@orbitcloud.local", 0.0, "healthy", datetime.now().isoformat())
            )
            return {"message": "Project created successfully", "id": cursor.lastrowid}
        except Exception as e:
            raise HTTPException(status_code=400, detail="Error: Project create nahi hua.")