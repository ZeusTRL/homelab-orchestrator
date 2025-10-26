from fastapi import APIRouter, Query, Depends, Body, HTTPException
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime

from ..db import SessionLocal
from ..services.scanner import run_nmap_scan
from ..models.device import Device
from ..models.service import Service

router = APIRouter(prefix="/scan", tags=["scan"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def _run_and_persist(targets: list[str], profile: str, skip_ping: bool, db: Session):
    results = await asyncio.to_thread(run_nmap_scan, targets, profile, skip_ping)

    for host, data in results.items():
        d = db.query(Device).filter(Device.mgmt_ip == host).first()
        if not d:
            d = Device(mgmt_ip=host, first_seen=datetime.utcnow())
            db.add(d); db.flush()
        d.hostname = data.get("hostname") or d.hostname
        d.mac = data.get("mac") or d.mac
        d.vendor = data.get("vendor") or d.vendor
        d.os = data.get("os") or d.os
        d.last_seen = datetime.utcnow()

        db.query(Service).filter(Service.device_id == d.id).delete(synchronize_session=False)
        for s in data.get("services", []):
            db.add(Service(
                device_id=d.id,
                port=s["port"],
                proto=s["proto"],
                name=s.get("name"),
                product=s.get("product"),
                version=s.get("version"),
            ))
    db.commit()
    return {"profile": profile, "skip_ping": skip_ping, "hosts": list(results.keys())}

# -------- GET version: query params only (no body) --------
@router.get("/")
async def scan_get(
    targets: list[str] = Query(..., description="CIDRs or IPs; repeat param for multiple"),
    profile: str = Query("fast", enum=["fast", "standard", "deep"]),
    skip_ping: bool = Query(False, description="Add -Pn; use if ICMP is blocked"),
    db: Session = Depends(get_db),
):
    return await _run_and_persist(targets, profile, skip_ping, db)

# -------- POST version: JSON body accepted --------
@router.post("/")
async def scan_post(
    body: dict = Body(..., description='{"targets":["192.168.3.0/24", "..."]}'),
    profile: str = Query("fast", enum=["fast", "standard", "deep"]),
    skip_ping: bool = Query(False, description="Add -Pn; use if ICMP is blocked"),
    db: Session = Depends(get_db),
):
    targets = body.get("targets")
    if not targets or not isinstance(targets, list):
        raise HTTPException(status_code=400, detail='Body must be {"targets":[...]}')
    return await _run_and_persist(targets, profile, skip_ping, db)
