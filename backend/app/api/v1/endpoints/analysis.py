"""
FAR Analysis and Reporting API endpoints
Handles analysis operations and reporting for FAR requests and rules
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.models.far_rule import FarRule
from app.models.far_request import FarRequest
from app.services.asset_service import AssetService
from app.services.graph_service import GraphService
from app.services.tuple_generation_service import TupleGenerationService
from app.utils.error_handlers import success_response, paginated_response

router = APIRouter(prefix="/requests", tags=["FAR Analysis"])


@router.get("/{request_id}/rules")
def list_request_rules(
    request_id: int,
    skip: int = 0,
    limit: int = 100,
    include_facts: bool = False,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all rules for a specific FAR request with optional facts
    """
    # Verify request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    # Get rules for this request
    rules_query = db.query(FarRule).filter(FarRule.request_id == request_id)
    total_rules = rules_query.count()
    rules = rules_query.offset(skip).limit(limit).all()
    
    # Format rules data
    formatted_rules = []
    for rule in rules:
        rule_data = {
            "id": str(rule.id),
            "action": str(rule.action or ""),
            "direction": str(rule.direction or ""),
            "created_at": str(rule.created_at),
            "canonical_hash": rule.canonical_hash.hex() if rule.canonical_hash is not None else None,
            "endpoint_count": len(rule.endpoints),
            "service_count": len(rule.services),
            "request_id": request_id
        }
        
        if include_facts and rule.facts is not None:
            rule_data["facts"] = rule.facts
        
        formatted_rules.append(rule_data)
    
    return paginated_response(
        data=formatted_rules,
        skip=skip,
        limit=limit,
        total=total_rules,
        message=f"Retrieved {len(formatted_rules)} of {total_rules} rules for request {request_id}"
    )


