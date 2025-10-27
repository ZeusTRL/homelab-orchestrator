from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models.device import Device
from ..models.interface import Interface
from ..models.neighbor import Neighbor
from ..ws import notify_topology_update_background
from ..services.snmp import poll_sysinfo, poll_interfaces, poll_lldp_neighbors

router = APIRouter(prefix="/snmp", tags=["snmp"])


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
class SnmpPollRequest(BaseModel):
    host: str = Field(..., description="Device management IP")
    community: str = Field("public", description="SNMP v2c community string")


class SnmpPollResponse(BaseModel):
    ok: bool
    host: str
    sysName: Optional[str] = None
    interfaces_count: int = 0
    neighbors_count: int = 0


# ---------------------------
# Helpers
# ---------------------------
def _infer_vendor_from_descr(descr: str) -> Optional[str]:
    d = (descr or "").lower()
    if "juniper" in d:
        return "Juniper"
    if "cisco" in d:
        return "Cisco"
    if "pfsense" in d:
        return "pfSense"
    if "ubiquiti" in d or "unifi" in d:
        return "Ubiquiti"
    return None


# ---------------------------
# Endpoint
# ---------------------------
@router.post("/poll", response_model=SnmpPollResponse)
async def snmp_poll(
    req: SnmpPollRequest = Body(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks  # injected by FastAPI
):
    host = req.host
    community = req.community

    # Upsert device
    dev = db.query(Device).filter(Device.mgmt_ip == host).first()
    if not dev:
        dev = Device(mgmt_ip=host)
        db.add(dev)
        db.flush()

    # System info
    sysinfo = poll_sysinfo(host, community) or {}
    sys_name = sysinfo.get("sysName")
    sys_descr = sysinfo.get("sysDescr") or ""

    # Basic enrichment
    if sys_name:
        dev.hostname = sys_name
    if sys_descr:
        inferred = _infer_vendor_from_descr(sys_descr)
        if inferred:
            dev.vendor = inferred
        dev.os = (sys_descr[:255]) if sys_descr else dev.os

    dev.last_seen = datetime.now(timezone.utc)

    # Interfaces: wipe & repopulate (simple approach)
    db.query(Interface).filter(Interface.device_id == dev.id).delete(synchronize_session=False)
    if_rows = poll_interfaces(host, community) or []
    for row in if_rows:
        db.add(Interface(
            device_id=dev.id,
            name=row.get("name"),
            admin_up=bool(row.get("admin_up")),
            oper_up=bool(row.get("oper_up")),
            speed=row.get("speed"),
            # desc=row.get("desc"),  # if you added this column
        ))

    # LLDP neighbors: wipe & repopulate (simple approach)
    db.query(Neighbor).filter(Neighbor.local_device_id == dev.id).delete(synchronize_session=False)
    nbrs = poll_lldp_neighbors(host, community) or []
    for n in nbrs:
        db.add(Neighbor(
            local_device_id=dev.id,
            local_if=None,
            remote_sysname=n.get("remote_sysname"),
            remote_port=n.get("remote_port"),
            remote_mgmt_ip=None,
        ))

    db.commit()

    # Notify clients to refresh topology (non-blocking)
    background_tasks.add_task(notify_topology_update_background)

    return SnmpPollResponse(
        ok=True,
        host=host,
        sysName=dev.hostname,
        interfaces_count=len(if_rows),
        neighbors_count=len(nbrs),
    )
