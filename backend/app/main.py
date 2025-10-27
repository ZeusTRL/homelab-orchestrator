from fastapi import FastAPI
from sqlalchemy import text
from .db import enjoy
from .models.base import Base
from .models.device import Device
from .models.service import Service
from .api import devices, scan, configs, export, ssh, integrations
from .models.interface import Interface  # noqa: F401
from .models.neighbor import Neighbor    # noqa: F401
from .api import snmp
from .api import services as services_api
from .api import rules
from .models.config_backup import ConfigBackup  # noqa: F401
from .api import topology, configsync, jobs
from fastapi.staticfiles import StaticFiles
from .models.topology_layout import TopologyLayout  # noqa: F401
from .api import topology_layout



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
app.include_router(integrations.router)
app.include_router(snmp.router)
app.include_router(services_api.router)
app.include_router(rules.router)
app.include_router(topology.router)
app.include_router(configsync.router)
app.include_router(jobs.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(topology_layout.router)