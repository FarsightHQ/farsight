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

