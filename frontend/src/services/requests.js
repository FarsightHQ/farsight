import apiClient from './api'

export const requestsService = {
  // List all requests
  list(skip = 0, limit = 100) {
    return apiClient.get('/api/v1/far', {
      params: { skip, limit },
    })
  },

  // Get request by ID
  get(id) {
    return apiClient.get(`/api/v1/far/${id}`)
  },

  // Create new request
  create(title, file, externalId = null) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', title)
    if (externalId) {
      formData.append('external_id', externalId)
    }

    return apiClient.post('/api/v1/far', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // Process CSV ingestion
  ingest(id) {
    return apiClient.post(`/api/v1/far/${id}/ingest`)
  },

  // Compute facts
  computeFacts(id) {
    return apiClient.post(`/api/v1/far/${id}/facts/compute`)
  },

  // Compute hybrid facts
  computeHybridFacts(id) {
    return apiClient.post(`/api/v1/far/${id}/facts/compute-hybrid`)
  },

  // Delete request
  delete(id) {
    return apiClient.delete(`/api/v1/far/${id}`)
  },

  // Get network topology for visualization
  getNetworkTopology(id) {
    return apiClient.get(`/api/v1/analysis/${id}/network-topology`)
  },

  // Get network graph for a single rule
  getRuleGraph(ruleId) {
    return apiClient.get(`/api/v1/rules/${ruleId}`, {
      params: { include: 'graph' },
    })
  },

  // Get all rules across all requests (or filtered by request_id)
  getAllRules(params = {}) {
    return apiClient.get('/api/v1/rules', {
      params: {
        skip: params.skip || 0,
        limit: params.limit || 100,
        request_id: params.request_id || undefined,
        action: params.action || undefined,
        include_summary: params.include_summary !== false,
      },
    })
  },
}
