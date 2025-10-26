from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models.device import Device
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