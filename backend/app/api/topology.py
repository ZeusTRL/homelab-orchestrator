from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..services.topology import build_topology

router = APIRouter(prefix="/topology", tags=["topology"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_topology(db: Session = Depends(get_db)):
    return build_topology(db)
