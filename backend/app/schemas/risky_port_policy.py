"""
Pydantic schemas for global risky port policy API.
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

ProtocolLiteral = Literal["tcp", "udp", "both"]
SeverityLiteral = Literal["info", "warning", "high"]


class RiskyPortPolicyEntryBase(BaseModel):
    protocol: ProtocolLiteral
    port_start: int = Field(..., ge=1, le=65535)
    port_end: int = Field(..., ge=1, le=65535)
    label: str = Field(..., min_length=1, max_length=500)
    recommendation: Optional[str] = Field(None, max_length=2000)
    severity: SeverityLiteral
    enabled: bool = True
    sort_order: int = 0

    @model_validator(mode="after")
    def port_end_gte_start(self):
        if self.port_end < self.port_start:
            raise ValueError("port_end must be >= port_start")
        return self


class RiskyPortPolicyEntryCreate(RiskyPortPolicyEntryBase):
    pass


class RiskyPortPolicyEntryResponse(RiskyPortPolicyEntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RiskyPortPolicyReplaceRequest(BaseModel):
    entries: List[RiskyPortPolicyEntryCreate] = Field(default_factory=list)
