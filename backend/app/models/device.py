from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from .base import Base


class Device(Base):
    __tablename__ = "devices"


    id = Column(Integer, primary_key=True)
    hostname = Column(String, index=True)
    mgmt_ip = Column(String, index=True)
    mac = Column(String, index=True)
    vendor = Column(String)
    model = Column(String)
    serial = Column(String)
    os = Column(String)
    os_version = Column(String)
    notes = Column(String)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    metadata_ = Column("metadata", JSON, default=dict)