@router.get("/{request_id}/summary")
def get_request_summary(
    request_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive summary statistics for a FAR request
    """
    # Verify request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    # Get all rules for this request
    rules = db.query(FarRule).filter(FarRule.request_id == request_id).all()
    
    if not rules:
        no_rules_data = {
            "request_id": request_id,
            "request_info": {
                "title": str(far_request.title or ""),
                "status": str(far_request.status or ""),
                "external_id": str(far_request.external_id or "")
            },
            "summary": {
                "total_rules": 0,
                "message": "No rules found for this request"
            }
        }
        return success_response(
            data=no_rules_data,
            message=f"No rules found for request {request_id}"
        )
    
    # Calculate statistics
    total_rules = len(rules)
    total_endpoints = sum(len(rule.endpoints) for rule in rules)
    total_services = sum(len(rule.services) for rule in rules)
    
    # Analyze endpoints by type
    sources_count = 0
    destinations_count = 0
    unique_sources = set()
    unique_destinations = set()
    
    for rule in rules:
        for endpoint in rule.endpoints:
            if endpoint.endpoint_type == 'source':
                sources_count += 1
                unique_sources.add(endpoint.network_cidr)
            elif endpoint.endpoint_type == 'destination':
                destinations_count += 1
                unique_destinations.add(endpoint.network_cidr)
    
    # Protocol analysis
    protocols = {}
    for rule in rules:
        for service in rule.services:
            protocol = service.protocol
            protocols[protocol] = protocols.get(protocol, 0) + 1
    
    # Calculate tuple estimates
    tuple_service = TupleGenerationService()
    total_tuples = 0
    
    for rule in rules:
        sources = [ep for ep in rule.endpoints if ep.endpoint_type == 'source']
        destinations = [ep for ep in rule.endpoints if ep.endpoint_type == 'destination']
        services = rule.services
        
        rule_tuples = tuple_service.calculate_tuple_estimate(
            len(sources), len(destinations), len(services)
        )
        total_tuples += rule_tuples
    
    # Facts analysis
    rules_with_facts = sum(1 for rule in rules if rule.facts is not None)
    
    summary_data = {
        "request_id": request_id,
        "request_info": {
            "title": str(far_request.title or ""),
            "status": str(far_request.status or ""),
            "external_id": str(far_request.external_id or ""),
            "created_at": str(far_request.created_at)
        },
        "summary": {
            "total_rules": total_rules,
            "total_endpoints": total_endpoints,
            "total_services": total_services,
            "estimated_total_tuples": total_tuples,
            "rules_with_facts": rules_with_facts,
            "facts_coverage": f"{(rules_with_facts/total_rules)*100:.1f}%" if total_rules > 0 else "0%"
        },
        "endpoint_analysis": {
            "total_sources": sources_count,
            "total_destinations": destinations_count,
            "unique_sources": len(unique_sources),
            "unique_destinations": len(unique_destinations),
            "source_reuse_ratio": f"{sources_count/len(unique_sources):.2f}" if unique_sources else "0",
            "destination_reuse_ratio": f"{destinations_count/len(unique_destinations):.2f}" if unique_destinations else "0"
        },
        "protocol_distribution": protocols,
        "complexity_analysis": {
            "avg_endpoints_per_rule": f"{total_endpoints/total_rules:.2f}" if total_rules > 0 else "0",
            "avg_services_per_rule": f"{total_services/total_rules:.2f}" if total_rules > 0 else "0",
            "avg_tuples_per_rule": f"{total_tuples/total_rules:.2f}" if total_rules > 0 else "0"
        }
    }
    
    return success_response(
        data=summary_data,
        message=f"Retrieved comprehensive summary for request {request_id}"
    )


@router.get("/{request_id}/network-topology")
def get_request_network_topology(
    request_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate network topology visualization data for all rules in a request
    """
    # Verify request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    # Get all rules for this request
    rules = db.query(FarRule).filter(FarRule.request_id == request_id).all()
    
    if not rules:
        no_rules_data = {
            "request_id": request_id,
            "error": "No rules found for this request"
        }
        return success_response(
            data=no_rules_data,
            message=f"No rules found for request {request_id}"
        )
    
    # Prepare rule data for graph service
    rule_data = []
    for rule in rules:
        sources = []
        destinations = []
        services = []
        
        for endpoint in rule.endpoints:
            endpoint_data = {"network_cidr": endpoint.network_cidr}
            if endpoint.endpoint_type == 'source':
                sources.append(endpoint_data)
            elif endpoint.endpoint_type == 'destination':
                destinations.append(endpoint_data)
        
        for service in rule.services:
            services.append({
                "protocol": service.protocol,
                "port_ranges": str(service.port_ranges)
            })
        
        rule_data.append({
            "rule_id": rule.id,
            "sources": sources,
            "destinations": destinations,
            "services": services
        })
    
    # Create graph service with asset integration
    asset_service = AssetService(db)
    graph_service = GraphService(asset_service)
    
    # Generate network topology
    topology = graph_service.create_network_topology_graph(rule_data)
    
    topology_data = {
        "request_id": request_id,
        "request_title": str(far_request.title or ""),
        "topology": topology,
        "summary": {
            "total_rules": len(rules),
            "network_nodes": topology["metadata"]["network_count"],
            "connections": topology["metadata"]["connection_count"]
        }
    }
    
    return success_response(
        data=topology_data,
        message=f"Generated network topology for request {request_id}"
    )


@router.get("/{request_id}/security-analysis")
def get_request_security_analysis(
    request_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform comprehensive security analysis for all rules in a request
    """
    # Verify request exists
    far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
    if not far_request:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    
    # Get all rules for this request
    rules = db.query(FarRule).filter(FarRule.request_id == request_id).all()
    
    if not rules:
        no_rules_data = {
            "request_id": request_id,
            "error": "No rules found for this request"
        }
        return success_response(
            data=no_rules_data,
            message=f"No rules found for request {request_id} security analysis"
        )
    
    # Analyze each rule
    rule_analyses = []
    total_issues = 0
    risk_distribution = {"low": 0, "medium": 0, "high": 0}
    
    for rule in rules:
        # Get rule data
        sources = []
        destinations = []
        services = []
        
        for endpoint in rule.endpoints:
            endpoint_data = {"network_cidr": endpoint.network_cidr}
            if endpoint.endpoint_type == 'source':
                sources.append(endpoint_data)
            elif endpoint.endpoint_type == 'destination':
                destinations.append(endpoint_data)
        
        for service in rule.services:
            services.append({
                "protocol": service.protocol,
                "port_ranges": str(service.port_ranges)
            })
        
        # Get facts
        facts_dict = rule.facts if rule.facts is not None and isinstance(rule.facts, dict) else {}
        
        # Perform analysis (reuse logic from rules endpoint)
        analysis = _analyze_rule_security(rule, facts_dict, sources, destinations, services)
        
        rule_analyses.append({
            "rule_id": rule.id,
            "analysis": analysis
        })
        
        total_issues += len(analysis["issues"])
        risk_distribution[analysis["risk_level"]] += 1
    
    # Calculate aggregate statistics
    avg_security_score = sum(r["analysis"]["security_score"] for r in rule_analyses) / len(rule_analyses)
    
    # Identify common issues
    issue_types = {}
    for rule_analysis in rule_analyses:
        for issue in rule_analysis["analysis"]["issues"]:
            issue_type = issue["type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = {"count": 0, "severity": issue["severity"]}
            issue_types[issue_type]["count"] += 1
    
    security_analysis_data = {
        "request_id": request_id,
        "request_title": str(far_request.title or ""),
        "overall_analysis": {
            "total_rules": len(rules),
            "average_security_score": f"{avg_security_score:.1f}/100",
            "total_issues": total_issues,
            "risk_distribution": risk_distribution,
            "rules_by_risk": {
                "high_risk": risk_distribution["high"],
                "medium_risk": risk_distribution["medium"],
                "low_risk": risk_distribution["low"]
            }
        },
        "common_issues": issue_types,
        "rule_details": rule_analyses,
        "recommendations": _generate_request_recommendations(issue_types, rule_analyses)
    }
    
    return success_response(
        data=security_analysis_data,
        message=f"Generated security analysis for request {request_id}"
    )


def _analyze_rule_security(rule: Any, facts: Dict, sources: List[Dict], destinations: List[Dict], services: List[Dict]) -> Dict[str, Any]:
    """Analyze security for a single rule (shared logic)"""
    analysis = {
        "security_score": 100,
        "risk_level": "low",
        "issues": [],
        "recommendations": []
    }
    
    # Analyze based on facts
    if facts:
        # Check for any-any rules
        if facts.get("src_is_any") or facts.get("dst_is_any"):
            analysis["issues"].append({
                "type": "overly_permissive",
                "severity": "high",
                "description": "Rule uses 0.0.0.0/0 (any) for source or destination"
            })
            analysis["security_score"] -= 30
        
        # Check for self-flow
        if facts.get("is_self_flow"):
            analysis["issues"].append({
                "type": "self_flow",
                "severity": "medium",
                "description": "Source and destination networks overlap"
            })
            analysis["security_score"] -= 10
        
        # Check for public IP exposure
        if facts.get("src_has_public") or facts.get("dst_has_public"):
            analysis["issues"].append({
                "type": "public_exposure",
                "severity": "medium",
                "description": "Rule involves public IP addresses"
            })
            analysis["security_score"] -= 15
    
    # Check tuple complexity
    tuple_count = len(sources) * len(destinations) * max(len(services), 1)
    if tuple_count > 100:
        analysis["issues"].append({
            "type": "high_complexity",
            "severity": "low",
            "description": f"Rule generates {tuple_count} network tuples"
        })
        analysis["security_score"] -= 5
    
    # Set risk level based on score
    analysis["security_score"] = max(0, analysis["security_score"])
    if analysis["security_score"] >= 80:
        analysis["risk_level"] = "low"
    elif analysis["security_score"] >= 60:
        analysis["risk_level"] = "medium"
    else:
        analysis["risk_level"] = "high"
    
    return analysis


def _generate_request_recommendations(issue_types: Dict, rule_analyses: List[Dict]) -> List[str]:
    """Generate recommendations based on common issues across all rules"""
    recommendations = []
    
    # Check for common patterns
    if "overly_permissive" in issue_types and issue_types["overly_permissive"]["count"] > 1:
        recommendations.append(
            f"Multiple rules ({issue_types['overly_permissive']['count']}) use 0.0.0.0/0 - "
            "consider implementing more specific network ranges"
        )
    
    if "public_exposure" in issue_types:
        recommendations.append(
            "Rules involve public IP addresses - ensure DMZ segmentation and proper monitoring"
        )
    
    if "high_complexity" in issue_types:
        recommendations.append(
            "Some rules generate many network tuples - consider rule optimization for performance"
        )
    
    # General recommendations
    high_risk_rules = sum(1 for r in rule_analyses if r["analysis"]["risk_level"] == "high")
    if high_risk_rules > 0:
        recommendations.append(f"Review {high_risk_rules} high-risk rules immediately")
    
    return recommendations
