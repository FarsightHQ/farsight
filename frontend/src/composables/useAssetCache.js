import { ref, reactive } from 'vue'
import { assetsService } from '@/services/assets'
import { extractBaseIpFromCidr } from '@/utils/ipUtils'

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
 * Composable for managing asset information cache
 * Fetches and caches asset data by IP address to avoid duplicate API calls
 */
export function useAssetCache() {
  // Cache: Map of IP address -> asset data
  const cache = reactive(new Map())
  
  // Track pending requests to avoid duplicate concurrent requests
  const pendingRequests = reactive(new Map())
  
  // Reactive version counter to trigger UI updates when cache changes
  const cacheVersion = ref(0)
  
  /**
   * Fetch asset information for a single IP address
   * @param {string} ipAddress - IP address to look up
   * @returns {Promise<Object|null>} - Asset object or null if not found
   */
  const fetchAsset = async (ipAddress) => {
    if (!ipAddress) return null
    
      // Validate IP format before making API call
      if (!isValidIPv4(ipAddress)) {
        console.warn(`Invalid IP format, skipping API call: ${ipAddress}`)
        // Cache null to avoid retrying invalid IPs
        cache.set(ipAddress, null)
        // Increment version to trigger reactivity
        cacheVersion.value++
        return null
      }
    
    // Check cache first
    if (cache.has(ipAddress)) {
      return cache.get(ipAddress)
    }
    
    // Check if request is already pending
    if (pendingRequests.has(ipAddress)) {
      return pendingRequests.get(ipAddress)
    }
    
    // Create new request
    const requestPromise = assetsService
      .getAssetByIp(ipAddress)
      .then((response) => {
        // Handle API response format
        const assetData = response.data?.data || response.data || null
        
        if (assetData) {
          // Store in cache
          cache.set(ipAddress, assetData)
          // Increment version to trigger reactivity
          cacheVersion.value++
        } else {
          // Cache null to avoid retrying failed lookups
          cache.set(ipAddress, null)
          // Increment version to trigger reactivity
          cacheVersion.value++
        }
        
        return assetData
      })
      .catch((error) => {
        // Handle errors gracefully
        console.warn(`Failed to fetch asset for IP ${ipAddress}:`, error)
        // Cache null to avoid retrying failed lookups
        cache.set(ipAddress, null)
        // Increment version to trigger reactivity
        cacheVersion.value++
        return null
      })
      .finally(() => {
        // Remove from pending requests
        pendingRequests.delete(ipAddress)
      })
    
    // Store pending request
    pendingRequests.set(ipAddress, requestPromise)
    
    return requestPromise
  }
  
  /**
   * Extract unique IP addresses from endpoints and fetch asset info for each
   * @param {Array} endpoints - Array of endpoint objects with network_cidr
   * @returns {Promise<Map>} - Map of IP address -> asset data
   */
  const fetchAssetsForEndpoints = async (endpoints) => {
    if (!endpoints || !Array.isArray(endpoints)) {
      return new Map()
    }
    
    // Extract unique base IPs from endpoints
    const uniqueIPs = new Set()
    endpoints.forEach((ep) => {
      const cidr = ep.network_cidr || ep.cidr
      if (cidr) {
        const baseIp = extractBaseIpFromCidr(cidr)
        if (baseIp) {
          uniqueIPs.add(baseIp)
        }
      }
    })
    
    // Fetch asset info for all unique IPs (in parallel)
    const fetchPromises = Array.from(uniqueIPs).map((ip) => fetchAsset(ip))
    await Promise.all(fetchPromises)
    
    // Return map of IP -> asset data
    const result = new Map()
    uniqueIPs.forEach((ip) => {
      const asset = cache.get(ip)
      if (asset) {
        result.set(ip, asset)
      }
    })
    
    return result
  }
  
  /**
   * Get asset from cache (without fetching)
   * @param {string} ipAddress - IP address to look up
   * @returns {Object|null} - Cached asset data or null
   */
  const getCachedAsset = (ipAddress) => {
    if (!ipAddress) return null
    return cache.get(ipAddress) || null
  }
  
  /**
   * Get asset for a CIDR (extracts base IP first)
   * @param {string} cidr - CIDR notation
   * @returns {Object|null} - Asset data or null
   */
  const getAssetForCidr = (cidr) => {
    if (!cidr) return null
    const baseIp = extractBaseIpFromCidr(cidr)
    return getCachedAsset(baseIp)
  }
  
  /**
   * Clear the cache
   */
  const clearCache = () => {
    cache.clear()
    pendingRequests.clear()
  }
  
  return {
    cache,
    cacheVersion,
    fetchAsset,
    fetchAssetsForEndpoints,
    getCachedAsset,
    getAssetForCidr,
    clearCache,
  }
}

