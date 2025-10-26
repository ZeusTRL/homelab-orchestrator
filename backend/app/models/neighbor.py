from sqlalchemy import Column, Integer, String, ForeignKey
from .base import Base

class Neighbor(Base):
    __tablename__ = "neighbors"
    id = Column(Integer, primary_key=True)
    local_device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    local_if = Column(String)
    remote_sysname = Column(String)
    remote_port = Column(String)
    remote_mgmt_ip = Column(String)
