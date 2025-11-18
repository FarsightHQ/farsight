/**
 * IP address utility functions
 * Handles conversion of CIDR notation to readable IP ranges
 */

/**
 * Convert CIDR notation to IP range format
 * 
 * @param {string} cidr - CIDR notation (e.g., "192.168.1.0/24")
 * @returns {string} - Formatted IP range (e.g., "192.168.1.0 - 192.168.1.255") or single IP for /32
 * 
 * Examples:
 * - "10.0.0.1/32" → "10.0.0.1"
 * - "192.168.1.0/24" → "192.168.1.0 - 192.168.1.255"
 * - "172.16.0.0/16" → "172.16.0.0 - 172.16.255.255"
 * - "0.0.0.0/0" → "0.0.0.0 - 255.255.255.255"
 */
export function formatCidrToRange(cidr) {
  if (!cidr || typeof cidr !== 'string') {
    return cidr || ''
  }

  try {
    // Check if it's already in range format (contains " - ")
    if (cidr.includes(' - ')) {
      return cidr
    }

    // Check if it contains CIDR notation (has /)
    if (!cidr.includes('/')) {
      // No prefix, treat as single IP
      return cidr
    }

    const [ipStr, prefixStr] = cidr.split('/')
    const prefix = parseInt(prefixStr, 10)

    // Validate prefix
    if (isNaN(prefix) || prefix < 0 || prefix > 32) {
      return cidr // Invalid prefix, return original
    }

    // Parse IP address
    const ipParts = ipStr.split('.').map(Number)
    if (ipParts.length !== 4 || ipParts.some(isNaN) || ipParts.some(p => p < 0 || p > 255)) {
      return cidr // Invalid IP, return original
    }

    // Single IP (/32)
    if (prefix === 32) {
      return ipStr
    }

    // Calculate network address (first IP)
    const hostBits = 32 - prefix
    const hostMask = (1 << hostBits) - 1
    const networkMask = 0xFFFFFFFF & (~hostMask)

    // Convert IP to 32-bit integer
    const ipInt = (ipParts[0] << 24) | (ipParts[1] << 16) | (ipParts[2] << 8) | ipParts[3]
    
    // Calculate network address
    const networkInt = ipInt & networkMask
    
    // Calculate broadcast address (last IP)
    const broadcastInt = networkInt | hostMask

    // Convert back to IP address strings
    const networkIP = [
      (networkInt >>> 24) & 0xFF,
      (networkInt >>> 16) & 0xFF,
      (networkInt >>> 8) & 0xFF,
      networkInt & 0xFF
    ].join('.')

    const broadcastIP = [
      (broadcastInt >>> 24) & 0xFF,
      (broadcastInt >>> 16) & 0xFF,
      (broadcastInt >>> 8) & 0xFF,
      broadcastInt & 0xFF
    ].join('.')

    // Return range format
    return `${networkIP} - ${broadcastIP}`
  } catch (error) {
    // If any error occurs, return original CIDR
    console.warn('Error formatting CIDR to range:', error, cidr)
    return cidr
  }
}

/**
 * Check if a string is a valid CIDR notation
 * 
 * @param {string} cidr - String to check
 * @returns {boolean} - True if valid CIDR notation
 */
export function isValidCidr(cidr) {
  if (!cidr || typeof cidr !== 'string') {
    return false
  }

  try {
    const [ipStr, prefixStr] = cidr.split('/')
    if (!ipStr || !prefixStr) {
      return false
    }

    const prefix = parseInt(prefixStr, 10)
    if (isNaN(prefix) || prefix < 0 || prefix > 32) {
      return false
    }

    const ipParts = ipStr.split('.').map(Number)
    if (ipParts.length !== 4) {
      return false
    }

    return ipParts.every(p => !isNaN(p) && p >= 0 && p <= 255)
  } catch {
    return false
  }
}

/**
 * Validate IPv4 address format
 * @param {string} ip - IP address to validate
 * @returns {boolean} - True if valid IPv4 format
 */
function isValidIPv4(ip) {
  if (!ip || typeof ip !== 'string') return false
  
  // Regex pattern for IPv4: 4 octets separated by dots, each 0-255
  const ipv4Pattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/
  const match = ip.trim().match(ipv4Pattern)
  
  if (!match) return false
  
  // Validate each octet is 0-255
  for (let i = 1; i <= 4; i++) {
    const octet = parseInt(match[i], 10)
    if (octet < 0 || octet > 255) {
      return false
    }
  }
  
  return true
}

/**
 * Extract base IP address from CIDR notation
 * 
 * @param {string} cidr - CIDR notation (e.g., "192.168.1.0/24") or IP with unexpected characters
 * @returns {string} - Base IP address (e.g., "192.168.1.0") or empty string if invalid
 * 
 * Examples:
 * - "192.168.1.0/24" → "192.168.1.0"
 * - "10.0.0.1/32" → "10.0.0.1"
 * - "172.16.0.0/16" → "172.16.0.0"
 * - "192.168.1.5" → "192.168.1.5" (no CIDR notation, return as-is)
 * - "10.177.56.206:1" → "10.177.56.206" (strip trailing colon and characters)
 * - "10.177.56.206:1/24" → "10.177.56.206" (extract IP before colon, then validate)
 */
export function extractBaseIpFromCidr(cidr) {
  if (!cidr || typeof cidr !== 'string') {
    return ''
  }

  try {
    let cleaned = cidr.trim()
    
    // If it contains '/', extract IP part before the '/'
    if (cleaned.includes('/')) {
      cleaned = cleaned.split('/')[0].trim()
    }
    
    // If it contains ':', extract IP part before the ':' (handles cases like "10.177.56.206:1")
    if (cleaned.includes(':')) {
      // Check if it's IPv4 format (contains dots) - if so, split on colon
      if (cleaned.includes('.')) {
        cleaned = cleaned.split(':')[0].trim()
      }
      // For IPv6, we'd need more complex logic, but for now just take first part
      // This handles edge cases where colon might be part of the data
    }
    
    // Extract IP using regex pattern (4 octets separated by dots)
    const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}/
    const match = cleaned.match(ipv4Pattern)
    
    if (match) {
      const extractedIp = match[0]
      // Validate the extracted IP
      if (isValidIPv4(extractedIp)) {
        return extractedIp
      }
    }
    
    // If no pattern match or invalid, try validating the cleaned string directly
    if (isValidIPv4(cleaned)) {
      return cleaned
    }
    
    // If all else fails, return empty string (invalid IP)
    console.warn('Invalid IP format extracted from CIDR:', cidr, '→', cleaned)
    return ''
  } catch (error) {
    console.warn('Error extracting base IP from CIDR:', error, cidr)
    return ''
  }
}

