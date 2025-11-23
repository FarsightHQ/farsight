"""
FAR Rules API endpoints
Handles CRUD operations and queries for individual firewall rules
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.far_rule import FarRule
from app.models.far_request import FarRequest
from app.services.asset_service import AssetService
from app.services.graph_service import GraphService
from app.services.tuple_generation_service import TupleGenerationService
from app.utils.error_handlers import success_response
from app.utils.csv_errors import DatabaseConnectionError
from app.schemas.responses import (
    StandardResponse, 
    StatusEnum, 
    FarRulesResponse, 
    FarRulesSummaryModel, 
    RuleDetailModel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["FAR Rules"])


@router.get("")
def get_all_far_rules(
    skip: int = Query(0, ge=0, description="Number of rules to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum rules to return"),
    request_id: Optional[int] = Query(None, description="Optional filter by request ID"),
    action: Optional[str] = Query(None, description="Optional filter by action (allow/deny)"),
    include_summary: bool = Query(True, description="Include summary statistics"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all FAR rules across all requests (or filtered by request_id)
    
    Returns comprehensive rule information:
    - Complete source/destination networks
    - Service details (protocols, ports)
    - Human-readable rule summaries
    - Request information for each rule
    - Rule statistics and analysis
    
    Query Parameters:
    - skip: Number of rules to skip (pagination)
    - limit: Maximum rules to return (pagination)
    - request_id: Optional filter by specific request ID
    - action: Optional filter by action (allow/deny)
    - include_summary: Include summary statistics
    """
    try:
        # Build query - no request_id filter means all requests
        rules_query = db.query(FarRule).join(FarRequest)
        
        if request_id:
            rules_query = rules_query.filter(FarRule.request_id == request_id)
        
        if action:
            rules_query = rules_query.filter(FarRule.action.ilike(f"%{action}%"))
        
        total_rules = rules_query.count()
        rules = rules_query.order_by(FarRule.id.desc()).offset(skip).limit(limit).all()
        
        # Process rules to extract human-readable information
        enhanced_rules = []
        all_sources = set()
        all_destinations = set()
        all_protocols = set()
        allow_rules = 0
        deny_rules = 0
        total_tuple_estimate = 0
        
        for rule in rules:
            # Extract source networks
            source_networks = [
                ep.network_cidr for ep in rule.endpoints 
                if ep.endpoint_type == 'source'
            ]
            all_sources.update(source_networks)
            
            # Extract destination networks
            destination_networks = [
                ep.network_cidr for ep in rule.endpoints 
                if ep.endpoint_type == 'destination'
            ]
            all_destinations.update(destination_networks)
            
            # Extract protocols and ports
            protocols = []
            port_ranges = []
            for service in rule.services:
                protocols.append(service.protocol)
                port_ranges.append(str(service.port_ranges))
                all_protocols.add(service.protocol)
            
            # Count rule types
            if str(rule.action).upper() == 'ALLOW':
                allow_rules += 1
            elif str(rule.action).upper() == 'DENY':
                deny_rules += 1
            
            # Calculate tuple estimate for this rule
            tuple_estimate = len(source_networks) * len(destination_networks) * len(rule.services)
            total_tuple_estimate += tuple_estimate
            
            # Generate human-readable summary
            rule_summary = _generate_rule_summary(
                str(rule.action), source_networks, destination_networks, protocols, port_ranges
            )
            
            # Get request information
            request_info = {
                "id": rule.request.id,
                "title": rule.request.title,
                "external_id": rule.request.external_id,
                "status": rule.request.status
            }
            
            # Create enhanced rule model with request info
            # We'll add request info to the rule data since RuleDetailModel doesn't include it
            enhanced_rule_dict = {
                "id": rule.id,
                "action": rule.action,
                "direction": rule.direction,
                "source_networks": source_networks,
                "source_count": len(source_networks),
                "destination_networks": destination_networks,
                "destination_count": len(destination_networks),
                "protocols": protocols,
                "port_ranges": port_ranges,
                "service_count": len(rule.services),
                "created_at": rule.created_at.isoformat(),
                "rule_hash": rule.canonical_hash.hex() if rule.canonical_hash is not None else None,
                "tuple_estimate": tuple_estimate,
                "rule_summary": rule_summary,
                "request": request_info  # Add request information
            }
            
            # Create RuleDetailModel (will ignore extra fields like 'request')
            enhanced_rule = RuleDetailModel(**{k: v for k, v in enhanced_rule_dict.items() if k != 'request'})
            # Store the full dict for response
            enhanced_rules.append({
                "rule": enhanced_rule,
                "request": request_info
            })
        
        # Create summary if requested
        summary = FarRulesSummaryModel(
            total_rules=total_rules,
            allow_rules=allow_rules,
            deny_rules=deny_rules,
            unique_sources=len(all_sources),
            unique_destinations=len(all_destinations),
            protocols_used=list(all_protocols),
            estimated_tuples=total_tuple_estimate
        ) if include_summary else FarRulesSummaryModel(
            total_rules=0,
            allow_rules=0,
            deny_rules=0,
            unique_sources=0,
            unique_destinations=0,
            protocols_used=[],
            estimated_tuples=0
        )
        
        # Create pagination info
        pagination = {
            "skip": skip,
            "limit": limit,
            "total": total_rules,
            "returned": len(enhanced_rules),
            "has_next": skip + limit < total_rules,
            "has_previous": skip > 0
        }
        
        # Format rules for response (include request info)
        rules_for_response = []
        for item in enhanced_rules:
            rule_dict = item["rule"].model_dump(exclude_none=False)
            rule_dict["request"] = item["request"]
            rules_for_response.append(rule_dict)
        
        # Create response data
        # Note: We need to work around the schema - FarRulesResponse expects List[RuleDetailModel]
        # but we need to include request info. We'll use dict() to convert and add request info
        response_data = {
            "far_request_id": request_id if request_id else 0,  # Use 0 for global view
            "summary": summary.dict(),
            "rules": rules_for_response,  # List of dicts with request info
            "pagination": pagination,
            "metadata": {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "processing_notes": "Enhanced human-readable rule format with request information",
                "filter_applied": {
                    "request_id": request_id,
                    "action": action
                } if request_id or action else None
            }
        }
        
        # Return response compatible with FarRulesResponse but with request info in rules
        return success_response(
            data=response_data,
            message=f"Retrieved {len(enhanced_rules)} enhanced rules" + (f" for request {request_id}" if request_id else " across all requests")
        )
    except OperationalError as e:
        logger.error(f"Database connection error getting FAR rules: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving FAR rules",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error getting FAR rules: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve FAR rules: {str(e)}")


def _generate_rule_summary(action: str, sources: List[str], destinations: List[str], 
                          protocols: List[str], ports: List[str]) -> str:
    """
    Generate a human-readable summary of a firewall rule
    """
    # Simplify network lists for display
    src_display = f"{len(sources)} source{'s' if len(sources) != 1 else ''}"
    if len(sources) == 1:
        src_display = sources[0]
    elif len(sources) <= 3:
        src_display = ", ".join(sources)
    
    dst_display = f"{len(destinations)} destination{'s' if len(destinations) != 1 else ''}"
    if len(destinations) == 1:
        dst_display = destinations[0]
    elif len(destinations) <= 3:
        dst_display = ", ".join(destinations)
    
    # Simplify protocol/port display
    service_display = ""
    if protocols:
        if len(protocols) == 1:
            protocol = protocols[0].upper()
            if ports and len(ports) == 1:
                service_display = f" on {protocol} port {ports[0]}"
            else:
                service_display = f" using {protocol}"
        else:
            service_display = f" using {'/'.join(set(protocols)).upper()}"
    
    return f"{action.upper()}: {src_display} → {dst_display}{service_display}"


@router.get("/{rule_id}")
def get_far_rule_details(
    rule_id: int,
    format: Optional[str] = None,
    include: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get detailed information for a specific FAR rule by ID
    
    Query Parameters:
    - format: Output format ('table' for human-readable, 'json' for API format)
    - include: Additional data to include (comma-separated):
      - 'assets': Include matching asset registry information
      - 'graph': Include D3-compatible graph visualization data
      - 'tuples': Include actual network tuples generated by this rule
      - 'analysis': Include security analysis and recommendations
      - 'all': Include all available data
    
    Returns comprehensive rule details including:
    - Basic rule information (action, direction, etc.)
    - All source and destination endpoints
    - All services (protocols and port ranges)
    - Computed facts (if available)
    - Related request information
    - Optional: Asset details, graph data, security analysis
    """
    try:
        # Get the rule with its relationships
        rule = db.query(FarRule).filter(FarRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        # Parse include parameter
        includes = []
        if include:
            if include == 'all':
                includes = ['assets', 'graph', 'tuples', 'analysis']
            else:
                includes = [item.strip() for item in include.split(',')]
        
        # Get request information
        request_info = {
            "id": rule.request.id,
            "title": rule.request.title,
            "external_id": rule.request.external_id,
            "status": rule.request.status
        }
        
        # Organize endpoints by type
        sources = []
        destinations = []
        for endpoint in rule.endpoints:
            endpoint_data = {"network_cidr": endpoint.network_cidr}
            if endpoint.endpoint_type == 'source':
                sources.append(endpoint_data)
            elif endpoint.endpoint_type == 'destination':
                destinations.append(endpoint_data)
        
        # Format services
        services = []
        for service in rule.services:
            services.append({
                "protocol": service.protocol,
                "port_ranges": str(service.port_ranges)  # PostgreSQL multirange format
            })
        
        # Parse facts if available
        facts = rule.facts if rule.facts is not None else None
        facts_dict = facts if facts is not None and isinstance(facts, dict) else {}
        
        # Calculate tuple estimate using TupleGenerationService
        tuple_service = TupleGenerationService()
        tuple_estimate = tuple_service.calculate_tuple_estimate(
            len(sources), len(destinations), len(services)
        ) if sources and destinations else 0
        
        # Base response
        response = {
            "rule_id": rule_id,
            "request": request_info,
            "rule_details": {
                "action": rule.action,
                "direction": rule.direction,
                "created_at": rule.created_at.isoformat(),
                "canonical_hash": rule.canonical_hash.hex() if rule.canonical_hash is not None else None
            },
            "endpoints": {
                "sources": sources,
                "destinations": destinations,
                "source_count": len(sources),
                "destination_count": len(destinations)
            },
            "services": services,
            "service_count": len(services),
            "facts": facts,
            "tuple_estimate": tuple_estimate
        }
        
        # Add optional data based on includes
        if 'assets' in includes:
            response['assets'] = _get_rule_assets(rule_id, sources, destinations, db)
        
        if 'graph' in includes:
            response['graph'] = _get_rule_graph_data(rule_id, sources, destinations, services, db)
        
        if 'tuples' in includes:
            response['tuples'] = _get_rule_tuples(sources, destinations, services)
        
        if 'analysis' in includes:
            response['analysis'] = _get_rule_analysis(rule, facts_dict, sources, destinations, services)
        
        # Format response based on format parameter
        if format == 'table':
            return _format_rule_as_table(response)
        
        return success_response(
            data=response,
            message=f"Retrieved detailed information for rule {rule_id}"
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting rule details for {rule_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving rule details",
            details={"error": str(e), "rule_id": rule_id}
        )
    except Exception as e:
        logger.error(f"Error getting rule details for {rule_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rule details: {str(e)}")


@router.get("/{rule_id}/endpoints", response_model=Dict[str, Any])
def get_rule_endpoints(
    rule_id: int,
    endpoint_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get endpoints for a specific rule, optionally filtered by type
    
    Args:
        rule_id: The ID of the rule
        endpoint_type: Optional filter ('source' or 'destination')
    """
    try:
        rule = db.query(FarRule).filter(FarRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        endpoints = rule.endpoints
        if endpoint_type:
            endpoints = [ep for ep in endpoints if ep.endpoint_type == endpoint_type]
        
        data = {
            "rule_id": rule_id,
            "endpoints": [
                {
                    "id": ep.id,
                    "type": ep.endpoint_type,
                    "network_cidr": ep.network_cidr
                }
                for ep in endpoints
            ],
            "count": len(endpoints)
        }
        
        message = f"Retrieved {len(endpoints)} endpoints for rule {rule_id}"
        if endpoint_type:
            message += f" (filtered by type: {endpoint_type})"
        
        return success_response(
            data=data,
            message=message,
            metadata={"filter": endpoint_type} if endpoint_type else None
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting endpoints for rule {rule_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving rule endpoints",
            details={"error": str(e), "rule_id": rule_id}
        )
    except Exception as e:
        logger.error(f"Error getting endpoints for rule {rule_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rule endpoints: {str(e)}")


@router.get("/{rule_id}/services", response_model=Dict[str, Any])
def get_rule_services(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    Get services (protocols and ports) for a specific rule
    """
    try:
        rule = db.query(FarRule).filter(FarRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        services = []
        for service in rule.services:
            services.append({
                "id": service.id,
                "protocol": service.protocol,
                "port_ranges": str(service.port_ranges),
                "service_type": TupleGenerationService()._classify_service(
                    service.protocol, 
                    str(service.port_ranges)
                )
            })
        
        data = {
            "rule_id": rule_id,
            "services": services,
            "count": len(services)
        }
        
        return success_response(
            data=data,
            message=f"Retrieved {len(services)} services for rule {rule_id}"
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting services for rule {rule_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving rule services",
            details={"error": str(e), "rule_id": rule_id}
        )
    except Exception as e:
        logger.error(f"Error getting services for rule {rule_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rule services: {str(e)}")


# Helper functions
def _get_rule_assets(rule_id: int, sources: List[Dict], destinations: List[Dict], db: Session) -> Dict[str, Any]:
    """Get asset registry information for rule endpoints"""
    asset_service = AssetService(db)
    
    # Get assets for the rule endpoints
    source_assets = asset_service.get_assets_for_rule_endpoints(sources, [])
    dest_assets = asset_service.get_assets_for_rule_endpoints([], destinations)
    
    asset_matches = {
        "sources": source_assets,
        "destinations": dest_assets,
        "total_matches": len(source_assets) + len(dest_assets)
    }
    
    return asset_matches


def _get_rule_graph_data(rule_id: int, sources: List[Dict], destinations: List[Dict], services: List[Dict], db: Session) -> Dict[str, Any]:
    """Generate D3-compatible graph data for visualization with asset details"""
    asset_service = AssetService(db)
    graph_service = GraphService(asset_service)
    
    # Use the GraphService to create the rule graph
    graph_data = graph_service.create_rule_graph(
        sources=sources,
        destinations=destinations,
        services=services,
        rule_id=rule_id
    )
    
    return graph_data


def _get_rule_tuples(sources: List[Dict], destinations: List[Dict], services: List[Dict]) -> Dict[str, Any]:
    """Generate actual network tuples for this rule"""
    tuple_service = TupleGenerationService()
    
    # Use the TupleGenerationService to generate tuples
    return tuple_service.generate_rule_tuples(sources, destinations, services)


def _get_rule_analysis(rule: Any, facts: Dict, sources: List[Dict], destinations: List[Dict], services: List[Dict]) -> Dict[str, Any]:
    """Provide security analysis and recommendations for the rule"""
    analysis = {
        "security_score": 0,  # 0-100, higher is better
        "risk_level": "low",
        "issues": [],
        "recommendations": [],
        "compliance": {
            "zero_trust": False,
            "principle_of_least_privilege": True
        }
    }
    
    # Analyze based on facts
    if facts:
        # Check for any-any rules
        if facts.get("src_is_any") or facts.get("dst_is_any"):
            analysis["issues"].append({
                "type": "overly_permissive",
                "severity": "high",
                "description": "Rule uses 0.0.0.0/0 (any) for source or destination",
                "impact": "Allows unrestricted network access"
            })
            analysis["risk_level"] = "high"
            analysis["security_score"] -= 30
            analysis["recommendations"].append("Replace 0.0.0.0/0 with specific IP ranges")
        
        # Check for self-flow
        if facts.get("is_self_flow"):
            analysis["issues"].append({
                "type": "self_flow",
                "severity": "medium",
                "description": "Source and destination networks overlap",
                "impact": "May allow unintended lateral movement"
            })
            analysis["security_score"] -= 10
            analysis["recommendations"].append("Review if self-flow is intentional")
        
        # Check for public IP exposure
        if facts.get("src_has_public") or facts.get("dst_has_public"):
            analysis["issues"].append({
                "type": "public_exposure",
                "severity": "medium",
                "description": "Rule involves public IP addresses",
                "impact": "Potential exposure to internet traffic"
            })
            analysis["security_score"] -= 15
            analysis["recommendations"].append("Ensure public IP access is necessary and properly secured")
        
        # Check tuple expansion
        tuple_count = len(sources) * len(destinations) * max(len(services), 1)
        if tuple_count > 100:
            analysis["issues"].append({
                "type": "high_complexity",
                "severity": "low",
                "description": f"Rule generates {tuple_count} network tuples",
                "impact": "May impact firewall performance"
            })
            analysis["security_score"] -= 5
            analysis["recommendations"].append("Consider breaking into more specific rules")
    
    # Set baseline score
    analysis["security_score"] = max(0, 100 + analysis["security_score"])
    
    # Determine risk level based on score
    if analysis["security_score"] >= 80:
        analysis["risk_level"] = "low"
    elif analysis["security_score"] >= 60:
        analysis["risk_level"] = "medium"
    else:
        analysis["risk_level"] = "high"
    
    return analysis


def _format_rule_as_table(response: Dict[str, Any]) -> Dict[str, Any]:
    """Format rule response as human-readable table data"""
    rule_info = response["rule_details"]
    endpoints = response["endpoints"]
    services = response["services"]
    
    # Create a summary table
    table_data = {
        "rule_summary": {
            "Rule ID": response["rule_id"],
            "Action": rule_info["action"],
            "Direction": rule_info["direction"],
            "Request": f"{response['request']['title']} (ID: {response['request']['id']})",
            "Sources": f"{endpoints['source_count']} networks",
            "Destinations": f"{endpoints['destination_count']} networks",
            "Services": f"{response['service_count']} protocols",
            "Tuple Estimate": response["tuple_estimate"]
        },
        "endpoints_table": {
            "sources": [src["network_cidr"] for src in endpoints["sources"]],
            "destinations": [dst["network_cidr"] for dst in endpoints["destinations"]]
        },
        "services_table": [
            {
                "Protocol": svc["protocol"].upper(),
                "Port Range": svc["port_ranges"].strip('{}').strip('[]'),
                "Service Type": TupleGenerationService()._classify_service(svc["protocol"], svc["port_ranges"])
            }
            for svc in services
        ]
    }
    
    # Add optional sections if present
    if "assets" in response:
        table_data["assets_summary"] = {
            "Total Assets Found": response["assets"]["total_matches"],
            "Source Assets": len(response["assets"]["sources"]),
            "Destination Assets": len(response["assets"]["destinations"])
        }
    
    if "analysis" in response:
        analysis = response["analysis"]
        table_data["security_analysis"] = {
            "Security Score": f"{analysis['security_score']}/100",
            "Risk Level": analysis["risk_level"].upper(),
            "Issues Found": len(analysis["issues"]),
            "Recommendations": len(analysis["recommendations"])
        }
    
    # Include original response for completeness
    table_data["raw_data"] = response
    
    return table_data
