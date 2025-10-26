import nmap


def run_nmap_scan(targets: list[str]) -> dict:
    nm = nmap.PortScanner()
    nm.scan(
        hosts=",".join(targets),
        arguments="-sS -sU -sV -O --host-timeout 30s --max-retries 1"
)
    results = {}
    for host in nm.all_hosts():
        h = nm[host]
        results[host] = {
            "hostname": h.hostname() or None,
        "state": h.state(),
        "vendor": h.get("vendor", {}),
        "osmatch": h.get("osmatch", []),
        "tcp": h.get("tcp", {}),
        "udp": h.get("udp", {}),
        "addresses": h.get("addresses", {}),
}
    return results