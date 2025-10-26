from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from .base import Base

class ConfigBackup(Base):
    __tablename__ = "config_backups"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    vendor = Column(String, index=True)      # "juniper" | "pfsense" | ...
    path = Column(String)                    # absolute path to saved file
    sha256 = Column(String, index=True)      # quick integrity/dedup
