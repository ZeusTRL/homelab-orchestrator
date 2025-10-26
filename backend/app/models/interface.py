from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Interface(Base):
    __tablename__ = "interfaces"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    name = Column(String, index=True)
    mac = Column(String)
    admin_up = Column(Boolean, default=None)
    oper_up = Column(Boolean, default=None)
    speed = Column(String, default=None)
