from fastapi import APIRouter
from ..services.exporter import export_zip


router = APIRouter(prefix="/export", tags=["export"])


@router.post("/zip")
async def export_all():
    path = export_zip()
    return {"zip_path": path}