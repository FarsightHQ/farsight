import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from typing import List, Dict, Any
from app.core.database import get_db
from app.utils.error_handlers import success_response
from app.utils.csv_errors import DatabaseConnectionError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/ip/{ip_address}/rules")
async def get_rules_for_ip(
    project_id: int,
    ip_address: str,
    db: Session = Depends(get_db),
    include_sources: bool = Query(True, description="Include rules where IP is source"),
    include_destinations: bool = Query(True, description="Include rules where IP is destination"),
):
    """
    Get all firewall rules involving a specific IP address.
    
    Args:
        ip_address: The IP address to search for (e.g., "10.177.58.43")
        include_sources: Whether to include rules where IP is a source
        include_destinations: Whether to include rules where IP is a destination
    
    Returns:
        List of all rules involving the IP address
    """
    
    # Normalize IP to CIDR format if not already
    if "/" not in ip_address:
        ip_cidr = f"{ip_address}/32"
    else:
        ip_cidr = ip_address
    
    # Build the SQL query based on parameters
    conditions = []
    if include_sources:
        conditions.append("src_ep.network_cidr = :ip_cidr")
    if include_destinations:
        conditions.append("dst_ep.network_cidr = :ip_cidr")
    
    if not conditions:
        raise HTTPException(status_code=400, detail="Must include sources, destinations, or both")
    
    where_clause = " OR ".join(conditions)
    
    query = text(f"""
        WITH ip_relationships AS (
          SELECT DISTINCT
            r.id as rule_id,
            r.action,
            r.direction,
            CASE 
              WHEN src_ep.network_cidr = :ip_cidr THEN 'SOURCE'
              WHEN dst_ep.network_cidr = :ip_cidr THEN 'DESTINATION'
            END as ip_role,
            src_ep.network_cidr as source_ip,
            dst_ep.network_cidr as destination_ip,
            svc.protocol,
            svc.port_ranges,
            req.id as request_id,
            req.title as request_title
          FROM far_rules r
          JOIN far_rule_endpoints src_ep ON r.id = src_ep.rule_id AND src_ep.endpoint_type = 'source'
          JOIN far_rule_endpoints dst_ep ON r.id = dst_ep.rule_id AND dst_ep.endpoint_type = 'destination'
          JOIN far_rule_services svc ON r.id = svc.rule_id
          JOIN far_requests req ON r.request_id = req.id
          WHERE req.project_id = :project_id AND ({where_clause})
        )
        SELECT DISTINCT
          rule_id,
          action,
          direction,
          ip_role,
          source_ip,
          destination_ip,
          protocol,
          port_ranges,
          request_id,
          request_title
        FROM ip_relationships
        ORDER BY rule_id, ip_role, protocol
    """)
    
    try:
        result = db.execute(query, {"ip_cidr": ip_cidr, "project_id": project_id})
        rows = result.fetchall()
        
        if not rows:
            no_rules_data = {
                "ip_address": ip_address,
                "total_rules": 0,
                "relationships": []
            }
            return success_response(
                data=no_rules_data,
                message=f"No rules found for IP {ip_address}"
            )
        
        relationships = []
        for row in rows:
            # Parse PostgreSQL port ranges format: {[8001,8001]} -> "8001" or {[8001,8010]} -> "8001-8010"
            port_ranges_raw = row.port_ranges
            ports_display = port_ranges_raw
            
            if port_ranges_raw and port_ranges_raw.startswith('{') and port_ranges_raw.endswith('}'):
                # Remove outer braces and split by comma
                ranges_str = port_ranges_raw[1:-1]  # Remove { }
                if ranges_str.startswith('[') and ranges_str.endswith(']'):
                    # Parse [start,end] format
                    range_content = ranges_str[1:-1]  # Remove [ ]
                    if ',' in range_content:
                        start, end = range_content.split(',')
                        start, end = start.strip(), end.strip()
                        if start == end:
                            ports_display = start
                        else:
                            ports_display = f"{start}-{end}"
                    else:
                        ports_display = range_content.strip()
            
            relationships.append({
                "rule_id": row.rule_id,
                "request_id": row.request_id,
                "request_title": row.request_title,
                "action": row.action,
                "direction": row.direction,
                "ip_role": row.ip_role,
                "source_ip": row.source_ip,
                "destination_ip": row.destination_ip,
                "protocol": row.protocol,
                "ports": ports_display,
                "service": f"{row.protocol}/{ports_display}"
            })
        
        # Group by role for summary
        sources = [r for r in relationships if r["ip_role"] == "SOURCE"]
        destinations = [r for r in relationships if r["ip_role"] == "DESTINATION"]
        
        ip_rules_data = {
            "ip_address": ip_address,
            "total_rules": len(relationships),
            "source_rules": len(sources),
            "destination_rules": len(destinations),
            "relationships": relationships
        }
        
        return success_response(
            data=ip_rules_data,
            message=f"Retrieved {len(relationships)} rules for IP {ip_address}"
        )
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting rules for IP {ip_address}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving rules for IP address",
            details={"error": str(e), "ip_address": ip_address}
        )
    except Exception as e:
        logger.error(f"Error getting rules for IP {ip_address}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rules for IP: {str(e)}")

@router.get("/ip/{ip_address}/summary")
async def get_ip_rule_summary(
    project_id: int,
    ip_address: str,
    db: Session = Depends(get_db),
):
    """
    Get a concise summary of rules for an IP address.
    """
    try:
        # Get all relationships
        result_response = await get_rules_for_ip(
            project_id, ip_address, db
        )
        result = result_response["data"]  # Extract data from standardized response
        
        if result["total_rules"] == 0:
            return success_response(
                data={
                    "ip_address": ip_address,
                    "total_rules": 0,
                    "unique_destinations": 0,
                    "unique_sources": 0,
                    "services": [],
                    "most_common_destination": None,
                    "most_common_source": None
                },
                message=f"No rules found for IP {ip_address}"
            )
        
        # Create summary
        unique_destinations = set()
        unique_sources = set()
        services = set()
        
        for rel in result["relationships"]:
            if rel["ip_role"] == "SOURCE":
                unique_destinations.add(rel["destination_ip"])
            else:
                unique_sources.add(rel["source_ip"])
            services.add(rel["service"])
        
        summary_data = {
            "ip_address": ip_address,
            "can_reach": list(unique_destinations),
            "can_be_reached_by": list(unique_sources),
            "services": sorted(list(services)),
            "total_rules": result["total_rules"]
        }
        
        return success_response(
            data=summary_data,
            message=f"Retrieved summary for IP {ip_address} with {result['total_rules']} rules"
        )
    except (HTTPException, DatabaseConnectionError):
        raise
    except OperationalError as e:
        logger.error(f"Database connection error getting IP rule summary for {ip_address}: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(
            message="Database connection failed when retrieving IP rule summary",
            details={"error": str(e), "ip_address": ip_address}
        )
    except Exception as e:
        logger.error(f"Error getting IP rule summary for {ip_address}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve IP rule summary: {str(e)}")
