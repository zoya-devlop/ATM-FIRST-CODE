print("FILE RUNNING")
import os
import subprocess
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

# ---------------- CONFIG ----------------
APP_NAME = os.getenv("APP_NAME", "Zoya Cloud")
APP_ENV = os.getenv("APP_ENV", "development")

DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@zoya.com")
DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "Admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "123456")
DEFAULT_API_TOKEN = os.getenv("DEFAULT_API_TOKEN", "zoya-token")


# ---------------- APP ----------------
app = FastAPI(
    title=APP_NAME,
    version="1.0.0"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "zoya_secret"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

users = []

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("sub")
 
# ---------------- UTILS ----------------
def utc_now():
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str):
    return "-".join(value.lower().strip().split())


# ---------------- DOCKER ----------------
def create_container():
    try:
        result = subprocess.run(
            ["docker", "run", "-d", "-p", "8090:80", "nginx"],
            capture_output=True,
            text=True
        )
        return result.stdout
    except Exception as e:
        return str(e)


# ---------------- AUTH ----------------
def require_token(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.replace("Bearer ", "").strip()

    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, email, name, api_token FROM users WHERE api_token = ?",
            (token,),
        ).fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return dict(user)


# ---------------- ROUTES ----------------
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


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "environment": APP_ENV,
        "time": utc_now()
    }


from datetime import datetime

@app.post("/create-server")
def create_server(name: str, token: str = Depends(oauth2_scheme)):
    user = get_current_user(token)

    server = {
        "id": len(servers) + 1,
        "name": name,
        "user": user,
        "status": "running",
        "created_at": str(datetime.utcnow()),
        "url": f"http://127.0.0.1:8000/{name}"
    }

    servers.append(server)

    return {"message": "Server created", "server": server}


# ---------------- LOGIN ----------------
class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, email, name, password, api_token FROM users WHERE email = ?",
            (payload.email,),
        ).fetchone()

    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "token": user["api_token"],
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }


# ---------------- USER ----------------
@app.get("/api/me")
def me(current_user: dict = Depends(require_token)):
    return {"user": current_user}


# ---------------- PROJECT CREATE ----------------
class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    region: str = Field(min_length=2, max_length=40)


@app.post("/api/projects")
def create_project(payload: ProjectCreate, current_user: dict = Depends(require_token)):
    created_at = utc_now()
    slug = f"{slugify(payload.name)}-{secrets.token_hex(2)}"

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO projects (name, slug, region, owner_email, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.name, slug, payload.region, current_user["email"], created_at),
        )

    return {"status": "project created", "slug": slug}

@app.get("/servers")
def list_servers():
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.ID}} {{.Image}} {{.Status}}"],
            capture_output=True,
            text=True
        )
        servers = result.stdout.strip().split("\n")
        return {"servers": servers}
    except Exception as e:
        return {"error": str(e)}
    
    
@app.delete("/delete-server/{container_id}")
def delete_server(container_id: str):
    import docker

    client = docker.from_env()

    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
        return {"status": "deleted"}
    except Exception as e:
        return {"error": str(e)}
    
    @app.post("/register")
    def register(email: str, password: str):
        hashed = hash_password(password)
        users.append({"email": email, "password": hashed})
        return {"message": "User registered"}
   
from fastapi import Form

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    for user in users:
        if user["email"] == username and verify_password(password, user["password"]):
            token = create_token({"sub": username})
            return {"access_token": token}
    return {"error": "Invalid credentials"}

@app.get("/protected")
def protected(token: str = Depends(oauth2_scheme)):
    return {"message": "You are logged in"}

@app.post("/register")
def register(email: str, password: str):
    hashed = hash_password(password)
    users.append({"email": email, "password": hashed})
    return {"message": "User registered"}


@app.get("/")
def home():
    return {"msg": "Zoya Cloud running"}

@app.get("/servers")
def get_servers():
    return users

servers = []

@app.post("/create-server")
def create_server(name: str):
    servers.append({"name": name})
    return {"message": "Server created"}

@app.get("/servers")
def get_servers():
    return servers