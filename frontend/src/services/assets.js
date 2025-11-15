import apiClient from './api'

export const assetsService = {
  // Search/filter assets with pagination
  searchAssets(filters = {}) {
    const {
      ip_address,
      ip_range,
      segment,
      vlan,
      os_name,
      environment,
      hostname,
      is_active = true,
      limit = 100,
      offset = 0,
    } = filters

    return apiClient.get('/api/v1/assets', {
      params: {
        ip_address,
        ip_range,
        segment,
        vlan,
        os_name,
        environment,
        hostname,
        is_active,
        limit,
        offset,
      },
    })
  },

  // Get single asset by IP (full details)
  getAssetByIp(ipAddress) {
    return apiClient.get(`/api/v1/assets/${encodeURIComponent(ipAddress)}`)
  },

  // Upload CSV file (ONLY way to create assets)
  uploadCSV(file, uploadedBy = 'system') {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.post('/api/v1/assets/upload-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: {
        uploaded_by: uploadedBy,
      },
    })
  },

  // List upload batches
  getUploadBatches(limit = 50, offset = 0) {
    return apiClient.get('/api/v1/assets/upload-batches', {
      params: {
        limit,
        offset,
      },
    })
  },

  // Get batch details
  getUploadBatch(batchId) {
    return apiClient.get(`/api/v1/assets/upload-batches/${batchId}`)
  },

  // Get asset analytics
  getAnalytics() {
    return apiClient.get('/api/v1/assets/analytics')
  },

  // Get filter options (unique values for dropdowns)
  getFilterOptions() {
    return apiClient.get('/api/v1/assets/filter-options')
  },
}

