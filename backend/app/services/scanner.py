import nmap
from typing import Dict, List

PROFILES: Dict[str, str] = {
    "fast":     "-T4 -sS -F -sV --version-light --host-timeout 10s --max-retries 1",
    "standard": "-T3 -sS -sV --host-timeout 20s --max-retries 2",
    "deep":     "-T3 -sS -sU -sV -O --host-timeout 45s --max-retries 1",
}

def run_nmap_scan(targets: List[str], profile: str = "fast", skip_ping: bool = False) -> dict:
    base_args = PROFILES.get(profile, PROFILES["fast"])
    if skip_ping:
        base_args = f"{base_args} -Pn"

    nm = nmap.PortScanner()
    nm.scan(hosts=",".join(targets), arguments=base_args)

    results = {}
    for host in nm.all_hosts():
        h = nm[host]
        if (h.state() or "").lower() != "up":
            continue  # ← filter out non-up targets

        hostname = h.hostname() or None
        mac = (h.get("addresses") or {}).get("mac")
        vendor = None
        if mac:
            vend = h.get("vendor") or {}
            vendor = vend.get(mac) or (next(iter(vend.values())) if vend else None)

        osmatch = h.get("osmatch") or []
        os_name = osmatch[0]["name"] if osmatch else None

        services = []
        for proto in ("tcp", "udp"):
            table = h.get(proto) or {}
            for port, pdata in table.items():
                services.append({
                    "port": port,
                    "proto": proto,
                    "name": pdata.get("name"),
                    "product": pdata.get("product"),
                    "version": pdata.get("version"),
                    "state": pdata.get("state"),
                })

        results[host] = {
            "hostname": hostname,
            "mac": mac,
            "vendor": vendor,
            "os": os_name,
            "services": services,
        }
    return results
