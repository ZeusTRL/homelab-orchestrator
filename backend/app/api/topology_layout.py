
from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models.device import Device
from ..models.topology_layout import TopologyLayout
from ..schemas.layout import LayoutSetRequest, LayoutGetResponse

router = APIRouter(prefix="/topology/layout", tags=["topology"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=LayoutGetResponse)
def get_layout(db: Session = Depends(get_db)):
    rows = db.query(TopologyLayout).all()
    return {"points": {r.device_id: {"x": float(r.pos_x), "y": float(r.pos_y)} for r in rows}}

@router.post("/", response_model=LayoutGetResponse)
def set_layout(payload: LayoutSetRequest = Body(...), db: Session = Depends(get_db)):
    # Existing devices (set of ints)
    device_ids = [p.device_id for p in payload.points]
    existing_ids = {row[0] for row in db.query(Device.id).filter(Device.id.in_(device_ids)).all()}

    # Upsert only for existing device ids
    by_id = {p.device_id: p for p in payload.points if p.device_id in existing_ids}
    if by_id:
        rows = db.query(TopologyLayout).filter(TopologyLayout.device_id.in_(list(by_id.keys()))).all()
        seen = set()
        for row in rows:
            p = by_id[row.device_id]
            row.pos_x = float(p.x)
            row.pos_y = float(p.y)
            seen.add(row.device_id)
        for did, p in by_id.items():
            if did not in seen:
                db.add(TopologyLayout(device_id=did, pos_x=float(p.x), pos_y=float(p.y)))
        db.commit()

    # Return current map
    all_rows = db.query(TopologyLayout).all()
    return {"points": {r.device_id: {"x": float(r.pos_x), "y": float(r.pos_y)} for r in all_rows}}

@router.delete("/", response_model=LayoutGetResponse)
def clear_layout(device_id: int | None = Query(None), db: Session = Depends(get_db)):
    if device_id is None:
        db.query(TopologyLayout).delete(synchronize_session=False)
    else:
        db.query(TopologyLayout).filter(TopologyLayout.device_id == device_id).delete(synchronize_session=False)
    db.commit()
    rows = db.query(TopologyLayout).all()
    return {"points": {r.device_id: {"x": float(r.pos_x), "y": float(r.pos_y)} for r in rows}}
