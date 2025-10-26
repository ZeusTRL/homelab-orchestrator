from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models.device import Device
from ..schemas.device import DeviceOut, DeviceCreate, DeviceUpdate

router = APIRouter(prefix="/devices", tags=["devices"])


# --- Dependency for DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- List all devices (with optional active_only filter) ---
@router.get("/", response_model=list[DeviceOut])
def list_devices(
    active_only: bool = Query(
        False, description="If true, only show devices seen by scans or SNMP."
    ),
    db: Session = Depends(get_db),
):
    q = db.query(Device).order_by(Device.id.desc())
    if active_only:
        q = q.filter(Device.last_seen.isnot(None))
    return q.all()


# --- Get a single device by ID ---
@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


# --- Create a device manually (optional feature) ---
@router.post("/", response_model=DeviceOut)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    db_device = Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


# --- Update a device record ---
@router.put("/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, payload: DeviceUpdate, db: Session = Depends(get_db)):
    db_device = db.query(Device).filter(Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(db_device, key, value)

    db.commit()
    db.refresh(db_device)
    return db_device


# --- Delete a device ---
@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return {"ok": True, "deleted_id": device_id}
