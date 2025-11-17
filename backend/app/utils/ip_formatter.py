"""
IP address formatting utilities
Handles conversion of CIDR notation to readable IP ranges
"""


def format_cidr_to_range(cidr: str) -> str:
    """
    Convert CIDR notation to IP range format
    
    Args:
        cidr: CIDR notation (e.g., "192.168.1.0/24")
    
    Returns:
        Formatted IP range (e.g., "192.168.1.0 - 192.168.1.255") or single IP for /32
    
    Examples:
        - "10.0.0.1/32" → "10.0.0.1"
        - "192.168.1.0/24" → "192.168.1.0 - 192.168.1.255"
        - "172.16.0.0/16" → "172.16.0.0 - 172.16.255.255"
        - "0.0.0.0/0" → "0.0.0.0 - 255.255.255.255"
    """
    if not cidr or not isinstance(cidr, str):
        return cidr or ''
    
    try:
        # Check if it's already in range format (contains " - ")
        if ' - ' in cidr:
            return cidr
        
        # Check if it contains CIDR notation (has /)
        if '/' not in cidr:
            # No prefix, treat as single IP
            return cidr
        
        ip_str, prefix_str = cidr.split('/', 1)
        
        try:
            prefix = int(prefix_str)
        except ValueError:
            return cidr  # Invalid prefix, return original
        
        # Validate prefix
        if prefix < 0 or prefix > 32:
            return cidr  # Invalid prefix, return original
        
        # Parse IP address
        try:
            ip_parts = [int(part) for part in ip_str.split('.')]
        except ValueError:
            return cidr  # Invalid IP, return original
        
        if len(ip_parts) != 4 or any(p < 0 or p > 255 for p in ip_parts):
            return cidr  # Invalid IP, return original
        
        # Single IP (/32)
        if prefix == 32:
            return ip_str
        
        # Calculate network address (first IP)
        host_bits = 32 - prefix
        host_mask = (1 << host_bits) - 1
        network_mask = 0xFFFFFFFF & (~host_mask)
        
        # Convert IP to 32-bit integer
        ip_int = (ip_parts[0] << 24) | (ip_parts[1] << 16) | (ip_parts[2] << 8) | ip_parts[3]
        
        # Calculate network address
        network_int = ip_int & network_mask
        
        # Calculate broadcast address (last IP)
        broadcast_int = network_int | host_mask
        
        # Convert back to IP address strings
        network_ip = '.'.join([
            str((network_int >> 24) & 0xFF),
            str((network_int >> 16) & 0xFF),
            str((network_int >> 8) & 0xFF),
            str(network_int & 0xFF)
        ])
        
        broadcast_ip = '.'.join([
            str((broadcast_int >> 24) & 0xFF),
            str((broadcast_int >> 16) & 0xFF),
            str((broadcast_int >> 8) & 0xFF),
            str(broadcast_int & 0xFF)
        ])
        
        # Return range format
        return f"{network_ip} - {broadcast_ip}"
    
    except Exception:
        # If any error occurs, return original CIDR
        return cidr


def is_valid_cidr(cidr: str) -> bool:
    """
    Check if a string is a valid CIDR notation
    
    Args:
        cidr: String to check
    
    Returns:
        True if valid CIDR notation
    """
    if not cidr or not isinstance(cidr, str):
        return False
    
    try:
        if '/' not in cidr:
            return False
        
        ip_str, prefix_str = cidr.split('/', 1)
        if not ip_str or not prefix_str:
            return False
        
        try:
            prefix = int(prefix_str)
        except ValueError:
            return False
        
        if prefix < 0 or prefix > 32:
            return False
        
        ip_parts = ip_str.split('.')
        if len(ip_parts) != 4:
            return False
        
        for part in ip_parts:
            try:
                p = int(part)
                if p < 0 or p > 255:
                    return False
            except ValueError:
                return False
        
        return True
    except Exception:
        return False

