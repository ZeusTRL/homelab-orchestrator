from __future__ import annotations
from typing import Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


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
    # For request bodies we accept/return a field named "metadata"
    metadata: Optional[dict[str, Any]] = None


class DeviceCreate(DeviceBase):
    # Minimal required field if creating manually
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
    # Pydantic v2 config (no class Config!)
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

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
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    # Read from ORM attribute `metadata_`, but serialize as "metadata"
    metadata_: Optional[dict[str, Any]] = Field(
        default=None,
        serialization_alias="metadata",
    )


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
