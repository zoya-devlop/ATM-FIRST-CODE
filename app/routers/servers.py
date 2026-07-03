
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.dashboard import router as dashboard_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Naya dashboard router connect kar diya
app.include_router(dashboard_router)