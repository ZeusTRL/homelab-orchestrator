from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..services.scanner import run_nmap_scan
from ..models.device import Device


router = APIRouter(prefix="/scan", tags=["scan"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
async def scan(targets: list[str] = Query(..., description="CIDRs or IPs"), db: Session = Depends(get_db)):
    results = run_nmap_scan(targets)
    # upsert devices + services (minimal for MVP)
    for host, data in results.items():
        d = db.query(Device).filter(Device.mgmt_ip == host).first()
        if not d:
            d = Device(mgmt_ip=host)
            db.add(d)
        d.hostname = data.get("hostname")
        vend = data.get("vendor") or {}
        d.vendor = next(iter(vend.values())) if isinstance(vend, dict) and vend else d.vendor
        d.os = (data.get("osmatch") or [{}])[0].get("name") if data.get("osmatch") else d.os
    db.commit()
    return {"hosts": list(results.keys())}