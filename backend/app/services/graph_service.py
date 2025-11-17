"""
Graph Service for D3.js Visualization
Handles creation of graph data structures for network visualization
"""
import logging
from typing import Dict, List, Any, Set, Tuple, Optional
from ..services.asset_service import AssetService
from ..utils.ip_formatter import format_cidr_to_range
from ..utils.port_formatter import format_port_ranges

logger = logging.getLogger(__name__)


class GraphService:
    """Service for generating D3-compatible graph data"""
    
    def __init__(self, asset_service: AssetService):
        self.asset_service = asset_service
    
    def create_rule_graph(
        self, 
        sources: List[Dict[str, str]], 
        destinations: List[Dict[str, str]], 
        services: List[Dict[str, str]],
        rule_id: int,
        rule_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a flow-style graph for a firewall rule with rectangles for IPs and circles for ports"""
        
        # Process sources - simple list of IP rectangles
        source_list = []
        for i, source in enumerate(sources):
            network_cidr = source["network_cidr"]
            asset_info = self.asset_service.get_asset_by_ip(network_cidr)
            formatted_label = format_cidr_to_range(network_cidr)
            base_tooltip = self.asset_service.create_node_tooltip(network_cidr, asset_info, "Source")
            
            source_list.append({
                "id": f"src_{rule_id}_{i}",
                "network_cidr": network_cidr,
                "label": formatted_label,
                "formatted_label": formatted_label,
                "tooltip": f"{base_tooltip}\\nCIDR: {network_cidr}"
            })
        
        # Process destinations with ports attached
        destination_list = []
        for i, dest in enumerate(destinations):
            network_cidr = dest["network_cidr"]
            asset_info = self.asset_service.get_asset_by_ip(network_cidr)
            formatted_label = format_cidr_to_range(network_cidr)
            base_tooltip = self.asset_service.create_node_tooltip(network_cidr, asset_info, "Destination")
            
            # Aggregate ports per destination (one circle per port range)
            ports = []
            for j, service in enumerate(services):
                port_ranges_raw = service["port_ranges"]
                port_display = format_port_ranges(port_ranges_raw)
                protocol = service['protocol']
                
                ports.append({
                    "id": f"port_{rule_id}_{i}_{j}",
                    "protocol": protocol,
                    "port_ranges": port_ranges_raw,
                    "formatted_ports": port_display,
                    "tooltip": f"Protocol: {protocol}\\nPorts: {port_display or 'any'}\\nRaw: {port_ranges_raw}"
                })
            
            destination_list.append({
                "id": f"dst_{rule_id}_{i}",
                "network_cidr": network_cidr,
                "label": formatted_label,
                "formatted_label": formatted_label,
                "ports": ports,
                "tooltip": f"{base_tooltip}\\nCIDR: {network_cidr}"
            })
        
        # Create connections - one per source-destination pair
        connections = []
        for source in source_list:
            for dest in destination_list:
                # Count ports for this connection
                port_count = len(dest["ports"])
                
                # Collect all services for this connection
                connection_services = []
                for port in dest["ports"]:
                    connection_services.append({
                        "protocol": port["protocol"],
                        "port_ranges": port["port_ranges"],
                        "formatted_ports": port["formatted_ports"]
                    })
                
                connections.append({
                    "source_id": source["id"],
                    "destination_id": dest["id"],
                    "port_count": port_count,
                    "services": connection_services
                })
        
        return {
            "sources": source_list,
            "destinations": destination_list,
            "connections": connections,
            "metadata": {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "source_count": len(sources),
                "destination_count": len(destinations),
                "service_count": len(services),
                "connection_count": len(connections)
            }
        }
    
    def create_multi_rule_graph(
        self, 
        rule_data: List[Dict[str, Any]],
        max_rules: int = 10
    ) -> Dict[str, Any]:
        """Create a graph showing relationships between multiple rules"""
        if len(rule_data) > max_rules:
            rule_data = rule_data[:max_rules]
        
        nodes = []
        links = []
        shared_elements = self._find_shared_elements(rule_data)
        
        # Create nodes for each rule
        for rule in rule_data:
            rule_id = rule["rule_id"]
            rule_node = {
                "id": f"rule_{rule_id}",
                "type": "rule",
                "label": f"Rule {rule_id}",
                "group": "rule",
                "size": 15,
                "color": "#ff6b6b",
                "tooltip": f"FAR Rule {rule_id}"
            }
            nodes.append(rule_node)
        
        # Create shared element nodes and connections
        self._add_shared_element_nodes(nodes, links, shared_elements, rule_data)
        
        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "rule_count": len(rule_data),
                "shared_elements": len(shared_elements),
                "node_count": len(nodes),
                "link_count": len(links)
            }
        }
    
    def create_network_topology_graph(
        self, 
        network_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a network topology view based on firewall rules"""
        nodes = []
        links = []
        network_map = {}
        
        # Extract unique networks from rules
        networks = set()
        for rule in network_data:
            for source in rule.get("sources", []):
                networks.add(source["network_cidr"])
            for dest in rule.get("destinations", []):
                networks.add(dest["network_cidr"])
        
        # Create network nodes
        for network in networks:
            asset_info = self.asset_service.get_asset_by_ip(network)
            formatted_label = format_cidr_to_range(network)
            base_tooltip = self.asset_service.create_node_tooltip(network, asset_info, "Network")
            
            node = {
                "id": f"net_{network.replace('/', '_').replace('.', '_')}",
                "type": "network",
                "label": formatted_label,
                "network_cidr": network,
                "group": "network",
                "size": 12,
                "color": "#feca57",
                "tooltip": f"{base_tooltip}\\nCIDR: {network}"
            }
            nodes.append(node)
            network_map[network] = node["id"]
        
        # Create links based on rules
        for rule in network_data:
            rule_id = rule["rule_id"]
            sources = rule.get("sources", [])
            destinations = rule.get("destinations", [])
            
            for source in sources:
                for dest in destinations:
                    source_id = network_map[source["network_cidr"]]
                    dest_id = network_map[dest["network_cidr"]]
                    
                    # Avoid self-links
                    if source_id != dest_id:
                        links.append({
                            "source": source_id,
                            "target": dest_id,
                            "type": "traffic_flow",
                            "label": f"Rule {rule_id}",
                            "rule_id": rule_id
                        })
        
        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "network_count": len(networks),
                "rule_count": len(network_data),
                "connection_count": len(links)
            }
        }
    
    def _find_shared_elements(self, rule_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Set[int]]]:
        """Find elements shared between multiple rules"""
        shared = {
            "sources": {},
            "destinations": {},
            "services": {}
        }
        
        for rule in rule_data:
            rule_id = rule["rule_id"]
            
            # Track sources
            for source in rule.get("sources", []):
                cidr = source["network_cidr"]
                if cidr not in shared["sources"]:
                    shared["sources"][cidr] = set()
                shared["sources"][cidr].add(rule_id)
            
            # Track destinations
            for dest in rule.get("destinations", []):
                cidr = dest["network_cidr"]
                if cidr not in shared["destinations"]:
                    shared["destinations"][cidr] = set()
                shared["destinations"][cidr].add(rule_id)
            
            # Track services
            for service in rule.get("services", []):
                svc_key = f"{service['protocol']}/{service['port_ranges']}"
                if svc_key not in shared["services"]:
                    shared["services"][svc_key] = set()
                shared["services"][svc_key].add(rule_id)
        
        # Filter to only truly shared elements (used by 2+ rules)
        filtered_shared = {}
        for category, elements in shared.items():
            filtered_shared[category] = {
                k: v for k, v in elements.items() if len(v) > 1
            }
        
        return filtered_shared
    
    def _add_shared_element_nodes(
        self, 
        nodes: List[Dict[str, Any]], 
        links: List[Dict[str, Any]], 
        shared_elements: Dict[str, Dict[str, Set[int]]], 
        rule_data: List[Dict[str, Any]]
    ):
        """Add nodes for shared elements and connect them to rules"""
        node_id_counter = 0
        
        for category, elements in shared_elements.items():
            color_map = {
                "sources": "#4ecdc4",
                "destinations": "#45b7d1", 
                "services": "#96ceb4"
            }
            
            for element, rule_ids in elements.items():
                node_id = f"shared_{category}_{node_id_counter}"
                node_id_counter += 1
                
                # Create shared element node
                shared_node = {
                    "id": node_id,
                    "type": f"shared_{category[:-1]}",  # Remove 's' from category
                    "label": element,
                    "group": f"shared_{category}",
                    "size": 8 + len(rule_ids) * 2,  # Size based on sharing frequency
                    "color": color_map[category],
                    "tooltip": f"Shared {category[:-1]}: {element}\\nUsed by {len(rule_ids)} rules"
                }
                nodes.append(shared_node)
                
                # Link to each rule that uses this element
                for rule_id in rule_ids:
                    links.append({
                        "source": f"rule_{rule_id}",
                        "target": node_id,
                        "type": f"uses_{category[:-1]}",
                        "label": category[:-1]
                    })
