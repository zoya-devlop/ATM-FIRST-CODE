# Orbit Cloud

Orbit Cloud is a real starter cloud infrastructure product for a company that wants to grow toward a larger platform over time. This MVP includes:

- a FastAPI backend
- SQLite persistence
- token-based authentication
- project, compute, Kubernetes, storage, billing, and activity APIs
- a browser dashboard served by the same app
- Docker support for local or small-server deployment

## What it does

This app gives you a lightweight control plane similar in spirit to an early cloud provider dashboard:

- sign in as an operator
- create projects
- provision virtual machines
- create Kubernetes clusters
- create storage buckets
- watch monthly spend
- track operational activity

It is intentionally small, but it is built in a way that can grow into:

- multi-tenant auth and roles
- real background job workers
- provisioning through AWS, GCP, Azure, Proxmox, or Kubernetes
- Terraform integration
- audit logs and alerts
- payment processing

## Project structure

```text
app/
  main.py          FastAPI app and API routes
  db.py            SQLite setup
static/
  app.js           Dashboard logic
  styles.css       UI styling
templates/
  index.html       Main dashboard page
Dockerfile
docker-compose.yml
requirements.txt
```

## Local run

### Option 1: Python

1. Install Python 3.12+.
2. Create a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the sample environment:

```powershell
Copy-Item .env.example .env
```

5. Start the server:

```bash
uvicorn app.main:app --reload
```

6. Open `http://127.0.0.1:8000`

### Option 2: Docker

```bash
docker compose up --build
```

Open `http://127.0.0.1:8000`

## Default login

- Email: `admin@orbitcloud.local`
- Password: `ChangeMe123!`
- API Token: `orbit-local-admin-token`

Change these values in `.env` before any real deployment.

## Example API usage

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@orbitcloud.local\",\"password\":\"ChangeMe123!\"}"
```

Create a project:

```bash
curl -X POST http://127.0.0.1:8000/api/projects \
  -H "Authorization: Bearer orbit-local-admin-token" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Payments Platform\",\"region\":\"ap-south-1\"}"
```

## Real-world next steps

If you want this to become a real company platform, the next strong upgrades are:

1. Replace SQLite with PostgreSQL.
2. Hash passwords with `passlib` or `bcrypt`.
3. Add JWT or session auth plus roles.
4. Move provisioning into background workers with Celery, Dramatiq, or a queue service.
5. Connect instance, cluster, and bucket creation to real cloud APIs.
6. Add Terraform plans and execution pipelines.
7. Add observability with Prometheus, Grafana, and OpenTelemetry.
8. Add CI/CD and automated tests.

## Important note

This MVP is real and runnable, but resource provisioning is simulated right now. That is the right starting point for a serious product because it gives you a working control plane first, then you can connect it to real infrastructure providers safely.
