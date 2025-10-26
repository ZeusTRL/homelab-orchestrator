from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models.device import Device
from ..models.interface import Interface
from ..models.neighbor import Neighbor
from ..services.snmp import poll_sysinfo, poll_interfaces, poll_lldp_neighbors

router = APIRouter(prefix="/snmp", tags=["snmp"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/poll")
async def snmp_poll(
    host: str = Body(...),
    community: str = Body("public"),
    db: Session = Depends(get_db),
):
    d = db.query(Device).filter(Device.mgmt_ip == host).first()
    if not d:
        d = Device(mgmt_ip=host)
        db.add(d)
        db.flush()

    sysinfo = poll_sysinfo(host, community) or {}
    d.hostname   = sysinfo.get("sysName") or d.hostname
    sysdescr     = sysinfo.get("sysDescr") or ""
    # quick Juniper parsing
    if "Juniper" in sysdescr:
        d.vendor = "Juniper"
    d.os = d.os or sysdescr[:255]
    # You could parse model/serial from ENTITY-MIB later

    # Interfaces
    db.query(Interface).filter(Interface.device_id == d.id).delete(synchronize_session=False)
    for row in poll_interfaces(host, community):
        db.add(Interface(
            device_id=d.id,
            name=row["name"],
            admin_up=row["admin_up"],
            oper_up=row["oper_up"],
            speed=row["speed"],
        ))

    # LLDP Neighbors
    db.query(Neighbor).filter(Neighbor.local_device_id == d.id).delete(synchronize_session=False)
    for n in poll_lldp_neighbors(host, community):
        db.add(Neighbor(
            local_device_id=d.id,
            local_if=None,                # can be filled with LLDP localPort walk later
            remote_sysname=n["remote_sysname"],
            remote_port=n.get("remote_port"),
            remote_mgmt_ip=None,
        ))

    db.commit()
    return {"ok": True, "host": host}
