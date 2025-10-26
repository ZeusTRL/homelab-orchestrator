from typing import Dict, Any, List
import networkx as nx
from sqlalchemy.orm import Session
from ..models.device import Device
from ..models.neighbor import Neighbor

def build_topology(db: Session) -> Dict[str, Any]:
    G = nx.Graph()

    # Nodes: devices we know
    devices = {d.id: d for d in db.query(Device).all()}
    for d in devices.values():
        G.add_node(d.id, label=d.hostname or d.mgmt_ip, vendor=d.vendor, ip=d.mgmt_ip)

    # Edges: LLDP neighbors we’ve captured
    for n in db.query(Neighbor).all():
        # Try to match remote by sysname or mgmt_ip if present
        remote_id = None
        for d in devices.values():
            if n.remote_mgmt_ip and d.mgmt_ip == n.remote_mgmt_ip:
                remote_id = d.id; break
            if n.remote_sysname and (d.hostname or "").lower() == (n.remote_sysname or "").lower():
                remote_id = d.id; break
        if remote_id:
            u, v = n.local_device_id, remote_id
            if u and v and u != v:
                G.add_edge(u, v, local_if=n.local_if, remote_port=n.remote_port)

    # Return a simple JSON structure
    nodes = [{"id": nid, **G.nodes[nid]} for nid in G.nodes]
    edges = [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges]
    return {"nodes": nodes, "edges": edges}
