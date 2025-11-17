"""
Port range formatting utilities
Handles conversion of PostgreSQL multirange format to human-readable port ranges
"""

import re


def format_port_ranges(port_ranges: str) -> str:
    """
    Parse PostgreSQL multirange format and convert to human-readable port ranges
    
    Args:
        port_ranges: PostgreSQL multirange format string (e.g., "{[80,80],[443,443]}")
    
    Returns:
        Human-readable port range string (e.g., "80, 443")
    
    Examples:
        - "{[10334,10334]}" → "10334"
        - "{[8001,8010]}" → "8001-8010"
        - "{[8001,8010],[9000,9000]}" → "8001-8010, 9000"
        - "{}" → "" (empty)
    """
    if not port_ranges or not isinstance(port_ranges, str):
        return ''
    
    # Handle empty ranges
    port_ranges = port_ranges.strip()
    if port_ranges == '{}' or port_ranges == '':
        return ''
    
    # Remove outer braces
    if not port_ranges.startswith('{') or not port_ranges.endswith('}'):
        # If not in multirange format, return as-is (might be already formatted)
        return port_ranges
    
    ranges_str = port_ranges[1:-1]  # Remove { }
    if not ranges_str:
        return ''
    
    # Use regex to match all [start,end] patterns
    range_pattern = re.compile(r'\[(\d+),(\d+)\]')
    matches = range_pattern.findall(ranges_str)
    
    if not matches:
        # If no matches, return as-is (might be malformed)
        return port_ranges
    
    formatted_ranges = []
    for start_str, end_str in matches:
        try:
            start_num = int(start_str)
            end_num = int(end_str)
            
            # If start and end are the same, return single port
            if start_num == end_num:
                formatted_ranges.append(str(start_num))
            else:
                # Return range format
                formatted_ranges.append(f"{start_num}-{end_num}")
        except ValueError:
            # Invalid numbers, skip this range
            continue
    
    return ', '.join(formatted_ranges)

