"""
FAR Analysis and Reporting API endpoints
Handles analysis operations and reporting for FAR requests and rules
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.core.project_auth import get_far_request_in_project_or_404
from app.models.far_rule import FarRule
from app.models.far_request import FarRequest
from app.services.asset_service import AssetService
from app.services.graph_service import GraphService
from app.services.tuple_generation_service import TupleGenerationService
from app.services.risky_port_policy_service import apply_risky_port_policy_to_analysis, list_enabled_entries
from app.utils.error_handlers import success_response, paginated_response
from app.utils.csv_errors import DatabaseConnectionError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["FAR Analysis"])


@router.get("/{request_id}/summary")
def get_request_summary(
    project_id: int,
    request_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive summary statistics for a FAR request
    """
    try:
        far_request = get_far_request_in_project_or_404(db, request_id, project_id)

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
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting request summary for {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving request summary",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error getting request summary for {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve request summary: {str(e)}")


@router.get("/{request_id}/network-topology")
def get_request_network_topology(
    project_id: int,
    request_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Generate network topology for all rules in a request.

    Returns `topology` and `unified_graph` (same payload): unique CIDR nodes, merged directed edges,
    per-edge rule_ids and services, and node fields enriched from the asset registry where matched.
    """
    try:
        far_request = get_far_request_in_project_or_404(db, request_id, project_id)

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
                "rule_name": f"Rule {rule.id}",
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
            "unified_graph": topology,
            "summary": {
                "total_rules": len(rules),
                "network_nodes": topology["metadata"]["network_count"],
                "connections": topology["metadata"].get(
                    "connection_count", topology["metadata"].get("link_count", 0)
                ),
            },
        }
        
        return success_response(
            data=topology_data,
            message=f"Generated network topology for request {request_id}"
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting network topology for {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when generating network topology",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error generating network topology for {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate network topology: {str(e)}")


@router.get("/{request_id}/security-analysis")
def get_request_security_analysis(
    project_id: int,
    request_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Perform comprehensive security analysis for all rules in a request
    """
    try:
        far_request = get_far_request_in_project_or_404(db, request_id, project_id)

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
            analysis = _analyze_rule_security(
                rule, facts_dict, sources, destinations, services, db
            )
            
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
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting security analysis for {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when generating security analysis",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error generating security analysis for {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate security analysis: {str(e)}")


def _analyze_rule_security(
    rule: Any,
    facts: Dict,
    sources: List[Dict],
    destinations: List[Dict],
    services: List[Dict],
    db: Session,
) -> Dict[str, Any]:
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
    
    try:
        policy_entries = list_enabled_entries(db)
        apply_risky_port_policy_to_analysis(
            analysis, services, policy_entries, rich_issues=False
        )
    except Exception as e:
        logger.warning("Risky port policy skipped: %s", e, exc_info=True)

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

    if "risky_port" in issue_types:
        recommendations.append(
            "One or more rules match the global risky port policy. Review exposed services against "
            "industry-standard practice: disable unnecessary listeners, restrict to trusted networks, "
            "and apply vendor and framework hardening guidance (for example CIS and NIST baselines)."
        )
    
    # General recommendations
    high_risk_rules = sum(1 for r in rule_analyses if r["analysis"]["risk_level"] == "high")
    if high_risk_rules > 0:
        recommendations.append(f"Review {high_risk_rules} high-risk rules immediately")
    
    return recommendations
