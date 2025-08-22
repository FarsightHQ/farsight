"""
IP address classification helpers for facts computation
"""
import ipaddress
from typing import List


def is_rfc1918(cidr_str: str) -> bool:
    """Check if CIDR is within RFC1918 private ranges"""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        
        # RFC1918 ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
        rfc1918_ranges = [
            ipaddress.ip_network('10.0.0.0/8'),
            ipaddress.ip_network('172.16.0.0/12'),
            ipaddress.ip_network('192.168.0.0/16')
        ]
        
        return any(network.overlaps(private_range) for private_range in rfc1918_ranges)
    except (ipaddress.AddressValueError, ValueError):
        return False


def is_public_ip(cidr_str: str) -> bool:
    """Check if CIDR contains public (non-RFC1918) addresses"""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        
        # Check if it's NOT in any private range
        return not is_rfc1918(cidr_str) and not network.is_loopback and not network.is_link_local
    except (ipaddress.AddressValueError, ValueError):
        return False


def overlaps_multicast(cidr_str: str) -> bool:
    """Check if CIDR overlaps with multicast range 224.0.0.0/4"""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        
        # Special case: 0.0.0.0/0 should not be classified as multicast
        if str(network) == '0.0.0.0/0':
            return False
            
        multicast_range = ipaddress.ip_network('224.0.0.0/4')
        return network.overlaps(multicast_range)
    except (ipaddress.AddressValueError, ValueError):
        return False


def is_link_local(cidr_str: str) -> bool:
    """Check if CIDR overlaps with link-local range 169.254.0.0/16"""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        
        # Special case: 0.0.0.0/0 should not be classified as link-local
        if str(network) == '0.0.0.0/0':
            return False
            
        link_local_range = ipaddress.ip_network('169.254.0.0/16')
        return network.overlaps(link_local_range)
    except (ipaddress.AddressValueError, ValueError):
        return False


def is_loopback(cidr_str: str) -> bool:
    """Check if CIDR overlaps with loopback range 127.0.0.0/8"""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        
        # Special case: 0.0.0.0/0 should not be classified as loopback
        if str(network) == '0.0.0.0/0':
            return False
            
        loopback_range = ipaddress.ip_network('127.0.0.0/8')
        return network.overlaps(loopback_range)
    except (ipaddress.AddressValueError, ValueError):
        return False


def is_broadcast(cidr_str: str) -> bool:
    """Check for broadcast addresses"""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        
        # Check for 255.255.255.255/32
        if str(network) == '255.255.255.255/32':
            return True
            
        # Check if it's the broadcast address of a subnet
        if network.num_addresses == 1:  # /32
            # Check if this IP is the broadcast of any common subnet
            ip = network.network_address
            return str(ip) == '255.255.255.255'
            
        return False
    except (ipaddress.AddressValueError, ValueError):
        return False


def is_any_network(cidr_str: str) -> bool:
    """Check if CIDR is 0.0.0.0/0 (any)"""
    try:
        network = ipaddress.ip_network(cidr_str, strict=False)
        return str(network) == '0.0.0.0/0'
    except (ipaddress.AddressValueError, ValueError):
        return False


def cidrs_overlap(cidr1: str, cidr2: str) -> bool:
    """Check if two CIDRs overlap (excluding 0.0.0.0/0 false positives)"""
    try:
        # Exclude false positives where one side is 0.0.0.0/0 and the other isn't
        if cidr1 == '0.0.0.0/0' and cidr2 != '0.0.0.0/0':
            return False
        if cidr1 != '0.0.0.0/0' and cidr2 == '0.0.0.0/0':
            return False
            
        network1 = ipaddress.ip_network(cidr1, strict=False)
        network2 = ipaddress.ip_network(cidr2, strict=False)
        return network1.overlaps(network2)
    except (ipaddress.AddressValueError, ValueError):
        return False


def analyze_cidrs(cidrs: List[str]) -> dict:
    """Analyze a list of CIDRs and return classification flags"""
    return {
        'has_any': any(is_any_network(cidr) for cidr in cidrs),
        'has_public': any(is_public_ip(cidr) for cidr in cidrs),
        'has_broadcast': any(is_broadcast(cidr) for cidr in cidrs),
        'has_multicast': any(overlaps_multicast(cidr) for cidr in cidrs),
        'has_link_local': any(is_link_local(cidr) for cidr in cidrs),
        'has_loopback': any(is_loopback(cidr) for cidr in cidrs)
    }
