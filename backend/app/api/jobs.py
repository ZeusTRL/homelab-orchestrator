from fastapi import APIRouter, Body
import os
from rq import Queue
from redis import Redis

router = APIRouter(prefix="/jobs", tags=["jobs"])

def _q():
    redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    conn = Redis.from_url(redis_url)
    return Queue("default", connection=conn)

@router.post("/enqueue")
def enqueue_job(
    kind: str = Body(..., description="scan|snmp|pfsense|juniper_backup"),
    payload: dict = Body(default={})
):
    # For now we enqueue a placeholder; you can wire real callables later
    job = _q().enqueue("app.workers.dispatch", {"kind": kind, "payload": payload})
    return {"ok": True, "job_id": job.get_id()}
