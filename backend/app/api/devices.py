from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models.device import Device
from ..models.interface import Interface
from ..models.service import Service
from ..models.neighbor import Neighbor
from ..schemas.device import DeviceOut

router = APIRouter(prefix="/devices", tags=["devices"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).order_by(Device.id.desc()).all()

@router.get("/{device_id}")
def device_detail(device_id: int, db: Session = Depends(get_db)):
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        raise HTTPException(404, "Device not found")

    ifs = db.query(Interface).filter(Interface.device_id == d.id).all()
    svcs = db.query(Service).filter(Service.device_id == d.id).all()
    nbrs = db.query(Neighbor).filter(Neighbor.local_device_id == d.id).all()

    return {
        "device": {
            "id": d.id, "hostname": d.hostname, "mgmt_ip": d.mgmt_ip, "mac": d.mac,
            "vendor": d.vendor, "model": d.model, "serial": d.serial,
            "os": d.os, "os_version": d.os_version, "notes": d.notes
        },
        "interfaces": [ {"name": i.name, "admin_up": i.admin_up, "oper_up": i.oper_up, "speed": i.speed} for i in ifs ],
        "services":   [ {"port": s.port, "proto": s.proto, "name": s.name, "product": s.product, "version": s.version} for s in svcs ],
        "neighbors":  [ {"local_if": n.local_if, "remote_sysname": n.remote_sysname, "remote_port": n.remote_port, "remote_mgmt_ip": n.remote_mgmt_ip} for n in nbrs ],
    }
