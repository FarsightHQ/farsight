from pydantic import BaseModel
from typing import List, Optional

class IPRelationship(BaseModel):
    """Represents a single firewall rule relationship involving an IP"""
    rule_id: int
    request_id: int
    request_name: str
    action: str
    direction: Optional[str]
    ip_role: str  # "SOURCE" or "DESTINATION"
    source_ip: str
    destination_ip: str
    protocol: str
    port_ranges: str

    class Config:
        from_attributes = True

class IPRuleResponse(BaseModel):
    """Summary response for IP rule queries"""
    ip_address: str
    total_rules: int
    source_rules: int
    destination_rules: int
    relationships: List[IPRelationship]

    class Config:
        from_attributes = True
