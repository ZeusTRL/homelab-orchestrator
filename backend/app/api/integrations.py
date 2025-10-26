from fastapi import APIRouter, Body
from ..services.pfsense import pull_pfsense_bundle

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.post("/pfsense/pull")
async def pfsense_pull(
    host: str = Body(...),
    username: str = Body(...),
    password: str = Body(""),
    private_key_path: str | None = Body(None)
):
    return pull_pfsense_bundle(host, username, password, private_key_path)
