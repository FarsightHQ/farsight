import apiClient from './api'

export const assetsService = {
  /**
   * Get asset information by IP address
   * @param {string} ipAddress - IP address to look up
   * @returns {Promise} - Asset object with hostname, segment, vlan, os_name, etc.
   */
  getAssetByIp(ipAddress) {
    return apiClient.get(`/api/v1/assets/${encodeURIComponent(ipAddress)}`)
  },

  /**
   * Search assets with filters and pagination
   * @param {Object} params - Search parameters (ip_address, segment, vlan, os_name, environment, hostname, is_active, limit, offset)
   * @returns {Promise} - Paginated list of assets
   */
  searchAssets(params = {}) {
    return apiClient.get('/api/v1/assets', { params })
  },

  /**
   * Get asset analytics/statistics
   * @param {Object} params - Optional filter parameters
   * @returns {Promise} - Analytics data
   */
  getAnalytics(params = {}) {
    return apiClient.get('/api/v1/assets/analytics', { params })
  },

  /**
   * Get filter options for asset search
   * Note: This endpoint may not exist on the backend. If it doesn't, this will return an error.
   * The frontend should handle this gracefully by extracting options from search results.
   * @returns {Promise} - Available filter options (segments, vlans, os_names, etc.)
   */
  getFilterOptions() {
    return apiClient.get('/api/v1/assets/filter-options').catch((error) => {
      // If endpoint doesn't exist, return empty options
      if (error.response?.status === 404) {
        console.warn('Filter options endpoint not available, returning empty options')
        return {
          data: { segments: [], vlans: [], os_names: [], environments: [] },
        }
      }
      throw error
    })
  },
}

