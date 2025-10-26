# Homelab Orchestrator – MVP


## What works now
- Device discovery via Nmap (TCP/UDP/OS guess), `POST /scan?targets=192.168.1.0/24&targets=10.0.0.0/24`
- Store minimal device records
- Generate Juniper EX3300 configs from VLAN/IP input (set-style or hierarchical)
- Export ZIP bundle of generated configs
- SSH push helper for JunOS (dry-run with `show | compare` or commit)


## Next up
- Services table population, VLAN/IP models, rule checks (no overlaps, risky ports)
- LLDP/SNMP ingestion (topology), change simulation
- React UI