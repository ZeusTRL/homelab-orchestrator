from pydantic import BaseModel
from typing import Optional, Any


class DeviceOut(BaseModel):
    id: int
    hostname: Optional[str] = None
    mgmt_ip: Optional[str] = None
    mac: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    notes: Optional[str] = None


    class Config:
        from_attributes = True


class GenJuniperConfigIn(BaseModel):
    hostname: str
    mgmt_ip: str
    vlans: list[dict] # [{"vid":10, "name":"LAN", "subnet":"192.168.10.0/24", "gateway":"192.168.10.1"}, ...]
    uplink_if: str = "ge-0/0/0"
    trunk_ifs: list[str] = []
    access_ports: list[dict] = [] # [{"if":"ge-0/0/5", "vlan":10}, ...]
    style: str = "set" # or "hier"