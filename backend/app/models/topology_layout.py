from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint, Index
from .base import Base

class TopologyLayout(Base):
    __tablename__ = "topology_layouts"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    pos_x = Column(Float, nullable=False)
    pos_y = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("device_id", name="uq_topo_layout_device"),
        Index("ix_topo_layout_device", "device_id"),
    )
