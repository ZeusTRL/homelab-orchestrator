from pathlib import Path
from datetime import datetime
import paramiko

EXPORT_DIR = Path("/configs/pfsense")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

CMD_PACK = {
    "pf_rules.txt": "pfctl -sr",
    "pf_nat.txt":   "pfctl -sn",
    "pf_stats.txt": "pfctl -sa",
    "sockets.txt":  "sockstat -4 -6 -l",
    "routes.txt":   "netstat -rn"
}

def _connect(host, username, password, private_key_path=None):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if private_key_path:
        key = paramiko.RSAKey.from_private_key_file(private_key_path)
        client.connect(host, username=username, pkey=key, look_for_keys=False)
    else:
        client.connect(host, username=username, password=password, look_for_keys=False)
    return client

def _exec(ssh, cmd):
    _, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read()
    err = stderr.read()
    return out.decode(errors="ignore"), err.decode(errors="ignore")

def pull_pfsense_bundle(host: str, username: str, password: str, private_key_path: str | None):
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    host_dir = EXPORT_DIR / f"{host}-{stamp}"
    host_dir.mkdir(parents=True, exist_ok=True)

    ssh = _connect(host, username, password, private_key_path)
    try:
        # 1) config.xml
        # (CE/Plus both use /conf/config.xml on current releases)
        cfg_out, cfg_err = _exec(ssh, "cat /conf/config.xml")
        if not cfg_out.strip():
            raise RuntimeError(f"Could not read /conf/config.xml: {cfg_err}")
        (host_dir / "config.xml").write_text(cfg_out)

        # 2) diagnostics
        for filename, cmd in CMD_PACK.items():
            out, _ = _exec(ssh, cmd)
            (host_dir / filename).write_text(out)

        # small summary
        summary = {
            "host": host,
            "bundle_dir": str(host_dir),
            "files": ["config.xml"] + list(CMD_PACK.keys())
        }
        return {"ok": True, **summary}
    finally:
        ssh.close()
