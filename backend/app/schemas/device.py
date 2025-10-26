from __future__ import annotations
from typing import Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


# ----------------------------
# Device CRUD / Responses
# ----------------------------

class DeviceBase(BaseModel):
    hostname: Optional[str] = None
    mgmt_ip: Optional[str] = None
    mac: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    notes: Optional[str] = None
    # store extra attributes collected from scans, SNMP, etc.
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Arbitrary metadata bag")

class DeviceCreate(DeviceBase):
    # For manual creation we at least want an IP
    mgmt_ip: str

class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    mgmt_ip: Optional[str] = None
    mac: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

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
    # expose DB column `metadata_` as `metadata` in API responses
    metadata: Optional[dict[str, Any]] = Field(default=None, serialization_alias="metadata")
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True  # pydantic v2: allows ORM -> model


# ----------------------------
# Juniper config generation
# ----------------------------

class GenJuniperConfigIn(BaseModel):
    hostname: str
    mgmt_ip: str
    vlans: List[dict]  # [{"vid":10,"name":"LAN","subnet":"192.168.10.0/24","gateway":"192.168.10.1/24"}, ...]
    uplink_if: str = "ge-0/0/0"
    trunk_ifs: List[str] = []
    access_ports: List[dict] = []  # [{"if":"ge-0/0/5","vlan":10}, ...]
    style: str = "set"  # or "hier"
