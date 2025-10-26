from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models.service import Service

router = APIRouter(prefix="/services", tags=["services"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def list_services(db: Session = Depends(get_db), proto: str | None = None, port: int | None = None):
    q = db.query(Service)
    if proto:
        q = q.filter(Service.proto == proto)
    if port:
        q = q.filter(Service.port == port)
    return [ {
        "id": s.id, "device_id": s.device_id, "port": s.port, "proto": s.proto,
        "name": s.name, "product": s.product, "version": s.version
    } for s in q.all() ]
