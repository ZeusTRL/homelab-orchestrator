from pathlib import Path
from datetime import datetime
import shutil


CONFIG_DIR = Path("/configs")
EXPORT_DIR = Path("/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def export_zip() -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    bundle_dir = EXPORT_DIR / f"bundle-{stamp}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    # Copy configs and (later) inventories, reports
    if CONFIG_DIR.exists():
        dest = bundle_dir / "configs"
        shutil.copytree(CONFIG_DIR, dest, dirs_exist_ok=True)
    zip_path = shutil.make_archive(str(bundle_dir), "zip", root_dir=bundle_dir)
    return zip_path