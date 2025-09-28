"""
Standardized response schemas for FAR API endpoints
Provides consistent response formats and proper OpenAPI documentation
"""
from typing import Dict, List, Any, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Generic type for data payloads
T = TypeVar('T')


class StatusEnum(str, Enum):
    """Standard status values"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"


class PaginationModel(BaseModel):
    """Standard pagination metadata"""
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum number of items returned")
    total: int = Field(..., description="Total number of items available")
    returned: int = Field(..., description="Number of items in this response")
    has_next: bool = Field(..., description="Whether more items are available")
    has_previous: bool = Field(..., description="Whether previous items exist")


class ErrorDetailModel(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class StandardResponse(BaseModel, Generic[T]):
    """Standard response format for all API endpoints"""
    status: StatusEnum = Field(..., description="Response status")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[T] = Field(None, description="Response payload")
    errors: Optional[List[ErrorDetailModel]] = Field(None, description="Error details if any")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request correlation ID")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response format"""
    status: StatusEnum = Field(..., description="Response status")
    message: str = Field(..., description="Human-readable response message")
    data: List[T] = Field(..., description="Array of response items")
    pagination: PaginationModel = Field(..., description="Pagination metadata")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request correlation ID")


# Specific response models for FAR domains
class RuleEndpointModel(BaseModel):
    """Model for rule endpoint data"""
    id: int = Field(..., description="Endpoint ID")
    type: str = Field(..., description="Endpoint type (source/destination)")
    network_cidr: str = Field(..., description="Network CIDR notation")


class RuleServiceModel(BaseModel):
    """Model for rule service data"""
    id: int = Field(..., description="Service ID")
    protocol: str = Field(..., description="Network protocol")
    port_ranges: str = Field(..., description="Port ranges")
    service_type: str = Field(..., description="Service classification")


class AssetModel(BaseModel):
    """Model for asset registry data"""
    ip_address: str = Field(..., description="Asset IP address")
    hostname: Optional[str] = Field(None, description="Asset hostname")
    environment: Optional[str] = Field(None, description="Environment")
    os_name: Optional[str] = Field(None, description="Operating system")
    location: Optional[str] = Field(None, description="Physical location")
    segment: Optional[str] = Field(None, description="Network segment")
    vlan: Optional[str] = Field(None, description="VLAN ID")
    availability: Optional[str] = Field(None, description="Availability status")


class GraphNodeModel(BaseModel):
    """Model for graph visualization nodes"""
    id: str = Field(..., description="Unique node identifier")
    type: str = Field(..., description="Node type")
    label: str = Field(..., description="Display label")
    group: str = Field(..., description="Node grouping")
    size: int = Field(..., description="Node size for visualization")
    color: str = Field(..., description="Node color")
    tooltip: str = Field(..., description="Tooltip text")


