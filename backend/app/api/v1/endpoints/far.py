"""
FAR (Federated Access Request) API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import aiofiles
import os
from app.core.database import get_db
from app.models.far_request import FarRequest
from app.schemas.far_request import FarRequestCreate, FarRequestResponse
from app.services.far_service import FarIngestionService
from app.services.csv_ingestion_service import CsvIngestionService

router = APIRouter()


@router.post("/requests", response_model=FarRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_far_request(
    title: str,
    file: UploadFile = File(...),
    external_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Create a new FAR request with file upload
    """
    service = FarIngestionService(db)
    
    try:
        result = await service.process_upload(
            title=title,
            file=file,
            external_id=external_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/requests", response_model=List[FarRequestResponse])
def list_far_requests(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all FAR requests
    """
    requests = db.query(FarRequest).offset(skip).limit(limit).all()
    return requests


@router.get("/requests/{request_id}", response_model=FarRequestResponse)
def get_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific FAR request by ID
    """
    request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    return request


@router.post("/requests/{request_id}/ingest", status_code=status.HTTP_200_OK)
async def ingest_far_csv(
    request_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Phase 2.2: Ingest and normalize CSV data for a FAR request
    
    This endpoint processes the uploaded CSV file, normalizes IP addresses and port ranges,
    and creates FAR rules with endpoint and service normalization.
    """
    # Verify the request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    
    if far_request.status not in ['submitted', 'processing']:
        raise HTTPException(
            status_code=400, 
            detail=f"Request is in '{far_request.status}' status and cannot be ingested"
        )
    
    try:
        # Update status to processing
        far_request.status = 'processing'
        db.commit()
        
        # Read the uploaded CSV file
        full_path = os.path.join("uploads", far_request.storage_path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Uploaded file not found")
        
        async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
            file_content = await f.read()
        
        # Process the CSV with the ingestion service
        ingestion_service = CsvIngestionService(db)
        statistics = await ingestion_service.ingest_csv_file(request_id, file_content)
        
        return {
            "message": "CSV ingestion completed",
            "request_id": request_id,
            "statistics": statistics
        }
        
    except Exception as e:
        # Reset status on error
        far_request.status = 'submitted'
        db.commit()
        raise HTTPException(status_code=400, detail=f"CSV ingestion failed: {str(e)}")


@router.get("/requests/{request_id}/rules")
def get_far_rules(
    request_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get normalized FAR rules for a request
    """
    # Verify the request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail="FAR request not found")
    
    # Get rules with their relationships
    from app.models.far_rule import FarRule
    rules = db.query(FarRule).filter(
        FarRule.request_id == request_id
    ).offset(skip).limit(limit).all()
    
    # Format rules with their endpoints and services
    formatted_rules = []
    for rule in rules:
        rule_data = {
            "id": rule.id,
            "action": rule.action,
            "direction": rule.direction,
            "created_at": rule.created_at.isoformat(),
            "endpoints": {
                "sources": [
                    {"network_cidr": ep.network_cidr} 
                    for ep in rule.endpoints if ep.endpoint_type == 'source'
                ],
                "destinations": [
                    {"network_cidr": ep.network_cidr} 
                    for ep in rule.endpoints if ep.endpoint_type == 'destination'
                ]
            },
            "services": [
                {
                    "protocol": svc.protocol,
                    "port_ranges": str(svc.port_ranges)  # PostgreSQL multirange format
                }
                for svc in rule.services
            ]
        }
        formatted_rules.append(rule_data)
    
    # Get total count
    total_rules = db.query(FarRule).filter(FarRule.request_id == request_id).count()
    
    return {
        "request_id": request_id,
        "total_rules": total_rules,
        "rules": formatted_rules,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "returned": len(formatted_rules)
        }
    }


@router.get("/rules/{rule_id}")
def get_far_rule_details(
    rule_id: int,
    format: Optional[str] = None,
    include: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
    from app.models.far_rule import FarRule
    
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
    
    # Calculate tuple estimate
    tuple_estimate = len(sources) * len(destinations) * max(len(services), 1) if sources and destinations else 0
    
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
        response['graph'] = _get_rule_graph_data(rule_id, sources, destinations, services)
    
    if 'tuples' in includes:
        response['tuples'] = _get_rule_tuples(sources, destinations, services)
    
    if 'analysis' in includes:
        response['analysis'] = _get_rule_analysis(rule, facts_dict, sources, destinations, services)
    
    # Format response based on format parameter
    if format == 'table':
        return _format_rule_as_table(response)
    
    return response


def _get_rule_assets(rule_id: int, sources: List[Dict], destinations: List[Dict], db: Session) -> Dict[str, Any]:
    """Get asset registry information for rule endpoints"""
    from app.models.asset_registry import AssetRegistry
    
    asset_matches = {
        "sources": [],
        "destinations": [],
        "total_matches": 0
    }
    
    # Check source assets
    for source in sources:
        cidr = source["network_cidr"]
        ip = cidr.split('/')[0]  # Extract IP from CIDR
        
        # Query asset registry for matching IPs
        assets = db.query(AssetRegistry).filter(
            AssetRegistry.ip_address == ip
        ).all()
        
        for asset in assets:
            asset_info = {
                "ip_address": asset.ip_address,
                "hostname": asset.hostname,
                "environment": asset.environment,
                "os_name": asset.os_name,
                "location": asset.location,
                "segment": asset.segment,
                "vlan": asset.vlan,
                "availability": asset.availability
            }
            asset_matches["sources"].append(asset_info)
    
    # Check destination assets
    for dest in destinations:
        cidr = dest["network_cidr"]
        ip = cidr.split('/')[0]  # Extract IP from CIDR
        
        # Query asset registry for matching IPs
        assets = db.query(AssetRegistry).filter(
            AssetRegistry.ip_address == ip
        ).all()
        
        for asset in assets:
            asset_info = {
                "ip_address": asset.ip_address,
                "hostname": asset.hostname,
                "environment": asset.environment,
                "os_name": asset.os_name,
                "location": asset.location,
                "segment": asset.segment,
                "vlan": asset.vlan,
                "availability": asset.availability
            }
            asset_matches["destinations"].append(asset_info)
    
    asset_matches["total_matches"] = len(asset_matches["sources"]) + len(asset_matches["destinations"])
    
    return asset_matches


def _get_rule_graph_data(rule_id: int, sources: List[Dict], destinations: List[Dict], services: List[Dict]) -> Dict[str, Any]:
    """Generate D3-compatible graph data for visualization with asset details"""
    nodes = []
    links = []
    
    # Add rule node (center)
    nodes.append({
        "id": f"rule_{rule_id}",
        "label": f"Rule {rule_id}",
        "type": "rule",
        "group": 1,
        "size": 20
    })
    
    # Add source nodes with asset details
    for i, source in enumerate(sources):
        node_id = f"src_{i}"
        cidr = source["network_cidr"]
        ip = cidr.split('/')[0]
        
        # Get asset details for this IP
        asset_info = _get_asset_by_ip(ip)
        
        # Create enhanced node with asset details
        node = {
            "id": node_id,
            "label": asset_info.get("hostname", cidr) if asset_info and asset_info.get("hostname") else cidr,
            "type": "source",
            "group": 2,
            "size": 15,
            "cidr": cidr,
            "ip_address": ip,
            "tooltip": _create_node_tooltip(cidr, asset_info, "Source")
        }
        
        # Add asset metadata if available
        if asset_info:
            node.update({
                "hostname": asset_info.get("hostname"),
                "environment": asset_info.get("environment"),
                "os_name": asset_info.get("os_name"),
                "location": asset_info.get("location"),
                "segment": asset_info.get("segment"),
                "vlan": asset_info.get("vlan"),
                "availability": asset_info.get("availability"),
                "has_asset_data": True
            })
        else:
            node["has_asset_data"] = False
        
        nodes.append(node)
        
        # Link source to rule
        links.append({
            "source": node_id,
            "target": f"rule_{rule_id}",
            "type": "source_to_rule",
            "value": 2,
            "label": "allows from"
        })
    
    # Add destination nodes with asset details
    for i, dest in enumerate(destinations):
        node_id = f"dst_{i}"
        cidr = dest["network_cidr"]
        ip = cidr.split('/')[0]
        
        # Get asset details for this IP
        asset_info = _get_asset_by_ip(ip)
        
        # Create enhanced node with asset details
        node = {
            "id": node_id,
            "label": asset_info.get("hostname", cidr) if asset_info and asset_info.get("hostname") else cidr,
            "type": "destination",
            "group": 3,
            "size": 15,
            "cidr": cidr,
            "ip_address": ip,
            "tooltip": _create_node_tooltip(cidr, asset_info, "Destination")
        }
        
        # Add asset metadata if available
        if asset_info:
            node.update({
                "hostname": asset_info.get("hostname"),
                "environment": asset_info.get("environment"),
                "os_name": asset_info.get("os_name"),
                "location": asset_info.get("location"),
                "segment": asset_info.get("segment"),
                "vlan": asset_info.get("vlan"),
                "availability": asset_info.get("availability"),
                "has_asset_data": True
            })
        else:
            node["has_asset_data"] = False
        
        nodes.append(node)
        
        # Link rule to destination
        links.append({
            "source": f"rule_{rule_id}",
            "target": node_id,
            "type": "rule_to_destination",
            "value": 2,
            "label": "allows to"
        })
    
    # Add service information to rule node
    service_info = []
    service_labels = []
    for service in services:
        port_range = service["port_ranges"].strip('{}').strip('[]')
        service_str = f"{service['protocol']}:{port_range}"
        service_info.append(service_str)
        
        # Create human-readable service labels
        service_type = _classify_service(service["protocol"], service["port_ranges"])
        service_labels.append(f"{service['protocol'].upper()}/{port_range} ({service_type})")
    
    # Update rule node with service information
    for node in nodes:
        if node["id"] == f"rule_{rule_id}":
            node.update({
                "services": service_info,
                "service_labels": service_labels,
                "tooltip": f"Rule {rule_id}\\nServices: {', '.join(service_labels)}"
            })
            break
    
    return {
        "nodes": nodes,
        "links": links,
        "metadata": {
            "rule_id": rule_id,
            "source_count": len(sources),
            "destination_count": len(destinations),
            "service_count": len(services),
            "total_assets_found": sum(1 for node in nodes if node.get("has_asset_data", False))
        },
        "legend": {
            "node_types": [
                {"type": "rule", "group": 1, "color": "#ff6b6b", "description": "Firewall Rule"},
                {"type": "source", "group": 2, "color": "#4ecdc4", "description": "Source Endpoints"},
                {"type": "destination", "group": 3, "color": "#45b7d1", "description": "Destination Endpoints"}
            ],
            "link_types": [
                {"type": "source_to_rule", "description": "Traffic flows from source"},
                {"type": "rule_to_destination", "description": "Traffic flows to destination"}
            ]
        }
    }


def _get_rule_tuples(sources: List[Dict], destinations: List[Dict], services: List[Dict]) -> Dict[str, Any]:
    """Generate actual network tuples for this rule"""
    tuples = []
    
    for source in sources:
        for dest in destinations:
            for service in services:
                # Parse port ranges (basic parsing for PostgreSQL format)
                port_range = service["port_ranges"].strip('{}').strip('[]')
                if ',' in port_range:
                    start_port, end_port = port_range.split(',')
                    port_display = f"{start_port}-{end_port}" if start_port != end_port else start_port
                else:
                    port_display = port_range
                
                tuple_data = {
                    "source": source["network_cidr"],
                    "destination": dest["network_cidr"],
                    "protocol": service["protocol"],
                    "ports": port_display,
                    "tuple_id": f"{source['network_cidr']}→{dest['network_cidr']}:{service['protocol']}/{port_display}"
                }
                tuples.append(tuple_data)
    
    return {
        "tuples": tuples,
        "total_count": len(tuples),
        "summary": {
            "unique_sources": len(sources),
            "unique_destinations": len(destinations),
            "unique_services": len(services)
        }
    }


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
        if facts.get("expansion_capped"):
            analysis["issues"].append({
                "type": "high_complexity",
                "severity": "low",
                "description": "Rule generates many network tuples",
                "impact": "May impact firewall performance"
            })
            analysis["security_score"] -= 5
            analysis["recommendations"].append("Consider breaking down into more specific rules")
    
    # Service analysis
    for service in services:
        protocol = service["protocol"]
        port_range = service["port_ranges"]
        
        # Check for common risky ports
        if "22" in port_range:  # SSH
            analysis["recommendations"].append("SSH access detected - ensure key-based authentication")
        if "3389" in port_range:  # RDP
            analysis["recommendations"].append("RDP access detected - consider VPN or bastion host")
        if "443" in port_range or "80" in port_range:  # HTTP/HTTPS
            analysis["recommendations"].append("Web traffic detected - ensure proper SSL/TLS configuration")
    
    # Calculate final security score (baseline 100, subtract for issues)
    analysis["security_score"] = max(0, 100 + analysis["security_score"])
    
    # Determine final risk level based on score
    if analysis["security_score"] >= 80:
        analysis["risk_level"] = "low"
    elif analysis["security_score"] >= 60:
        analysis["risk_level"] = "medium"
    else:
        analysis["risk_level"] = "high"
    
    # Compliance checks
    if not facts or not (facts.get("src_is_any") or facts.get("dst_is_any")):
        analysis["compliance"]["zero_trust"] = True
    
    return analysis


def _format_rule_as_table(response: Dict[str, Any]) -> Dict[str, Any]:
    """Format rule data as human-readable table structure"""
    rule_id = response["rule_id"]
    request = response["request"]
    details = response["rule_details"]
    endpoints = response["endpoints"]
    services = response["services"]
    facts = response.get("facts", {})
    
    # Create table-formatted response
    table_format = {
        "rule_summary": {
            "Rule ID": rule_id,
            "Action": details["action"],
            "Direction": details["direction"] or "bidirectional",
            "Created": details["created_at"],
            "Request": f"{request['title']} (ID: {request['id']})",
            "External ID": request.get("external_id", "N/A")
        },
        "network_endpoints": {
            "Sources": [src["network_cidr"] for src in endpoints["sources"]],
            "Destinations": [dst["network_cidr"] for dst in endpoints["destinations"]],
            "Source Count": endpoints["source_count"],
            "Destination Count": endpoints["destination_count"]
        },
        "services_table": [
            {
                "Protocol": svc["protocol"].upper(),
                "Port Range": svc["port_ranges"].strip('{}').replace('[', '').replace(']', ''),
                "Service Type": _classify_service(svc["protocol"], svc["port_ranges"])
            }
            for svc in services
        ],
        "security_facts": {
            "Is Any-Any Rule": facts.get("src_is_any", False) or facts.get("dst_is_any", False),
            "Has Self-Flow": facts.get("is_self_flow", False),
            "Public IP Involved": facts.get("src_has_public", False) or facts.get("dst_has_public", False),
            "Tuple Estimate": facts.get("tuple_estimate", response.get("tuple_estimate", 0)),
            "Risk Indicators": _get_risk_indicators(facts)
        },
        "human_readable_summary": _generate_human_summary(response)
    }
    
    return {
        "format": "table",
        "rule_id": rule_id,
        "data": table_format
    }


def _classify_service(protocol: str, port_ranges: str) -> str:
    """Classify service type based on protocol and port"""
    port_str = port_ranges.strip('{}').strip('[]')
    
    common_ports = {
        "80": "HTTP Web",
        "443": "HTTPS Web", 
        "22": "SSH Remote Access",
        "3389": "RDP Remote Desktop",
        "53": "DNS",
        "25": "SMTP Email",
        "143": "IMAP Email",
        "993": "IMAPS Email",
        "21": "FTP",
        "23": "Telnet",
        "3306": "MySQL Database",
        "5432": "PostgreSQL Database",
        "1433": "SQL Server Database",
        "6443": "Kubernetes API",
        "8080": "HTTP Alternate",
        "8443": "HTTPS Alternate"
    }
    
    if port_str in common_ports:
        return common_ports[port_str]
    
    # Check ranges
    if "1024" in port_str and "65535" in port_str:
        return "High Ports (Ephemeral)"
    elif int(port_str.split(',')[0] if ',' in port_str else port_str) < 1024:
        return "System/Well-Known Port"
    else:
        return "User/Application Port"


def _get_risk_indicators(facts: Dict) -> List[str]:
    """Extract risk indicators from facts"""
    indicators = []
    
    if facts.get("src_is_any") or facts.get("dst_is_any"):
        indicators.append("🔴 Any-to-Any Access")
    
    if facts.get("is_self_flow"):
        indicators.append("🟡 Self-Flow Detected")
    
    if facts.get("src_has_public") or facts.get("dst_has_public"):
        indicators.append("🟠 Public IP Exposure")
    
    if facts.get("expansion_capped"):
        indicators.append("🟡 High Tuple Count")
    
    if not indicators:
        indicators.append("🟢 No Major Issues Detected")
    
    return indicators


def _generate_human_summary(response: Dict[str, Any]) -> str:
    """Generate human-readable summary of the rule"""
    rule_id = response["rule_id"]
    action = response["rule_details"]["action"]
    sources = response["endpoints"]["sources"]
    destinations = response["endpoints"]["destinations"]
    services = response["services"]
    
    src_count = len(sources)
    dst_count = len(destinations)
    svc_count = len(services)
    
    # Build summary
    summary = f"Rule {rule_id} {action}s traffic from {src_count} source"
    if src_count != 1:
        summary += "s"
    
    summary += f" to {dst_count} destination"
    if dst_count != 1:
        summary += "s"
    
    if svc_count > 0:
        protocols = list(set(svc["protocol"] for svc in services))
        summary += f" using {'/'.join(protocols).upper()} protocol"
        if len(protocols) > 1:
            summary += "s"
        
        summary += f" on {svc_count} service"
        if svc_count > 1:
            summary += "s"
    
    # Add tuple estimate
    tuple_est = response.get("tuple_estimate", 0)
    summary += f". This creates approximately {tuple_est} network tuples."
    
    return summary


def _get_asset_by_ip(ip_address: str) -> Dict[str, Any] | None:
    """Get asset information for a specific IP address"""
    from app.core.database import SessionLocal
    from app.models.asset_registry import AssetRegistry
    
    # Create a new database session for this lookup
    db = SessionLocal()
    try:
        asset = db.query(AssetRegistry).filter(
            AssetRegistry.ip_address == ip_address
        ).first()
        
        if asset:
            return {
                "ip_address": asset.ip_address,
                "hostname": asset.hostname,
                "environment": asset.environment,
                "os_name": asset.os_name,
                "location": asset.location,
                "segment": asset.segment,
                "vlan": asset.vlan,
                "availability": asset.availability
            }
        return None
    finally:
        db.close()


def _create_node_tooltip(cidr: str, asset_info: Dict[str, Any] | None, node_type: str) -> str:
    """Create a tooltip string for a graph node"""
    tooltip_lines = [f"{node_type}: {cidr}"]
    
    if asset_info:
        if asset_info.get("hostname"):
            tooltip_lines.append(f"Hostname: {asset_info['hostname']}")
        if asset_info.get("environment"):
            tooltip_lines.append(f"Environment: {asset_info['environment']}")
        if asset_info.get("os_name"):
            tooltip_lines.append(f"OS: {asset_info['os_name']}")
        if asset_info.get("location"):
            tooltip_lines.append(f"Location: {asset_info['location']}")
        if asset_info.get("segment"):
            tooltip_lines.append(f"Segment: {asset_info['segment']}")
        if asset_info.get("vlan"):
            tooltip_lines.append(f"VLAN: {asset_info['vlan']}")
        if asset_info.get("availability"):
            tooltip_lines.append(f"Availability: {asset_info['availability']}")
    else:
        tooltip_lines.append("No asset data available")
    
    return "\\n".join(tooltip_lines)
