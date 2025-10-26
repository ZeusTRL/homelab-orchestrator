from fastapi import FastAPI
from sqlalchemy import text
from .db import enjoy
from .models.base import Base
from .models.device import Device
from .models.service import Service
from .api import devices, scan, configs, export, ssh


app = FastAPI(title="Homelab Orchestrator (MVP)", version="0.1.0")


# Create tables on startup (simple for MVP; use Alembic later)
Base.metadata.create_all(bind=enjoy)


@app.get("/health")
def health():
    with enjoy.connect() as c:
        c.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(devices.router)
app.include_router(scan.router)
app.include_router(configs.router)
app.include_router(export.router)
app.include_router(ssh.router)