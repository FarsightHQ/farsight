"""
IP address and port range normalization utilities for Phase 2.2
"""
import ipaddress
import hashlib
from typing import List, Set, Tuple, Union, Optional
from dataclasses import dataclass


@dataclass
class NormalizedEndpoint:
    """Normalized IP endpoint in CIDR format"""
    network_cidr: str
    
    def __post_init__(self):
        # Validate CIDR format
        try:
            ipaddress.ip_network(self.network_cidr, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR format '{self.network_cidr}': {e}")


@dataclass  
class NormalizedService:
    """Normalized service with protocol and coalesced port ranges"""
    protocol: str
    port_ranges: List[Tuple[int, int]]  # List of (start, end) tuples
    
    def __post_init__(self):
        # Sort and validate port ranges
        self.port_ranges = sorted(self.port_ranges)
        for start, end in self.port_ranges:
            if not (1 <= start <= end <= 65535):
                raise ValueError(f"Invalid port range: {start}-{end}")


@dataclass
class NormalizedRule:
    """Complete normalized rule with endpoints and services"""
    source_endpoints: List[NormalizedEndpoint]
    destination_endpoints: List[NormalizedEndpoint] 
    services: List[NormalizedService]
    action: str = 'allow'
    direction: Optional[str] = None


def normalize_ip_address(ip_str: str) -> str:
    """
    Normalize IP address or range to CIDR format
    
    Args:
        ip_str: IP address, range, or CIDR (e.g., '192.168.1.1', '10.0.0.1-10.0.0.10', '172.16.0.0/24')
        
    Returns:
        CIDR notation string
        
    Raises:
        ValueError: If IP format is invalid
    """
    ip_str = ip_str.strip()
    
    # Handle CIDR notation (already normalized)
    if '/' in ip_str:
        try:
            network = ipaddress.ip_network(ip_str, strict=False)
            return str(network)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR format '{ip_str}': {e}")
    
    # Handle IP ranges (e.g., "10.0.0.1-10.0.0.10")
    if '-' in ip_str:
        try:
            start_str, end_str = ip_str.split('-', 1)
            start_ip = ipaddress.ip_address(start_str.strip())
            end_ip = ipaddress.ip_address(end_str.strip())
            
            if start_ip.version != end_ip.version:
                raise ValueError("IP version mismatch in range")
            
            # Convert range to list of networks
            networks = list(ipaddress.summarize_address_range(start_ip, end_ip))
            
            # Return the first (and typically only) network that covers the range
            return str(networks[0])
                
        except ValueError as e:
            raise ValueError(f"Invalid IP range '{ip_str}': {e}")
    
    # Handle single IP address
    try:
        ip = ipaddress.ip_address(ip_str)
        # Convert single IP to /32 (IPv4) or /128 (IPv6) network
        if ip.version == 4:
            return f"{ip}/32"
        else:
            return f"{ip}/128"
    except ValueError as e:
        raise ValueError(f"Invalid IP address '{ip_str}': {e}")


def normalize_port_ranges(port_str: str, protocol: str = 'tcp') -> NormalizedService:
    """
    Normalize port specification to coalesced ranges
    
    Args:
        port_str: Port specification (e.g., '80', '80,443', '1000-2000', '80,443,1000-2000')
        protocol: Protocol name (default: 'tcp')
        
    Returns:
        NormalizedService with coalesced port ranges
        
    Raises:
        ValueError: If port format is invalid
    """
    if not port_str or port_str.strip() == '':
        raise ValueError("Empty port specification")
    
    ranges: Set[Tuple[int, int]] = set()
    
    # Split by comma and process each part
    for part in port_str.split(','):
        part = part.strip()
        if not part:
            continue
            
        if '-' in part:
            # Port range (e.g., "1000-2000")
            try:
                start_str, end_str = part.split('-', 1)
                start_port = int(start_str.strip())
                end_port = int(end_str.strip())
                
                if start_port > end_port:
                    start_port, end_port = end_port, start_port
                    
                if not (1 <= start_port <= 65535 and 1 <= end_port <= 65535):
                    raise ValueError(f"Ports must be between 1-65535: {part}")
                    
                ranges.add((start_port, end_port))
                
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid port range format '{part}': must be numeric")
                raise
        else:
            # Single port
            try:
                port = int(part)
                if not (1 <= port <= 65535):
                    raise ValueError(f"Port must be between 1-65535: {port}")
                ranges.add((port, port))
            except ValueError as e:
                if "invalid literal" in str(e):
                    raise ValueError(f"Invalid port format '{part}': must be numeric")
                raise
    
    if not ranges:
        raise ValueError("No valid ports found")
    
    # Coalesce overlapping and adjacent ranges
    coalesced = coalesce_port_ranges(list(ranges))
    
    return NormalizedService(
        protocol=protocol.lower(),
        port_ranges=coalesced
    )


def coalesce_port_ranges(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Coalesce overlapping and adjacent port ranges
    
    Args:
        ranges: List of (start, end) port range tuples
        
    Returns:
        List of coalesced non-overlapping ranges, sorted by start port
    """
    if not ranges:
        return []
    
    # Sort by start port
    sorted_ranges = sorted(ranges)
    coalesced = [sorted_ranges[0]]
    
    for current_start, current_end in sorted_ranges[1:]:
        last_start, last_end = coalesced[-1]
        
        # Check if ranges overlap or are adjacent
        if current_start <= last_end + 1:
            # Merge ranges
            coalesced[-1] = (last_start, max(last_end, current_end))
        else:
            # No overlap, add as new range
            coalesced.append((current_start, current_end))
    
    return coalesced


def compute_canonical_hash(rule: NormalizedRule) -> bytes:
    """
    Compute SHA-256 hash for normalized rule to enable deduplication
    
    Args:
        rule: Normalized rule object
        
    Returns:
        32-byte SHA-256 hash
    """
    # Create deterministic string representation
    components = []
    
    # Add action and direction
    components.append(f"action:{rule.action}")
    if rule.direction:
        components.append(f"direction:{rule.direction}")
    
    # Add sorted source endpoints
    source_cidrs = sorted([ep.network_cidr for ep in rule.source_endpoints])
    components.append(f"sources:{','.join(source_cidrs)}")
    
    # Add sorted destination endpoints
    dest_cidrs = sorted([ep.network_cidr for ep in rule.destination_endpoints])
    components.append(f"destinations:{','.join(dest_cidrs)}")
    
    # Add sorted services
    service_strs = []
    for service in rule.services:
        ranges_str = ','.join([f"{start}-{end}" for start, end in service.port_ranges])
        service_strs.append(f"{service.protocol}:{ranges_str}")
    
    service_strs.sort()
    components.append(f"services:{';'.join(service_strs)}")
    
    # Create hash
    rule_str = '|'.join(components)
    return hashlib.sha256(rule_str.encode('utf-8')).digest()


def format_port_ranges_for_postgres(ranges: List[Tuple[int, int]]) -> str:
    """
    Format port ranges for PostgreSQL int4multirange type
    
    Args:
        ranges: List of (start, end) port range tuples
        
    Returns:
        PostgreSQL multirange literal string
    """
    if not ranges:
        return '{}'
    
    # Format each range as [start,end]
    range_strs = []
    for start, end in ranges:
        if start == end:
            range_strs.append(f'[{start},{start}]')
        else:
            range_strs.append(f'[{start},{end}]')
    
    return '{' + ','.join(range_strs) + '}'
