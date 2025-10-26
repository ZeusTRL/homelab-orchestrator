from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import difflib

from ..db import SessionLocal
from ..models.device import Device
from ..models.config_backup import ConfigBackup
from ..services.configsync import backup_juniper, last_two_backups

router = APIRouter(prefix="/configs/backup", tags=["config-backup"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/pull/juniper")
def pull_juniper(
    device_id: int = Body(...),
    host: str = Body(...),
    username: str = Body(...),
    password: str | None = Body(None),
    private_key_path: str | None = Body(None),
    db: Session = Depends(get_db),
):
    if not db.query(Device).filter(Device.id == device_id).first():
        raise HTTPException(404, "Device not found")
    return backup_juniper(db, device_id, host, username, password, private_key_path)

@router.get("/diff")
def backup_diff(device_id: int, db: Session = Depends(get_db)):
    backups = last_two_backups(db, device_id)
    if len(backups) < 2:
        return {"ok": False, "detail": "Need at least two backups to diff."}
    a, b = backups[1], backups[0]  # older, newer
    old = Path(a.path).read_text(errors="ignore").splitlines(keepends=True)
    new = Path(b.path).read_text(errors="ignore").splitlines(keepends=True)
    diff = difflib.unified_diff(old, new, fromfile=a.path, tofile=b.path)
    return {"ok": True, "from": a.path, "to": b.path, "diff": "".join(diff)}
