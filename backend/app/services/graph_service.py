"""
Graph Service for D3.js Visualization
Handles creation of graph data structures for network visualization
"""
import logging
from typing import Dict, List, Any, Set, Tuple, Optional
from ..services.asset_service import AssetService

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
        """Create a D3-compatible graph for a firewall rule"""
        nodes = []
        links = []
        node_map = {}  # Track nodes to avoid duplicates
        
        # Create the central rule node
        rule_node_id = f"rule_{rule_id}"
        rule_node = {
            "id": rule_node_id,
            "type": "rule",
            "label": rule_name or f"Rule {rule_id}",
            "group": "rule",
            "size": 20,
            "color": "#ff6b6b",
            "tooltip": f"FAR Rule {rule_id}\\n{rule_name or 'Firewall Access Rule'}"
        }
        nodes.append(rule_node)
        node_map[rule_node_id] = rule_node
        
        # Process source nodes
        source_group_id = f"sources_{rule_id}"
        if len(sources) > 1:
            # Create a group node for multiple sources
            source_group = {
                "id": source_group_id,
                "type": "source_group",
                "label": f"Sources ({len(sources)})",
                "group": "source",
                "size": 15,
                "color": "#4ecdc4",
                "tooltip": f"{len(sources)} source networks"
            }
            nodes.append(source_group)
            node_map[source_group_id] = source_group
            
            # Link rule to source group
            links.append({
                "source": rule_node_id,
                "target": source_group_id,
                "type": "contains",
                "label": "sources"
            })
        
        # Add individual source nodes
        for i, source in enumerate(sources):
            source_id = f"src_{rule_id}_{i}"
            asset_info = self.asset_service.get_asset_by_ip(source["network_cidr"])
            
            source_node = {
                "id": source_id,
                "type": "source",
                "label": source["network_cidr"],
                "group": "source",
                "size": 10,
                "color": "#4ecdc4",
                "tooltip": self.asset_service.create_node_tooltip(source["network_cidr"], asset_info, "Source")
            }
            nodes.append(source_node)
            node_map[source_id] = source_node
            
            # Link to rule or source group
            parent_id = source_group_id if len(sources) > 1 else rule_node_id
            links.append({
                "source": parent_id,
                "target": source_id,
                "type": "contains" if len(sources) > 1 else "source_to_rule",
                "label": "source" if len(sources) == 1 else ""
            })
        
        # Process destination nodes
        dest_group_id = f"destinations_{rule_id}"
        if len(destinations) > 1:
            # Create a group node for multiple destinations
            dest_group = {
                "id": dest_group_id,
                "type": "dest_group",
                "label": f"Destinations ({len(destinations)})",
                "group": "destination",
                "size": 15,
                "color": "#45b7d1",
                "tooltip": f"{len(destinations)} destination networks"
            }
            nodes.append(dest_group)
            node_map[dest_group_id] = dest_group
            
            # Link rule to destination group
            links.append({
                "source": rule_node_id,
                "target": dest_group_id,
                "type": "contains",
                "label": "destinations"
            })
        
        # Add individual destination nodes
        for i, dest in enumerate(destinations):
            dest_id = f"dst_{rule_id}_{i}"
            asset_info = self.asset_service.get_asset_by_ip(dest["network_cidr"])
            
            dest_node = {
                "id": dest_id,
                "type": "destination",
                "label": dest["network_cidr"],
                "group": "destination",
                "size": 10,
                "color": "#45b7d1",
                "tooltip": self.asset_service.create_node_tooltip(dest["network_cidr"], asset_info, "Destination")
            }
            nodes.append(dest_node)
            node_map[dest_id] = dest_node
            
            # Link to rule or destination group
            parent_id = dest_group_id if len(destinations) > 1 else rule_node_id
            links.append({
                "source": rule_node_id if len(destinations) == 1 else parent_id,
                "target": dest_id,
                "type": "rule_to_dest" if len(destinations) == 1 else "contains",
                "label": "destination" if len(destinations) == 1 else ""
            })
        
        # Process service nodes
        service_group_id = f"services_{rule_id}"
        if len(services) > 1:
            # Create a group node for multiple services
            service_group = {
                "id": service_group_id,
                "type": "service_group",
                "label": f"Services ({len(services)})",
                "group": "service",
                "size": 15,
                "color": "#96ceb4",
                "tooltip": f"{len(services)} services/protocols"
            }
            nodes.append(service_group)
            node_map[service_group_id] = service_group
            
            # Link rule to service group
            links.append({
                "source": rule_node_id,
                "target": service_group_id,
                "type": "contains",
                "label": "services"
            })
        
        # Add individual service nodes
        for i, service in enumerate(services):
            service_id = f"svc_{rule_id}_{i}"
            port_range = service["port_ranges"].strip('{}').strip('[]')
            port_display = self._format_port_range(port_range)
            
            service_node = {
                "id": service_id,
                "type": "service",
                "label": f"{service['protocol']}/{port_display}",
                "group": "service",
                "size": 10,
                "color": "#96ceb4",
                "tooltip": f"Protocol: {service['protocol']}\\nPorts: {port_display}"
            }
            nodes.append(service_node)
            node_map[service_id] = service_node
            
            # Link to rule or service group
            parent_id = service_group_id if len(services) > 1 else rule_node_id
            links.append({
                "source": rule_node_id if len(services) == 1 else parent_id,
                "target": service_id,
                "type": "rule_to_service" if len(services) == 1 else "contains",
                "label": "service" if len(services) == 1 else ""
            })
        
        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "node_count": len(nodes),
                "link_count": len(links),
                "source_count": len(sources),
                "destination_count": len(destinations),
                "service_count": len(services)
            },
            "layout_hints": {
                "center_node": rule_node_id,
                "groups": {
                    "rule": {"color": "#ff6b6b"},
                    "source": {"color": "#4ecdc4"},
                    "destination": {"color": "#45b7d1"},
                    "service": {"color": "#96ceb4"}
                },
                "force_simulation": {
                    "charge": -300,
                    "link_distance": 100,
                    "center_force": 0.1
                }
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
            node = {
                "id": f"net_{network.replace('/', '_').replace('.', '_')}",
                "type": "network",
                "label": network,
                "group": "network",
                "size": 12,
                "color": "#feca57",
                "tooltip": self.asset_service.create_node_tooltip(network, asset_info, "Network")
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
    
    def _format_port_range(self, port_range: str) -> str:
        """Format port range for display"""
        if ',' in port_range:
            start_port, end_port = port_range.split(',')
            return f"{start_port}-{end_port}" if start_port != end_port else start_port
        else:
            return port_range
    
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
