import os
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.db import get_connection


APP_NAME = os.getenv("APP_NAME", "Zoya Cloud")
APP_ENV = os.getenv("APP_ENV", "development")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@orbitcloud.local")
DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "Company Admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")
DEFAULT_API_TOKEN = os.getenv("DEFAULT_API_TOKEN", "orbit-local-admin-token")

app = FastAPI(
    title=APP_NAME,
    version="0.1.0",
    description="A small cloud infrastructure MVP with a control plane, API, and dashboard.",
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    return "-".join(value.lower().strip().split())


def bootstrap_demo_data() -> None:
    with get_connection() as connection:
        admin = connection.execute("SELECT id FROM users WHERE email = ?", (DEFAULT_ADMIN_EMAIL,)).fetchone()
        if admin:
            return

        created_at = utc_now()
        connection.execute(
            """
            INSERT INTO users (email, name, password, api_token, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_NAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_API_TOKEN, created_at),
        )

        project_rows = [
            ("Core Platform", "core-platform", "ap-south-1", DEFAULT_ADMIN_EMAIL, 920.50, "healthy"),
            ("AI Research", "ai-research", "us-central1", DEFAULT_ADMIN_EMAIL, 1460.20, "scaling"),
        ]
        connection.executemany(
            """
            INSERT INTO projects (name, slug, region, owner_email, monthly_cost, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [(*row, created_at) for row in project_rows],
        )

        projects = connection.execute("SELECT id, slug FROM projects").fetchall()
        project_ids = {row["slug"]: row["id"] for row in projects}

        connection.executemany(
            """
            INSERT INTO compute_instances
            (project_id, name, region, vcpu, memory_gb, status, public_ip, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (project_ids["core-platform"], "api-gateway-1", "ap-south-1", 4, 16, "running", "34.93.10.18", created_at),
                (project_ids["core-platform"], "jobs-worker-1", "ap-south-1", 8, 32, "running", "34.93.10.19", created_at),
                (project_ids["ai-research"], "gpu-trainer-1", "us-central1", 16, 64, "provisioning", "35.229.20.10", created_at),
            ],
        )

        connection.executemany(
            """
            INSERT INTO kubernetes_clusters
            (project_id, name, region, node_count, kubernetes_version, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (project_ids["core-platform"], "prod-cluster", "ap-south-1", 5, "1.30", "healthy", created_at),
                (project_ids["ai-research"], "ml-serving", "us-central1", 3, "1.29", "upgrading", created_at),
            ],
        )

        connection.executemany(
            """
            INSERT INTO storage_buckets
            (project_id, name, region, size_gb, object_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (project_ids["core-platform"], "orbit-core-backups", "ap-south-1", 180, 45210, created_at),
                (project_ids["ai-research"], "orbit-ml-datasets", "us-central1", 940, 1603, created_at),
            ],
        )

        connection.executemany(
            """
            INSERT INTO invoices (project_id, period, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (project_ids["core-platform"], "2026-03", 920.50, "paid", created_at),
                (project_ids["ai-research"], "2026-03", 1460.20, "due", created_at),
            ],
        )

        connection.executemany(
            """
            INSERT INTO activity_events
            (project_id, actor, action, resource_type, resource_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (project_ids["core-platform"], DEFAULT_ADMIN_EMAIL, "created", "cluster", "prod-cluster", created_at),
                (project_ids["core-platform"], "autoscaler", "scaled", "instance", "jobs-worker-1", created_at),
                (project_ids["ai-research"], DEFAULT_ADMIN_EMAIL, "provisioned", "instance", "gpu-trainer-1", created_at),
            ],
        )

@app.on_event("startup")
def startup():
    pass

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": APP_NAME,
        "default_email": DEFAULT_ADMIN_EMAIL,
        "default_password": DEFAULT_ADMIN_PASSWORD,
        "default_token": DEFAULT_API_TOKEN,
        "app_env": APP_ENV
    })

def require_token(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    token = authorization.replace("Bearer ", "", 1).strip()
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, email, name, api_token FROM users WHERE api_token = ?",
            (token,),
        ).fetchone()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token.")
    return dict(user)


class LoginRequest(BaseModel):
    email: str
    password: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    region: str = Field(min_length=2, max_length=40)


class InstanceCreate(BaseModel):
    project_id: int
    name: str = Field(min_length=2, max_length=80)
    region: str = Field(min_length=2, max_length=40)
    vcpu: int = Field(ge=1, le=128)
    memory_gb: int = Field(ge=1, le=1024)


class ClusterCreate(BaseModel):
    project_id: int
    name: str = Field(min_length=2, max_length=80)
    region: str = Field(min_length=2, max_length=40)
    node_count: int = Field(ge=1, le=500)
    kubernetes_version: str = Field(min_length=3, max_length=20)


class BucketCreate(BaseModel):
    project_id: int
    name: str = Field(min_length=3, max_length=80)
    region: str = Field(min_length=2, max_length=40)


def add_activity(connection, project_id: int | None, actor: str, action: str, resource_type: str, resource_name: str) -> None:
    connection.execute(
        """
        INSERT INTO activity_events (project_id, actor, action, resource_type, resource_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (project_id, actor, action, resource_type, resource_name, utc_now()),
    )


def project_exists(connection, project_id: int) -> bool:
    return connection.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone() is not None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": APP_NAME,
            "default_email": DEFAULT_ADMIN_EMAIL,
            "default_password": DEFAULT_ADMIN_PASSWORD,
            "default_token": DEFAULT_API_TOKEN,
            "app_env": APP_ENV,
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "environment": APP_ENV, "timestamp": utc_now()}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, email, name, password, api_token FROM users WHERE email = ?",
            (payload.email,),
        ).fetchone()
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    return {
        "token": user["api_token"],
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
    }


@app.get("/api/me")
def me(current_user: dict[str, Any] = Depends(require_token)):
    return {"user": current_user}


@app.get("/api/dashboard")
def dashboard(current_user: dict[str, Any] = Depends(require_token)):
    with get_connection() as connection:
        projects = [dict(row) for row in connection.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()]
        instances = [dict(row) for row in connection.execute("SELECT * FROM compute_instances ORDER BY id DESC").fetchall()]
        clusters = [dict(row) for row in connection.execute("SELECT * FROM kubernetes_clusters ORDER BY id DESC").fetchall()]
        buckets = [dict(row) for row in connection.execute("SELECT * FROM storage_buckets ORDER BY id DESC").fetchall()]
        invoices = [dict(row) for row in connection.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()]
        events = [dict(row) for row in connection.execute("SELECT * FROM activity_events ORDER BY id DESC LIMIT 12").fetchall()]

    total_monthly_cost = round(sum(project["monthly_cost"] for project in projects), 2)
    healthy_projects = sum(1 for project in projects if project["status"] == "healthy")

    return {
        "user": current_user,
        "summary": {
            "projects": len(projects),
            "instances": len(instances),
            "clusters": len(clusters),
            "buckets": len(buckets),
            "monthly_cost": total_monthly_cost,
            "healthy_projects": healthy_projects,
        },
        "projects": projects,
        "instances": instances,
        "clusters": clusters,
        "buckets": buckets,
        "invoices": invoices,
        "events": events,
    }


@app.post("/api/projects", status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, current_user: dict[str, Any] = Depends(require_token)):
    created_at = utc_now()
    slug_base = slugify(payload.name)
    slug = f"{slug_base}-{secrets.token_hex(2)}"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO projects (name, slug, region, owner_email, monthly_cost, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (payload.name, slug, payload.region, current_user["email"], 0.0, "healthy", created_at),
        )
        project = connection.execute("SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
        add_activity(connection, project["id"], current_user["email"], "created", "project", payload.name)

    return {"project": dict(project)}


@app.post("/api/instances", status_code=status.HTTP_201_CREATED)
def create_instance(payload: InstanceCreate, current_user: dict[str, Any] = Depends(require_token)):
    with get_connection() as connection:
        if not project_exists(connection, payload.project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        connection.execute(
            """
            INSERT INTO compute_instances
            (project_id, name, region, vcpu, memory_gb, status, public_ip, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.project_id,
                payload.name,
                payload.region,
                payload.vcpu,
                payload.memory_gb,
                "running",
                f"10.0.{payload.project_id}.{secrets.randbelow(240) + 10}",
                utc_now(),
            ),
        )
        instance = connection.execute("SELECT * FROM compute_instances ORDER BY id DESC LIMIT 1").fetchone()
        connection.execute(
            "UPDATE projects SET monthly_cost = monthly_cost + ? WHERE id = ?",
            ((payload.vcpu * 12.5) + (payload.memory_gb * 1.8), payload.project_id),
        )
        add_activity(connection, payload.project_id, current_user["email"], "created", "instance", payload.name)

    return {"instance": dict(instance)}


@app.post("/api/clusters", status_code=status.HTTP_201_CREATED)
def create_cluster(payload: ClusterCreate, current_user: dict[str, Any] = Depends(require_token)):
    with get_connection() as connection:
        if not project_exists(connection, payload.project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        connection.execute(
            """
            INSERT INTO kubernetes_clusters
            (project_id, name, region, node_count, kubernetes_version, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.project_id,
                payload.name,
                payload.region,
                payload.node_count,
                payload.kubernetes_version,
                "healthy",
                utc_now(),
            ),
        )
        cluster = connection.execute("SELECT * FROM kubernetes_clusters ORDER BY id DESC LIMIT 1").fetchone()
        connection.execute(
            "UPDATE projects SET monthly_cost = monthly_cost + ? WHERE id = ?",
            (payload.node_count * 45.0, payload.project_id),
        )
        add_activity(connection, payload.project_id, current_user["email"], "created", "cluster", payload.name)

    return {"cluster": dict(cluster)}


@app.post("/api/buckets", status_code=status.HTTP_201_CREATED)
def create_bucket(payload: BucketCreate, current_user: dict[str, Any] = Depends(require_token)):
    with get_connection() as connection:
        if not project_exists(connection, payload.project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        connection.execute(
            """
            INSERT INTO storage_buckets
            (project_id, name, region, size_gb, object_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (payload.project_id, payload.name, payload.region, 0, 0, utc_now()),
        )
        bucket = connection.execute("SELECT * FROM storage_buckets ORDER BY id DESC LIMIT 1").fetchone()
        add_activity(connection, payload.project_id, current_user["email"], "created", "bucket", payload.name)

    return {"bucket": dict(bucket)}
