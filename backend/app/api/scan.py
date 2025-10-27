from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal

import asyncio
from fastapi import APIRouter, Body, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models.device import Device
from ..ws import notify_topology_update_background
from ..services import scanner

router = APIRouter(prefix="/scan", tags=["scan"])


# ---------------------------
# DB session dependency
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# Schemas
# ---------------------------
ScanProfile = Literal["fast", "standard", "deep"]


class ScanRequest(BaseModel):
    targets: List[str] = Field(..., description="CIDRs or IPs, e.g., ['192.168.3.0/24', '192.168.3.10']")
    profile: ScanProfile = "standard"
    skip_ping: bool = False


class ScanResponse(BaseModel):
    ok: bool
    count: int
    hosts: List[str]


# ---------------------------
# Helpers
# ---------------------------
def _normalize_targets_param(targets_param: str | None) -> List[str]:
    if not targets_param:
        return []
    raw = [t.strip() for t in targets_param.replace(",", " ").split()]
    return [t for t in raw if t]


async def _run_scan_and_persist(
    targets: List[str],
    profile: ScanProfile,
    skip_ping: bool,
    db: Session,
) -> List[str]:
    """
    Run scan (thread off main loop) and upsert 'up' hosts into Devices, updating last_seen.
    services.scanner.scan_targets may return list[str] or list[dict] with an 'ip' key.
    """
    results = await asyncio.to_thread(scanner.scan_targets, targets, profile, skip_ping)
    if not results:
        return []

    ips: List[str] = []
    for item in results:
        if isinstance(item, str):
            ips.append(item)
        elif isinstance(item, dict):
            ip = item.get("ip") or item.get("addr") or item.get("mgmt_ip")
            if ip:
                ips.append(str(ip))

    now = datetime.now(timezone.utc)
    for ip in ips:
        dev = db.query(Device).filter(Device.mgmt_ip == ip).first()
        if not dev:
            dev = Device(mgmt_ip=ip)
            db.add(dev)
            db.flush()
        dev.last_seen = now

    db.commit()
    return ips


# ---------------------------
# Endpoints
# ---------------------------
@router.get("/", response_model=ScanResponse)
async def scan_get(
    targets: str = Query(..., description="Comma or space separated CIDRs or IPs"),
    profile: ScanProfile = Query("standard"),
    skip_ping: bool = Query(False, description="If true, do a no-ping scan"),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks  # injected by FastAPI
):
    target_list = _normalize_targets_param(targets)
    ips = await _run_scan_and_persist(target_list, profile, skip_ping, db)
    if ips:
        background_tasks.add_task(notify_topology_update_background)
    return ScanResponse(ok=True, count=len(ips), hosts=ips)


@router.post("/", response_model=ScanResponse)
async def scan_post(
    req: ScanRequest = Body(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks  # injected by FastAPI
):
    ips = await _run_scan_and_persist(req.targets, req.profile, req.skip_ping, db)
    if ips:
        background_tasks.add_task(notify_topology_update_background)
    return ScanResponse(ok=True, count=len(ips), hosts=ips)
