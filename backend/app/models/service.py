from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Service(Base):
    __tablename__ = "services"


    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    port = Column(Integer)
    proto = Column(String)
    name = Column(String)
    product = Column(String)
    version = Column(String)