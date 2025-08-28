"""
Network Tuple Generation Service
Handles generation and analysis of network tuples from firewall rules
"""
import logging
from typing import Dict, List, Any, Tuple
from itertools import product

logger = logging.getLogger(__name__)


class TupleGenerationService:
    """Service for generating and analyzing network tuples"""
    
    def __init__(self):
        pass
    
    def generate_rule_tuples(
        self, 
        sources: List[Dict[str, str]], 
        destinations: List[Dict[str, str]], 
        services: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Generate actual network tuples for a rule"""
        tuples = []
        
        for source, dest, service in product(sources, destinations, services):
            # Parse port ranges (basic parsing for PostgreSQL format)
            port_range = service["port_ranges"].strip('{}').strip('[]')
            port_display = self._format_port_range(port_range)
            
            tuple_data = {
                "source": source["network_cidr"],
                "destination": dest["network_cidr"],
                "protocol": service["protocol"],
                "ports": port_display,
                "tuple_id": f"{source['network_cidr']}→{dest['network_cidr']}:{service['protocol']}/{port_display}",
                "service_type": self._classify_service(service["protocol"], service["port_ranges"])
            }
            tuples.append(tuple_data)
        
        return {
            "tuples": tuples,
            "total_count": len(tuples),
            "summary": {
                "unique_sources": len(sources),
                "unique_destinations": len(destinations),
                "unique_services": len(services)
            },
            "analysis": self._analyze_tuples(tuples)
        }
    
    def calculate_tuple_estimate(
        self, 
        source_count: int, 
        destination_count: int, 
        service_count: int
    ) -> int:
        """Calculate estimated number of tuples"""
        return source_count * destination_count * max(service_count, 1)
    
    def analyze_tuple_complexity(self, tuple_count: int) -> Dict[str, Any]:
        """Analyze the complexity implications of tuple count"""
        complexity_levels = {
            "low": tuple_count <= 10,
            "medium": 10 < tuple_count <= 100,
            "high": 100 < tuple_count <= 1000,
            "very_high": tuple_count > 1000
        }
        
        # Determine complexity level
        complexity = "low"
        for level, condition in complexity_levels.items():
            if condition:
                complexity = level
                break
        
        return {
            "tuple_count": tuple_count,
            "complexity_level": complexity,
            "performance_impact": self._assess_performance_impact(tuple_count),
            "recommendations": self._get_tuple_recommendations(tuple_count)
        }
    
    def group_tuples_by_criteria(
        self, 
        tuples: List[Dict[str, Any]], 
        group_by: str = "protocol"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group tuples by various criteria"""
        grouped = {}
        
        for tuple_data in tuples:
            key = tuple_data.get(group_by, "unknown")
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(tuple_data)
        
        return grouped
    
    def find_overlapping_tuples(self, tuples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find tuples that might have overlapping network ranges"""
        overlapping = []
        
        for i, tuple1 in enumerate(tuples):
            for j, tuple2 in enumerate(tuples[i+1:], i+1):
                if self._check_tuple_overlap(tuple1, tuple2):
                    overlapping.append({
                        "tuple1": tuple1,
                        "tuple2": tuple2,
                        "overlap_type": self._determine_overlap_type(tuple1, tuple2)
                    })
        
        return overlapping
    
    def _format_port_range(self, port_range: str) -> str:
        """Format port range for display"""
        if ',' in port_range:
            start_port, end_port = port_range.split(',')
            return f"{start_port}-{end_port}" if start_port != end_port else start_port
        else:
            return port_range
    
    def _classify_service(self, protocol: str, port_ranges: str) -> str:
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
        try:
            port_num = int(port_str.split(',')[0] if ',' in port_str else port_str)
            if 1024 <= port_num <= 65535:
                return "High Ports (Ephemeral)" if port_num >= 32768 else "User/Application Port"
            elif port_num < 1024:
                return "System/Well-Known Port"
        except ValueError:
            pass
        
        return "Unknown Service"
    
    def _analyze_tuples(self, tuples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze tuple patterns and characteristics"""
        if not tuples:
            return {"empty": True}
        
        protocols = set(t["protocol"] for t in tuples)
        service_types = set(t["service_type"] for t in tuples)
        unique_sources = set(t["source"] for t in tuples)
        unique_destinations = set(t["destination"] for t in tuples)
        
        return {
            "protocol_diversity": len(protocols),
            "protocols_used": list(protocols),
            "service_type_diversity": len(service_types),
            "service_types": list(service_types),
            "source_diversity": len(unique_sources),
            "destination_diversity": len(unique_destinations),
            "fan_out_ratio": len(unique_destinations) / len(unique_sources) if unique_sources else 0
        }
    
    def _assess_performance_impact(self, tuple_count: int) -> str:
        """Assess performance impact based on tuple count"""
        if tuple_count <= 10:
            return "minimal"
        elif tuple_count <= 100:
            return "low"
        elif tuple_count <= 1000:
            return "moderate"
        else:
            return "high"
    
    def _get_tuple_recommendations(self, tuple_count: int) -> List[str]:
        """Get recommendations based on tuple count"""
        recommendations = []
        
        if tuple_count > 1000:
            recommendations.extend([
                "Consider breaking this rule into multiple more specific rules",
                "Review if all source-destination combinations are necessary",
                "Consider using more specific IP ranges instead of broad subnets"
            ])
        elif tuple_count > 100:
            recommendations.extend([
                "Monitor firewall performance with this rule",
                "Consider if rule can be optimized for better specificity"
            ])
        elif tuple_count > 50:
            recommendations.append("Rule generates moderate complexity - ensure it's well documented")
        else:
            recommendations.append("Rule complexity is within acceptable limits")
        
        return recommendations
    
    def _check_tuple_overlap(self, tuple1: Dict[str, Any], tuple2: Dict[str, Any]) -> bool:
        """Check if two tuples have overlapping characteristics"""
        # Simple overlap check - can be enhanced with CIDR overlap logic
        return (
            tuple1["source"] == tuple2["source"] or
            tuple1["destination"] == tuple2["destination"] or
            (tuple1["protocol"] == tuple2["protocol"] and tuple1["ports"] == tuple2["ports"])
        )
    
    def _determine_overlap_type(self, tuple1: Dict[str, Any], tuple2: Dict[str, Any]) -> str:
        """Determine the type of overlap between tuples"""
        overlaps = []
        
        if tuple1["source"] == tuple2["source"]:
            overlaps.append("source")
        if tuple1["destination"] == tuple2["destination"]:
            overlaps.append("destination")
        if tuple1["protocol"] == tuple2["protocol"] and tuple1["ports"] == tuple2["ports"]:
            overlaps.append("service")
        
        return "_".join(overlaps) if overlaps else "unknown"
