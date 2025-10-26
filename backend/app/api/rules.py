from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models.device import Device
from ..models.service import Service
from ipaddress import ip_address

router = APIRouter(prefix="/rules", tags=["rules"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _is_private(ip: str) -> bool:
    try:
        return ip_address(ip.split('/')[0]).is_private
    except Exception:
        return True

@router.post("/run")
def run_rules(db: Session = Depends(get_db)):
    violations = []

    # 1) Duplicate management IPs
    by_ip = {}
    for d in db.query(Device).all():
        if not d.mgmt_ip:
            continue
        by_ip.setdefault(d.mgmt_ip, []).append(d.id)
    for ip, ids in by_ip.items():
        if len(ids) > 1:
            violations.append({
                "rule": "duplicate_mgmt_ip",
                "severity": "error",
                "ip": ip,
                "device_ids": ids
            })

    # 2) Risky exposures: SSH open on a device with public mgmt IP
    for d in db.query(Device).all():
        if not d.mgmt_ip or _is_private(d.mgmt_ip):
            continue
        svcs = db.query(Service).filter(Service.device_id == d.id, Service.port == 22).all()
        if svcs:
            violations.append({
                "rule": "ssh_open_public",
                "severity": "warn",
                "device_id": d.id,
                "mgmt_ip": d.mgmt_ip
            })

    return {"violations": violations}
