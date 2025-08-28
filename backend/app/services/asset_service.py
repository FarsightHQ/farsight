"""
Asset Registry Service
Handles all asset registry operations and IP-to-asset lookups
"""
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.asset_registry import AssetRegistry

logger = logging.getLogger(__name__)


class AssetService:
    """Service for asset registry operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_asset_by_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get asset information for a specific IP address"""
        try:
            asset = self.db.query(AssetRegistry).filter(
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
                    "availability": asset.availability,
                    "vm_display_name": asset.vm_display_name,
                    "itm_id": asset.itm_id,
                    "confidentiality": asset.confidentiality,
                    "integrity": asset.integrity
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving asset for IP {ip_address}: {e}")
            return None
    
    def get_assets_for_rule_endpoints(
        self, 
        sources: List[Dict[str, str]], 
        destinations: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Get asset registry information for rule endpoints"""
        asset_matches = {
            "sources": [],
            "destinations": [],
            "total_matches": 0
        }
        
        # Check source assets
        for source in sources:
            cidr = source["network_cidr"]
            ip = cidr.split('/')[0]  # Extract IP from CIDR
            
            asset_info = self.get_asset_by_ip(ip)
            if asset_info:
                asset_matches["sources"].append(asset_info)
        
        # Check destination assets
        for dest in destinations:
            cidr = dest["network_cidr"]
            ip = cidr.split('/')[0]  # Extract IP from CIDR
            
            asset_info = self.get_asset_by_ip(ip)
            if asset_info:
                asset_matches["destinations"].append(asset_info)
        
        asset_matches["total_matches"] = len(asset_matches["sources"]) + len(asset_matches["destinations"])
        
        return asset_matches
    
    def get_assets_by_criteria(
        self, 
        environment: Optional[str] = None,
        segment: Optional[str] = None,
        os_name: Optional[str] = None,
        location: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get assets by various criteria"""
        query = self.db.query(AssetRegistry)
        
        if environment:
            query = query.filter(AssetRegistry.environment == environment)
        if segment:
            query = query.filter(AssetRegistry.segment == segment)
        if os_name:
            query = query.filter(AssetRegistry.os_name == os_name)
        if location:
            query = query.filter(AssetRegistry.location == location)
        
        assets = query.limit(limit).all()
        
        return [
            {
                "ip_address": asset.ip_address,
                "hostname": asset.hostname,
                "environment": asset.environment,
                "os_name": asset.os_name,
                "location": asset.location,
                "segment": asset.segment,
                "vlan": asset.vlan,
                "availability": asset.availability
            }
            for asset in assets
        ]
    
    def create_node_tooltip(self, cidr: str, asset_info: Optional[Dict[str, Any]], node_type: str) -> str:
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
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """Get overall asset registry statistics"""
        try:
            total_assets = self.db.query(AssetRegistry).count()
            
            # Group by environment
            env_stats = self.db.query(AssetRegistry.environment, func.count(AssetRegistry.id)).\
                group_by(AssetRegistry.environment).all()
            
            # Group by segment
            segment_stats = self.db.query(AssetRegistry.segment, func.count(AssetRegistry.id)).\
                group_by(AssetRegistry.segment).all()
            
            return {
                "total_assets": total_assets,
                "by_environment": {env: count for env, count in env_stats},
                "by_segment": {segment: count for segment, count in segment_stats}
            }
        except Exception as e:
            logger.error(f"Error getting asset statistics: {e}")
            return {"error": str(e)}
