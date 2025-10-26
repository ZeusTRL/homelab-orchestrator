# SNMP poller using puresnmp (Python 3.12 friendly)
# We use numeric OIDs to avoid MIB dependency.

from typing import Optional, List, Dict
from puresnmp.api import v2c as snmp
from puresnmp import oid as _oid

# OIDs
SYS_DESCR = "1.3.6.1.2.1.1.1.0"   # sysDescr.0
SYS_NAME  = "1.3.6.1.2.1.1.5.0"   # sysName.0

IF_DESCR  = "1.3.6.1.2.1.2.2.1.2" # ifDescr
IF_ADMIN  = "1.3.6.1.2.1.2.2.1.7" # ifAdminStatus (1=up, 2=down)
IF_OPER   = "1.3.6.1.2.1.2.2.1.8" # ifOperStatus  (1=up, 2=down)
IF_SPEED  = "1.3.6.1.2.1.2.2.1.5" # ifSpeed (bps)

# LLDP (802.1AB)
LLDP_REM_SYSNAME = "1.0.8802.1.1.2.1.4.1.1.9"  # lldpRemSysName
LLDP_REM_PORTID  = "1.0.8802.1.1.2.1.4.1.1.7"  # lldpRemPortId


def _safe_str(val) -> Optional[str]:
    if val is None:
        return None
    try:
        if isinstance(val, bytes):
            return val.decode(errors="ignore")
        return str(val)
    except Exception:
        return None


def poll_sysinfo(host: str, community: str) -> dict:
    try:
        descr = snmp.get(host, community, _oid.OID(SYS_DESCR))
        name  = snmp.get(host, community, _oid.OID(SYS_NAME))
        return {"sysDescr": _safe_str(descr), "sysName": _safe_str(name)}
    except Exception:
        return {}


def _walk_map(host: str, community: str, base_oid: str) -> Dict[str, str]:
    """Walk an OID and return {index: value} where index is the last sub-id."""
    out: Dict[str, str] = {}
    for oid, value in snmp.walk(host, community, _oid.OID(base_oid)):
        # oid like 1.3.6.1....<index>
        idx = str(oid).split(".")[-1]
        out[idx] = _safe_str(value)
    return out


def poll_interfaces(host: str, community: str) -> List[dict]:
    try:
        d = _walk_map(host, community, IF_DESCR)
        a = _walk_map(host, community, IF_ADMIN)
        o = _walk_map(host, community, IF_OPER)
        s = _walk_map(host, community, IF_SPEED)
    except Exception:
        return []

    out = []
    for idx, name in d.items():
        out.append({
            "index": idx,
            "name": name,
            "admin_up": a.get(idx) == "1",
            "oper_up":  o.get(idx) == "1",
            "speed":    s.get(idx),
        })
    return out


def _walk_lldp(host: str, community: str, base_oid: str) -> Dict[str, str]:
    """
    LLDP indexes are typically: localPort.remIndex.remSubIndex (3 trailing numbers).
    We key by the last 3 numbers joined with dots.
    """
    out: Dict[str, str] = {}
    for oid, value in snmp.walk(host, community, _oid.OID(base_oid)):
        inst = ".".join(str(oid).split(".")[-3:])
        out[inst] = _safe_str(value)
    return out


def poll_lldp_neighbors(host: str, community: str) -> List[dict]:
    try:
        sysnames = _walk_lldp(host, community, LLDP_REM_SYSNAME)
        ports    = _walk_lldp(host, community, LLDP_REM_PORTID)
    except Exception:
        return []

    out = []
    for inst, rname in sysnames.items():
        out.append({
            "instance": inst,
            "remote_sysname": rname,
            "remote_port": ports.get(inst),
        })
    return out
