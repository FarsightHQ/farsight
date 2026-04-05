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
            asset_info = self.asset_service.get_asset_for_network_cidr(network_cidr)
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
            asset_info = self.asset_service.get_asset_for_network_cidr(network_cidr)
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
    
    def _network_cidr_to_node_id(self, network: str) -> str:
        return f"net_{network.replace('/', '_').replace('.', '_')}"

    def create_unified_endpoint_graph(self, rule_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        One node per distinct network_cidr; directed edges for each src×dst implied by rules,
        merged across rules with aggregated rule_ids and services.
        """
        networks: Set[str] = set()
        for rule in rule_data:
            for source in rule.get("sources", []):
                networks.add(source["network_cidr"])
            for dest in rule.get("destinations", []):
                networks.add(dest["network_cidr"])

        nodes: List[Dict[str, Any]] = []
        for cidr in sorted(networks):
            asset_info = self.asset_service.get_asset_for_network_cidr(cidr)
            formatted_label = format_cidr_to_range(cidr)
            base_tooltip = self.asset_service.create_node_tooltip(cidr, asset_info, "Network")
            node: Dict[str, Any] = {
                "id": self._network_cidr_to_node_id(cidr),
                "type": "network",
                "label": formatted_label,
                "network_cidr": cidr,
                "group": "network",
                "size": 12,
                "color": "#feca57",
                "tooltip": f"{base_tooltip}\\nCIDR: {cidr}",
                "asset": asset_info,
                "segment": asset_info.get("segment") if asset_info else None,
                "vlan": str(asset_info["vlan"]) if asset_info and asset_info.get("vlan") is not None else None,
                "environment": asset_info.get("environment") if asset_info else None,
                "location": asset_info.get("location") if asset_info else None,
            }
            nodes.append(node)

        network_map = {n["network_cidr"]: n["id"] for n in nodes}

        # (src_cidr, dst_cidr) -> aggregated link payload
        link_agg: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for rule in rule_data:
            rule_id = rule["rule_id"]
            rule_name = rule.get("rule_name")
            sources = rule.get("sources", [])
            destinations = rule.get("destinations", [])
            services = rule.get("services", [])

            rule_services: List[Dict[str, str]] = []
            for svc in services:
                pr = str(svc.get("port_ranges", "") or "")
                proto = str(svc.get("protocol", "") or "")
                rule_services.append({
                    "protocol": proto,
                    "port_ranges": pr,
                    "formatted_ports": format_port_ranges(pr),
                })

            for source in sources:
                for dest in destinations:
                    src_cidr = source["network_cidr"]
                    dst_cidr = dest["network_cidr"]
                    if src_cidr == dst_cidr:
                        continue
                    src_id = network_map[src_cidr]
                    dst_id = network_map[dst_cidr]
                    key = (src_cidr, dst_cidr)
                    if key not in link_agg:
                        link_agg[key] = {
                            "source": src_id,
                            "target": dst_id,
                            "type": "traffic_flow",
                            "rule_ids": set(),
                            "rules": [],
                            "service_keys": set(),
                            "services": [],
                        }
                    entry = link_agg[key]
                    entry["rule_ids"].add(rule_id)
                    if rule_name:
                        entry["rules"].append({"id": rule_id, "name": rule_name})
                    else:
                        entry["rules"].append({"id": rule_id, "name": None})
                    for rs in rule_services:
                        sk = (rs["protocol"], rs["port_ranges"])
                        if sk not in entry["service_keys"]:
                            entry["service_keys"].add(sk)
                            entry["services"].append(rs)

        links: List[Dict[str, Any]] = []
        for entry in link_agg.values():
            rule_ids_sorted = sorted(entry["rule_ids"])
            label = f"Rules {rule_ids_sorted}" if len(rule_ids_sorted) != 1 else f"Rule {rule_ids_sorted[0]}"
            links.append({
                "source": entry["source"],
                "target": entry["target"],
                "type": entry["type"],
                "label": label,
                "rule_ids": rule_ids_sorted,
                "rules": entry["rules"],
                "services": entry["services"],
            })

        distinct_rules = {r["rule_id"] for r in rule_data}
        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "schema_version": 1,
                "network_count": len(networks),
                "rule_count": len(distinct_rules),
                "connection_count": len(links),
                "node_count": len(nodes),
                "link_count": len(links),
            },
        }

    def create_network_topology_graph(
        self,
        network_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Backward-compatible name: same as unified endpoint graph (unique CIDRs, merged edges)."""
        return self.create_unified_endpoint_graph(network_data)
    
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
