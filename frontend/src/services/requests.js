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
}

