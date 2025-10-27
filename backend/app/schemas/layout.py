from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class LayoutPoint(BaseModel):
    device_id: int
    x: float = Field(..., description="Canvas X coordinate")
    y: float = Field(..., description="Canvas Y coordinate")

class LayoutSetRequest(BaseModel):
    points: List[LayoutPoint]

class LayoutGetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # Map device_id -> {x,y}
    points: dict[int, dict[str, float]]
