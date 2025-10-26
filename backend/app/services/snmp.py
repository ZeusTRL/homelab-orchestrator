from typing import Optional, List, Dict
# --- SNMP imports (compatible with pysnmp 4.x/5.x/6.x) ---
try:
    # Some 6.x builds expose the old flat hlapi
    from pysnmp.hlapi import (
        SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
        ObjectType, ObjectIdentity, getCmd, nextCmd
    )
except ImportError:
    try:
        # Other 6.x builds expose v3arch.* layout
        from pysnmp.hlapi.v3arch import (
            SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
            ObjectType, ObjectIdentity, getCmd, nextCmd
        )
    except ImportError as e:
        raise ImportError(
            "Could not import pysnmp HLAPI. Ensure pysnmp is installed. "
            "Tried 'pysnmp.hlapi' and 'pysnmp.hlapi.v3arch'."
        ) from e


# Common OIDs
SYS_NAME   = ObjectIdentity('SNMPv2-MIB', 'sysName', 0)
SYS_DESCR  = ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0)

# IF-MIB
IF_DESCR   = ObjectIdentity('IF-MIB', 'ifDescr')
IF_ADMIN   = ObjectIdentity('IF-MIB', 'ifAdminStatus')
IF_OPER    = ObjectIdentity('IF-MIB', 'ifOperStatus')
IF_SPEED   = ObjectIdentity('IF-MIB', 'ifSpeed')

# LLDP-MIB (neighbors)
LLDP_REM_SYSNAME = ObjectIdentity('LLDP-MIB', 'lldpRemSysName')
LLDP_REM_PORTID  = ObjectIdentity('LLDP-MIB', 'lldpRemPortId')
LLDP_REM_ADDR    = ObjectIdentity('LLDP-MIB', 'lldpRemManAddrIfId')  # we’ll fetch addr via addr table below
LLDP_REM_MANADDR = ObjectIdentity('LLDP-MIB', 'lldpRemManAddrIfSubtype')  # present = mgmt address table exists

def _get(host, community, oid) -> Optional[str]:
    engine = SnmpEngine()
    errorIndication, errorStatus, errorIndex, varBinds = next(getCmd(
        engine,
        CommunityData(community, mpModel=1),  # SNMPv2
        UdpTransportTarget((host, 161), timeout=1, retries=1),
        ContextData(),
        ObjectType(oid)
    ))
    if errorIndication or errorStatus:
        return None
    return str(varBinds[0][1])

def _walk(host, community, oid_root) -> List[Dict]:
    engine = SnmpEngine()
    out = []
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        engine,
        CommunityData(community, mpModel=1),
        UdpTransportTarget((host, 161), timeout=1, retries=1),
        ContextData(),
        ObjectType(oid_root),
        lexicographicMode=False
    ):
        if errorIndication or errorStatus:
            break
        row = {}
        for vb in varBinds:
            row[str(vb[0])] = str(vb[1])
        out.append(row)
    return out

def poll_sysinfo(host: str, community: str) -> dict:
    return {
        "sysName":  _get(host, community, SYS_NAME),
        "sysDescr": _get(host, community, SYS_DESCR),
    }

def poll_interfaces(host: str, community: str) -> list[dict]:
    if_descr = _walk(host, community, IF_DESCR)
    if_admin = _walk(host, community, IF_ADMIN)
    if_oper  = _walk(host, community, IF_OPER)
    if_speed = _walk(host, community, IF_SPEED)

    # Build index → value maps
    def idxmap(rows):  # rows like {'1.3.6...ifDescr.X': 'ge-0/0/1'}
        m = {}
        for r in rows:
            for k, v in r.items():
                idx = k.split('.')[-1]
                m[idx] = v
        return m

    d = idxmap(if_descr); a = idxmap(if_admin); o = idxmap(if_oper); s = idxmap(if_speed)

    out = []
    for idx, name in d.items():
        out.append({
            "index": idx,
            "name": name,
            "admin_up": a.get(idx) == '1',
            "oper_up":  o.get(idx) == '1',
            "speed":    s.get(idx)
        })
    return out

def poll_lldp_neighbors(host: str, community: str) -> list[dict]:
    # Minimal LLDP: remote system name and port id tables
    sysnames = _walk(host, community, LLDP_REM_SYSNAME)
    ports    = _walk(host, community, LLDP_REM_PORTID)

    # Flatten by instance suffix (last 3 indices typically: localPort, remIndex, remSubindex)
    def parse(rows):
        m = {}
        for r in rows:
            for k, v in r.items():
                inst = '.'.join(k.split('.')[-3:])
                m[inst] = v
        return m

    sn = parse(sysnames)
    pt = parse(ports)

    out = []
    for inst, rname in sn.items():
        out.append({
            "instance": inst,
            "remote_sysname": rname,
            "remote_port": pt.get(inst)
        })
    return out
