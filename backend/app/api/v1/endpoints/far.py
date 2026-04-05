"""
FAR (Federated Access Request) API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from typing import List, Dict, Any, Optional, cast
import aiofiles
import os
import ipaddress
from datetime import datetime
from app.core.database import get_db
from app.models.far_request import FarRequest
from app.schemas.far_request import FarRequestCreate, FarRequestResponse
from app.schemas.responses import (
    FarIpsResponse, FarIpSummaryModel, IpDetailsModel, StandardResponse, StatusEnum,
    FarRulesResponse, FarRulesSummaryModel, RuleDetailModel
)
from app.services.far_service import FarIngestionService
from app.services.csv_ingestion_service import CsvIngestionService
from app.services.csv_validation_service import CSVValidationService
from app.services.asset_service import AssetService
from app.services.graph_service import GraphService
from app.services.tuple_generation_service import TupleGenerationService
from app.utils.csv_errors import (
    CSVFileError, CSVEncodingError, CSVValidationError, CSVColumnError,
    DatabaseConnectionError, FileSystemError, InsufficientStorageError
)
import logging

logger = logging.getLogger(__name__)

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
    Enhanced with better error handling
    """
    service = FarIngestionService(db)
    
    try:
        result = await service.process_upload(
            title=title,
            file=file,
            external_id=external_id
        )
        return result
    except (HTTPException, DatabaseConnectionError, FileSystemError, InsufficientStorageError):
        # Re-raise known exceptions as-is (they're already properly formatted)
        raise
    except Exception as e:
        logger.error(f"Error creating FAR request: {str(e)}", exc_info=True)
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
    try:
        requests = db.query(FarRequest).offset(skip).limit(limit).all()
        return requests
    except OperationalError as e:
        logger.error(f"Database connection error listing FAR requests: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving FAR requests",
            details={"error": str(e), "skip": skip, "limit": limit}
        )
    except Exception as e:
        logger.error(f"Error listing FAR requests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve FAR requests: {str(e)}")


