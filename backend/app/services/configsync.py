from pathlib import Path
from datetime import datetime
import hashlib
import paramiko
from sqlalchemy.orm import Session
from ..models.config_backup import ConfigBackup

BACKUP_DIR = Path("/configs/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256(); h.update(data); return h.hexdigest()

def _ssh_read(host: str, username: str, password: str | None = None, key_path: str | None = None, cmd: str = "show configuration | display set"):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key_path:
        key = paramiko.RSAKey.from_private_key_file(key_path)
        client.connect(host, username=username, pkey=key, look_for_keys=False)
    else:
        client.connect(host, username=username, password=password, look_for_keys=False)
    try:
        _, out, err = client.exec_command(cmd)
        data = out.read()
        if not data:
            raise RuntimeError(err.read().decode(errors="ignore"))
        return data
    finally:
        client.close()

def backup_juniper(db: Session, device_id: int, host: str, username: str, password: str | None, key_path: str | None) -> dict:
    raw = _ssh_read(host, username, password, key_path, "show configuration | display set | no-more")
    sha = _sha256_bytes(raw)
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    outdir = BACKUP_DIR / f"juniper-{host}"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"config-{stamp}.set"
    path.write_bytes(raw)

    rec = ConfigBackup(device_id=device_id, vendor="juniper", path=str(path), sha256=sha)
    db.add(rec); db.commit()
    return {"ok": True, "path": str(path), "sha256": sha}

def last_two_backups(db: Session, device_id: int) -> list[ConfigBackup]:
    return db.query(ConfigBackup).filter(ConfigBackup.device_id == device_id).order_by(ConfigBackup.created_at.desc()).limit(2).all()
