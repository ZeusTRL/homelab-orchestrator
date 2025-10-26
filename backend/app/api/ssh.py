from fastapi import APIRouter, Body
from ..services.sshpush import push_juniper_set_config


router = APIRouter(prefix="/ssh", tags=["ssh"])


@router.post("/push")
async def push_config(
    host: str = Body(...),
    username: str = Body(...),
    password: str = Body(""),
    private_key_path: str | None = Body(None),
    config_text: str = Body(..., description="Juniper set-style commands or 'configure' mode script"),
    dry_run: bool = Body(True)
):
    result = push_juniper_set_config(host, username, password, private_key_path, config_text, dry_run)
    return result