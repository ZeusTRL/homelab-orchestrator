# Minimal RQ worker target – you can expand each case to call your services
from typing import Dict, Any
from time import sleep

def dispatch(task: Dict[str, Any]):
    kind = task.get("kind")
    payload = task.get("payload", {})
    # TODO: call into scanner/snmp/configsync as needed
    sleep(1)
    return {"done": True, "kind": kind, "payload": payload}
