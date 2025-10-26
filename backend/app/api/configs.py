from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..schemas.device import GenJuniperConfigIn
from ..services.configgen import render_juniper_config


router = APIRouter(prefix="/configs", tags=["configs"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate")
async def generate_juniper_config(payload: GenJuniperConfigIn = Body(...)):
    text, path = render_juniper_config(payload)
    return {"path": path, "preview": text}