class GraphLinkModel(BaseModel):
    """Model for graph visualization links"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Link type")
    label: str = Field(..., description="Link label")


class GraphDataModel(BaseModel):
    """Model for complete graph visualization data"""
    nodes: List[GraphNodeModel] = Field(..., description="Graph nodes")
    links: List[GraphLinkModel] = Field(..., description="Graph links")
    metadata: Dict[str, Any] = Field(..., description="Graph metadata")
    layout_hints: Optional[Dict[str, Any]] = Field(None, description="Layout configuration")


class NetworkTupleModel(BaseModel):
    """Model for network tuple data"""
    source: str = Field(..., description="Source network")
    destination: str = Field(..., description="Destination network")
    protocol: str = Field(..., description="Protocol")
    ports: str = Field(..., description="Port specification")
    tuple_id: str = Field(..., description="Unique tuple identifier")
    service_type: str = Field(..., description="Service classification")


class TupleAnalysisModel(BaseModel):
    """Model for tuple analysis data"""
    tuples: List[NetworkTupleModel] = Field(..., description="Generated tuples")
    total_count: int = Field(..., description="Total tuple count")
    summary: Dict[str, int] = Field(..., description="Tuple summary statistics")
    analysis: Dict[str, Any] = Field(..., description="Complexity analysis")


class SecurityIssueModel(BaseModel):
    """Model for security analysis issues"""
    type: str = Field(..., description="Issue type")
    severity: str = Field(..., description="Issue severity")
    description: str = Field(..., description="Issue description")
    impact: Optional[str] = Field(None, description="Potential impact")


class SecurityAnalysisModel(BaseModel):
    """Model for security analysis results"""
    security_score: int = Field(..., description="Security score (0-100)")
    risk_level: str = Field(..., description="Risk level")
    issues: List[SecurityIssueModel] = Field(..., description="Identified issues")
    recommendations: List[str] = Field(..., description="Security recommendations")
    compliance: Dict[str, bool] = Field(..., description="Compliance status")


class RuleDetailsModel(BaseModel):
    """Model for comprehensive rule details"""
    rule_id: int = Field(..., description="Rule ID")
    request: Dict[str, Any] = Field(..., description="Parent request information")
    rule_details: Dict[str, Any] = Field(..., description="Basic rule metadata")
    endpoints: Dict[str, Any] = Field(..., description="Rule endpoints")
    services: List[RuleServiceModel] = Field(..., description="Rule services")
    service_count: int = Field(..., description="Number of services")
    facts: Optional[Dict[str, Any]] = Field(None, description="Computed facts")
    tuple_estimate: int = Field(..., description="Estimated tuple count")
    assets: Optional[Dict[str, List[AssetModel]]] = Field(None, description="Related assets")
    graph: Optional[GraphDataModel] = Field(None, description="Graph visualization data")
    tuples: Optional[TupleAnalysisModel] = Field(None, description="Network tuples")
    analysis: Optional[SecurityAnalysisModel] = Field(None, description="Security analysis")


class RequestSummaryModel(BaseModel):
    """Model for request summary statistics"""
    request_id: int = Field(..., description="Request ID")
    request_info: Dict[str, Any] = Field(..., description="Request metadata")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    endpoint_analysis: Dict[str, Any] = Field(..., description="Endpoint analysis")
    protocol_distribution: Dict[str, int] = Field(..., description="Protocol distribution")
    complexity_analysis: Dict[str, str] = Field(..., description="Complexity metrics")


class NetworkTopologyModel(BaseModel):
    """Model for network topology visualization"""
    request_id: int = Field(..., description="Request ID")
    request_title: str = Field(..., description="Request title")
    topology: GraphDataModel = Field(..., description="Network topology graph")
    summary: Dict[str, int] = Field(..., description="Topology summary")


# Response type aliases for common patterns
RuleDetailsResponse = StandardResponse[RuleDetailsModel]
RuleEndpointsResponse = StandardResponse[Dict[str, Any]]  # For rule endpoints
RuleServicesResponse = StandardResponse[Dict[str, Any]]   # For rule services
RequestSummaryResponse = StandardResponse[RequestSummaryModel]
NetworkTopologyResponse = StandardResponse[NetworkTopologyModel]
PaginatedRulesResponse = PaginatedResponse[Dict[str, Any]]  # For rule listings


class APIErrorResponse(BaseModel):
    """Standardized error response format"""
    status: StatusEnum = Field(StatusEnum.ERROR, description="Always 'error' for error responses")
    message: str = Field(..., description="High-level error message")
    errors: List[ErrorDetailModel] = Field(..., description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    path: Optional[str] = Field(None, description="API path that caused the error")
    method: Optional[str] = Field(None, description="HTTP method used")


class ValidationErrorResponse(BaseModel):
    """Validation error response format"""
    status: StatusEnum = Field(StatusEnum.ERROR, description="Always 'error' for validation errors")
    message: str = Field("Validation failed", description="Error message")
    errors: List[ErrorDetailModel] = Field(..., description="Field validation errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request correlation ID")


# HTTP status code to error type mapping
ERROR_TYPES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED", 
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE"
}


# FAR-specific response models
class IpDetailsModel(BaseModel):
    """IP address details with asset and rule information"""
    ip_address: str = Field(..., description="IP address")
    ip_type: str = Field(..., description="Type: 'source', 'destination', or 'both'")
    rule_count: int = Field(..., description="Number of rules involving this IP")
    asset_info: Optional[Dict[str, Any]] = Field(None, description="Asset registry information if available")
    networks: List[str] = Field(default_factory=list, description="Network CIDRs this IP belongs to")


class FarIpSummaryModel(BaseModel):
    """Summary of all IPs in a FAR request"""
    request_id: int = Field(..., description="FAR request ID")
    total_ips: int = Field(..., description="Total unique IP addresses")
    source_ips: int = Field(..., description="Number of source IPs")
    destination_ips: int = Field(..., description="Number of destination IPs") 
    overlapping_ips: int = Field(..., description="IPs that appear as both source and destination")


class FarIpsResponse(BaseModel):
    """Complete response for FAR request IP analysis"""
    summary: FarIpSummaryModel = Field(..., description="High-level statistics")
    ips: List[IpDetailsModel] = Field(..., description="Detailed IP information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional analysis metadata")
