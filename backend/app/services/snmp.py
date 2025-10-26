# backend/app/services/snmp.py
# SNMP poller using puresnmp (Python 3.12 friendly, no external MIBs required).
# Returns simple dicts/lists so callers can persist into the DB easily.

from __future__ import annotations
from typing import Optional, List, Dict, Tuple
from puresnmp import api as snmp


# -------------------------------
# Common OIDs (string form)
# -------------------------------

# SNMPv2-MIB system info
SYS_DESCR = "1.3.6.1.2.1.1.1.0"   # sysDescr.0
SYS_NAME  = "1.3.6.1.2.1.1.5.0"   # sysName.0

# IF-MIB (per-interface tables)
IF_DESCR     = "1.3.6.1.2.1.2.2.1.2"   # ifDescr
IF_ADMIN     = "1.3.6.1.2.1.2.2.1.7"   # ifAdminStatus (1=up,2=down,3=testing)
IF_OPER      = "1.3.6.1.2.1.2.2.1.8"   # ifOperStatus  (1=up,2=down,...)
IF_SPEED     = "1.3.6.1.2.1.2.2.1.5"   # ifSpeed (bits per second)
IF_ALIAS     = "1.3.6.1.2.1.31.1.1.1.18"  # ifAlias (text description)
IF_HIGHSPEED = "1.3.6.1.2.1.31.1.1.1.15"  # ifHighSpeed (in Mbps)

# LLDP-MIB (IEEE 802.1AB) – remote tables (read-only)
LLDP_REM_SYSNAME = "1.0.8802.1.1.2.1.4.1.1.9"  # lldpRemSysName
LLDP_REM_PORTID  = "1.0.8802.1.1.2.1.4.1.1.7"  # lldpRemPortId
# (Mgmt address tables exist too, but are more verbose to parse across variants)


# -------------------------------
# Helpers
# -------------------------------

def _safe_str(val) -> Optional[str]:
    """Convert SNMP values to plain strings (unicode), safely."""
    if val is None:
        return None
    if isinstance(val, bytes):
        return val.decode(errors="ignore")
    try:
        return str(val)
    except Exception:
        return None


def _walk_pairs(host: str, community: str, base_oid: str) -> List[Tuple[str, str]]:
    """
    Walk an OID subtree and return list of (oid, value_str).
    OID is string-form, value is already coerced to string.
    """
    out: List[Tuple[str, str]] = []
    for oid, value in snmp.walk(host, community, base_oid):
        out.append((str(oid), _safe_str(value)))
    return out


def _walk_index_map(host: str, community: str, base_oid: str) -> Dict[str, str]:
    """
    Walk a column OID and return {index: value}, where index is the last sub-id.
    Example: 1.3.6...1.2.<index> -> "<value>"
    """
    out: Dict[str, str] = {}
    for oid, val in _walk_pairs(host, community, base_oid):
        idx = oid.split(".")[-1]
        out[idx] = val
    return out


# -------------------------------
# Public poll functions
# -------------------------------

def poll_sysinfo(host: str, community: str) -> dict:
    """
    Returns basic system info: sysDescr & sysName.
    """
    try:
        descr = snmp.get(host, community, SYS_DESCR)
        name  = snmp.get(host, community, SYS_NAME)
        return {"sysDescr": _safe_str(descr), "sysName": _safe_str(name)}
    except Exception:
        # Return empty on failure so callers can proceed gracefully.
        return {}


def poll_interfaces(host: str, community: str) -> List[dict]:
    """
    Returns a list of interface dicts with:
      - index (str)
      - name (ifDescr)
      - admin_up (bool from ifAdminStatus == 1)
      - oper_up  (bool from ifOperStatus  == 1)
      - speed (prefers ifHighSpeed in Mbps; falls back to ifSpeed in bps)
      - desc  (ifAlias, optional user description)
    """
    try:
        descr = _walk_index_map(host, community, IF_DESCR)
        admin = _walk_index_map(host, community, IF_ADMIN)
        oper  = _walk_index_map(host, community, IF_OPER)
        speed = _walk_index_map(host, community, IF_SPEED)
        alias = _walk_index_map(host, community, IF_ALIAS)
        hspd  = _walk_index_map(host, community, IF_HIGHSPEED)
    except Exception:
        return []

    out: List[dict] = []
    for idx, name in descr.items():
        # Prefer high-speed if present; else raw ifSpeed
        hs = hspd.get(idx)
        sp = hs if (hs and hs.isdigit()) else speed.get(idx)
        out.append({
            "index": idx,
            "name": name,
            "admin_up": admin.get(idx) == "1",
            "oper_up":  oper.get(idx) == "1",
            "speed":    sp,                 # Mbps if from ifHighSpeed, else bps (string)
            "desc":     alias.get(idx),     # interface description (if set)
        })
    return out


def poll_lldp_neighbors(host: str, community: str) -> List[dict]:
    """
    Returns a list of LLDP neighbor dicts keyed by the last 3 sub-ids of each row:
      - instance: "<localPort>.<remIndex>.<remSubIndex>"
      - remote_sysname
      - remote_port
    (Local interface mapping can be added in a future iteration with LLDP localPort tables.)
    """
    try:
        sysnames = _walk_pairs(host, community, LLDP_REM_SYSNAME)
        ports    = _walk_pairs(host, community, LLDP_REM_PORTID)
    except Exception:
        return []

    # Build maps keyed by the last 3 sub-ids to correlate rows across columns.
    def k3(oid: str) -> str:
        return ".".join(oid.split(".")[-3:])

    sys_map: Dict[str, str] = {k3(oid): val for oid, val in sysnames}
    port_map: Dict[str, str] = {k3(oid): val for oid, val in ports}

    out: List[dict] = []
    for inst, rname in sys_map.items():
        out.append({
            "instance": inst,
            "remote_sysname": rname,
            "remote_port": port_map.get(inst),
        })
    return out
