from typing import List, Optional
from pydantic import BaseModel, Field


class CorrelationNode(BaseModel):
    id: str
    name: str
    sector: str
    price: float


class CorrelationLink(BaseModel):
    source: str
    target: str
    correlation: float = Field(..., ge=-1.0, le=1.0)
    weight: float


class CorrelationNetworkResponse(BaseModel):
    nodes: List[CorrelationNode]
    links: List[CorrelationLink]
    timestamp: int
