import apiClient from './api'

export const registryAssetsService = {
  search(params = {}) {
    return apiClient.get('/api/v1/registry/assets', { params })
  },

  getByIp(ipAddress) {
    return apiClient.get(`/api/v1/registry/assets/${encodeURIComponent(ipAddress)}`)
  },

  linkedProjects(ipAddress) {
    return apiClient.get(`/api/v1/registry/assets/${encodeURIComponent(ipAddress)}/projects`)
  },
}