@router.get("/requests/{request_id}", response_model=FarRequestResponse)
def get_far_request(
    request_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific FAR request by ID
    """
    try:
        request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="FAR request not found")
        return request
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting FAR request {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving FAR request",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error getting FAR request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve FAR request: {str(e)}")


@router.post("/requests/{request_id}/ingest", status_code=status.HTTP_200_OK)
async def ingest_far_csv(
    request_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Phase 2.2: Ingest and normalize CSV data for a FAR request
    
    This endpoint processes the uploaded CSV file, normalizes IP addresses and port ranges,
    and creates FAR rules with endpoint and service normalization.
    Enhanced with comprehensive error handling.
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
        far_request.status = 'processing'  # type: ignore[assignment]
        db.commit()
        
        # Read the uploaded CSV file
        storage_path_str = cast(str, far_request.storage_path)
        full_path = os.path.join("uploads", storage_path_str)
        if not os.path.exists(full_path):
            far_request.status = 'error'  # type: ignore[assignment]
            db.commit()
            raise HTTPException(status_code=404, detail="Uploaded file not found")
        
        # Read file as bytes for encoding detection
        async with aiofiles.open(full_path, 'rb') as f:
            file_content_bytes = await f.read()
        
        # Validate and decode
        try:
            file_content, metadata = CSVValidationService.validate_file_structure(
                file_content_bytes,
                filename=far_request.source_filename
            )
        except CSVFileError as e:
            far_request.status = 'error'  # type: ignore[assignment]
            db.commit()
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message
            )
        except CSVEncodingError as e:
            far_request.status = 'error'  # type: ignore[assignment]
            db.commit()
            raise HTTPException(
                status_code=e.status_code,
                detail=e.message
            )
        
        # Process the CSV with the ingestion service
        ingestion_service = CsvIngestionService(db)
        
        try:
            statistics = await ingestion_service.ingest_csv_file(request_id, file_content)
        except CSVValidationError as e:
            far_request.status = 'error'  # type: ignore[assignment]
            db.commit()
            raise HTTPException(
                status_code=400,
                detail={
                    "message": e.message,
                    "details": e.details
                }
            )
        except CSVColumnError as e:
            far_request.status = 'error'  # type: ignore[assignment]
            db.commit()
            raise HTTPException(
                status_code=400,
                detail={
                    "message": e.message,
                    "missing_columns": e.details.get('missing_columns'),
                    "found_columns": e.details.get('found_columns')
                }
            )
        
        return {
            "message": "CSV ingestion completed",
            "request_id": request_id,
            "statistics": statistics,
            "status": far_request.status
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Reset status on error
        far_request.status = 'error'  # type: ignore[assignment]
        db.commit()
        logger.error(f"Unexpected error ingesting CSV for request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CSV ingestion failed: {str(e)}")


@router.get("/requests/{request_id}/rules", response_model=StandardResponse[FarRulesResponse])
def get_far_rules(
    request_id: int,
    skip: int = 0,
    limit: int = 100,
    include_summary: bool = True,
    db: Session = Depends(get_db)
) -> StandardResponse[FarRulesResponse]:
    logger.info(f"DEBUG: get_far_rules called with request_id={request_id}")
    # Verify the request exists 
    """
    Get enhanced, human-readable FAR rules for a request
    
    Returns comprehensive rule information instead of just hashes:
    - Complete source/destination networks
    - Service details (protocols, ports)
    - Human-readable rule summaries
    - Rule statistics and analysis
    
    Query Parameters:
    - skip: Number of rules to skip (pagination)
    - limit: Maximum rules to return (pagination)
    - include_summary: Include summary statistics
    """
    try:
        # Verify the request exists
        far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
        if not far_request:
            raise HTTPException(status_code=404, detail="FAR request not found")
        
        # Import models here to avoid circular imports
        from app.models.far_rule import FarRule
        
        # Get rules with their relationships
        rules_query = db.query(FarRule).filter(FarRule.request_id == request_id)
        total_rules = rules_query.count()
        
        rules = rules_query.offset(skip).limit(limit).all()
        
        # Process rules to extract human-readable information
        enhanced_rules = []
        all_sources = set()
        all_destinations = set()
        all_protocols = set()
        allow_rules = 0
        deny_rules = 0
        total_tuple_estimate = 0
        
        for rule in rules:
            logger.info(f"DEBUG: Processing rule {rule.id}")
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
            
            # Compute assessment data from facts
            # Compute assessment data from facts
            logger.info(f"DEBUG: About to compute assessment for rule {rule.id}, facts type: {type(rule.facts)}")
            # Ensure facts is a dict (SQLAlchemy ORM should return the value, but verify)
            facts_raw = rule.facts
            logger.info(f"DEBUG: Facts raw type: {type(facts_raw)}")
            if facts_raw is not None and isinstance(facts_raw, dict):
                facts: Optional[Dict[str, Any]] = cast(Dict[str, Any], facts_raw)
            else:
                facts = None
            assessment = _compute_rule_assessment(facts)
            
            # Temporary print to verify code execution (remove after debugging)
            logger.info(f"DEBUG: Rule {rule.id} - assessment computed: {assessment}")
            
            # Info logging to verify assessment computation
            logger.info(
                f"Rule {rule.id} assessment: health_status={assessment['health_status']}, "
                f"problem_count={assessment['problem_count']}, "
                f"criticality_score={assessment['criticality_score']}, "
                f"facts_present={facts is not None}"
            )
            if facts:
                logger.info(f"Rule {rule.id} facts keys: {list(facts.keys()) if isinstance(facts, dict) else 'not a dict'}")
                logger.info(f"Rule {rule.id} is_self_flow={facts.get('is_self_flow')}, src_is_any={facts.get('src_is_any')}, dst_is_any={facts.get('dst_is_any')}")
            
            # Create enhanced rule model
            enhanced_rule = RuleDetailModel(
                id=cast(int, rule.id),
                action=cast(str, rule.action),
                direction=cast(Optional[str], rule.direction),
                source_networks=source_networks,
                source_count=len(source_networks),
                destination_networks=destination_networks,
                destination_count=len(destination_networks),
                protocols=protocols,
                port_ranges=port_ranges,
                service_count=len(rule.services),
                created_at=rule.created_at.isoformat(),
                rule_hash=rule.canonical_hash.hex() if rule.canonical_hash is not None else None,
                tuple_estimate=tuple_estimate,
                rule_summary=rule_summary,
                health_status=assessment["health_status"],
                problem_count=assessment["problem_count"],
                criticality_score=assessment["criticality_score"]
            )
            enhanced_rules.append(enhanced_rule)
        
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
        
        # Create response data
        response_data = FarRulesResponse(
            far_request_id=request_id,
            summary=summary,
            rules=enhanced_rules,
            pagination=pagination,
            metadata={
                "request_title": far_request.title,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "processing_notes": "Enhanced human-readable rule format"
            }
        )
        
        return StandardResponse(
            status=StatusEnum.SUCCESS,
            message=f"Retrieved {len(enhanced_rules)} enhanced rules for FAR request {request_id}",
            data=response_data,
            errors=None,
            metadata={
                "api_version": "2.0",
                "enhancement": "human_readable_rules"
            },
            request_id=None
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting rules for FAR request {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving rules for FAR request",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error getting rules for FAR request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rules: {str(e)}")


@router.get("/requests/{request_id}/ips", response_model=StandardResponse[FarIpsResponse])
def get_far_request_ips(
    request_id: int,
    include_assets: bool = False,
    db: Session = Depends(get_db)
) -> StandardResponse[FarIpsResponse]:
    """
    Get all IP addresses involved in a specific FAR request
    
    Returns comprehensive IP analysis including:
    - All source and destination IPs
    - Asset registry information (if available)
    - Network associations
    - Rule counts per IP
    
    Query Parameters:
    - include_assets: Include asset registry information for each IP
    """
    try:
        # Verify the request exists
        far_request = db.query(FarRequest).filter(FarRequest.id == request_id).first()
        if not far_request:
            raise HTTPException(status_code=404, detail="FAR request not found")
        
        # Import models here to avoid circular imports
        from app.models.far_rule import FarRule, FarRuleEndpoint
        from app.models.asset_registry import AssetRegistry
        
        # Get all endpoints for this request through the rules
        query = db.query(FarRuleEndpoint, FarRule).join(
            FarRule, FarRuleEndpoint.rule_id == FarRule.id
        ).filter(FarRule.request_id == request_id)
        
        endpoints = query.all()
        
        # Collect and analyze IPs
        ip_data = {}
        source_ips = set()
        destination_ips = set()
        
        for endpoint, rule in endpoints:
            # Extract IPs from CIDR notation
            network_cidr = endpoint.network_cidr
            ips_in_network = _extract_ips_from_cidr(network_cidr)
            
            for ip in ips_in_network:
                if ip not in ip_data:
                    ip_data[ip] = {
                        "ip_address": ip,
                        "networks": set(),
                        "rule_count": 0,
                        "is_source": False,
                        "is_destination": False,
                        "asset_info": None
                    }
                
                # Track networks this IP belongs to
                ip_data[ip]["networks"].add(network_cidr)
                ip_data[ip]["rule_count"] += 1
                
                # Track IP type based on endpoint type
                if endpoint.endpoint_type == 'source':
                    ip_data[ip]["is_source"] = True
                    source_ips.add(ip)
                elif endpoint.endpoint_type == 'destination':
                    ip_data[ip]["is_destination"] = True
                    destination_ips.add(ip)
        
        # Get asset information if requested
        if include_assets:
            for ip in ip_data.keys():
                asset = db.query(AssetRegistry).filter(AssetRegistry.ip_address == ip).first()
                if asset:
                    ip_data[ip]["asset_info"] = {
                        "hostname": asset.hostname,
                        "asset_type": asset.asset_type,
                        "criticality": asset.criticality,
                        "environment": asset.environment,
                        "department": asset.department,
                        "is_active": asset.is_active,
                        "last_updated": asset.updated_at.isoformat() if asset.updated_at is not None else None
                    }
        
        # Convert sets to lists for JSON serialization
        for ip in ip_data.values():
            ip["networks"] = list(ip["networks"])
        
        # Determine IP type for each IP
        ip_details = []
        for ip_info in ip_data.values():
            ip_type = "both" if (ip_info["is_source"] and ip_info["is_destination"]) else \
                     "source" if ip_info["is_source"] else "destination"
            
            ip_details.append(IpDetailsModel(
                ip_address=ip_info["ip_address"],
                ip_type=ip_type,
                rule_count=ip_info["rule_count"],
                asset_info=ip_info["asset_info"],
                networks=ip_info["networks"]
            ))
        
        # Create summary
        overlapping_ips = len(source_ips.intersection(destination_ips))
        
        summary = FarIpSummaryModel(
            request_id=request_id,
            total_ips=len(ip_data),
            source_ips=len(source_ips),
            destination_ips=len(destination_ips),
            overlapping_ips=overlapping_ips
        )
        
        # Create response data
        response_data = FarIpsResponse(
            summary=summary,
            ips=ip_details,
            metadata={
                "request_title": far_request.title,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "include_assets": include_assets,
                "total_rules": len(set(rule.id for _, rule in endpoints))
            }
        )
        
        return StandardResponse(
            status=StatusEnum.SUCCESS,
            message=f"Retrieved {len(ip_data)} IP addresses for FAR request {request_id}",
            data=response_data,
            errors=None,
            metadata={
                "execution_time_ms": "calculated_at_response_time",
                "api_version": "1.0"
            },
            request_id=None
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting IPs for FAR request {request_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving IPs for FAR request",
            details={"error": str(e), "request_id": request_id}
        )
    except Exception as e:
        logger.error(f"Error getting IPs for FAR request {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve IPs: {str(e)}")


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
      - 'graph': Include bipartite flow graph plus unified_graph (unique CIDR nodes, merged edges)
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
            bundle = _get_rule_graph_bundle(rule_id, sources, destinations, services, db)
            response['graph'] = bundle['graph']
            response['unified_graph'] = bundle['unified_graph']
        
        if 'tuples' in includes:
            response['tuples'] = _get_rule_tuples(sources, destinations, services)
        
        if 'analysis' in includes:
            response['analysis'] = _get_rule_analysis(rule, facts_dict, sources, destinations, services)
        
        # Format response based on format parameter
        if format == 'table':
            return _format_rule_as_table(response)
        
        return response
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting rule details for rule {rule_id}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving rule details",
            details={"error": str(e), "rule_id": rule_id}
        )
    except Exception as e:
        logger.error(f"Error getting rule details for rule {rule_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rule details: {str(e)}")


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


def _get_rule_graph_bundle(
    rule_id: int,
    sources: List[Dict],
    destinations: List[Dict],
    services: List[Dict],
    db: Session,
) -> Dict[str, Any]:
    """Bipartite flow graph plus unified endpoint graph (one node per CIDR, merged edges)."""
    asset_service = AssetService(db)
    graph_service = GraphService(asset_service)
    graph_data = graph_service.create_rule_graph(
        sources=sources,
        destinations=destinations,
        services=services,
        rule_id=rule_id,
    )
    unified_graph = graph_service.create_unified_endpoint_graph(
        [
            {
                "rule_id": rule_id,
                "rule_name": f"Rule {rule_id}",
                "sources": sources,
                "destinations": destinations,
                "services": services,
            }
        ]
    )
    return {"graph": graph_data, "unified_graph": unified_graph}


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
                "Service Type": TupleGenerationService()._classify_service(svc["protocol"], svc["port_ranges"])
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


def _extract_ips_from_cidr(network_cidr: str) -> List[str]:
    """
    Extract individual IP addresses from CIDR notation
    For efficiency, limits extraction to small networks to avoid performance issues
    """
    try:
        network = ipaddress.ip_network(network_cidr, strict=False)
        
        # For single IPs or small networks, return individual IPs
        if network.num_addresses <= 256:  # /24 or smaller
            return [str(ip) for ip in network.hosts()] if network.num_addresses > 2 else [str(network.network_address)]
        else:
            # For larger networks, return the network address as representative
            return [str(network.network_address)]
            
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        # If it's not valid CIDR notation, try treating it as a single IP
        try:
            ipaddress.ip_address(network_cidr)
            return [network_cidr]
        except ipaddress.AddressValueError:
            # If all else fails, return as-is (might be hostname or other format)
            return [network_cidr]


def _compute_rule_assessment(facts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute assessment data from rule facts.
    
    Returns dict with health_status, problem_count, and criticality_score.
    """
    if not facts or not isinstance(facts, dict):
        return {
            "health_status": None,
            "problem_count": 0,
            "criticality_score": 0
        }
    
    # Check for tuple_summary from hybrid facts (if available)
    tuple_summary = facts.get("tuple_summary", {})
    if isinstance(tuple_summary, dict) and "problem_count" in tuple_summary:
        problem_count = tuple_summary.get("problem_count", 0)
        total_count = tuple_summary.get("total_count", 0)
        
        # Use hybrid facts health_status if available
        health_status = facts.get("health_status")
        if health_status:
            criticality_map = {"critical": 3, "warning": 2, "clean": 1}
            return {
                "health_status": health_status,
                "problem_count": problem_count,
                "criticality_score": criticality_map.get(health_status, 0)
            }
    
    # Fall back to basic facts computation
    src_is_any = facts.get("src_is_any", False)
    dst_is_any = facts.get("dst_is_any", False)
    is_self_flow = facts.get("is_self_flow", False)
    src_has_public = facts.get("src_has_public", False)
    dst_has_public = facts.get("dst_has_public", False)
    
    # Count problems
    problem_count = sum([
        src_is_any,
        dst_is_any,
        is_self_flow,
        src_has_public,
        dst_has_public
    ])
    
    # Determine health status
    if src_is_any or dst_is_any or (is_self_flow and (src_has_public or dst_has_public)):
        health_status = "critical"
        criticality_score = 3
    elif is_self_flow or src_has_public or dst_has_public:
        health_status = "warning"
        criticality_score = 2
    elif problem_count == 0:
        health_status = "clean"
        criticality_score = 1
    else:
        # Has some issues but not categorized above
        health_status = "warning"
        criticality_score = 2
    
    return {
        "health_status": health_status,
        "problem_count": problem_count,
        "criticality_score": criticality_score
    }


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


