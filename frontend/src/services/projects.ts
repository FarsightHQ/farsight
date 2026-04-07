import apiClient from './api'

export const projectsService = {
  list() {
    return apiClient.get('/api/v1/projects')
  },

  create(payload) {
    return apiClient.post('/api/v1/projects', payload)
  },

  get(id) {
    return apiClient.get(`/api/v1/projects/${id}`)
  },

  update(id, payload) {
    return apiClient.patch(`/api/v1/projects/${id}`, payload)
  },

  listMembers(projectId) {
    return apiClient.get(`/api/v1/projects/${projectId}/members`)
  },

  addMember(projectId, body) {
    return apiClient.post(`/api/v1/projects/${projectId}/members`, body)
  },

  removeMember(projectId, userSub) {
    const enc = encodeURIComponent(userSub).replace(
      /[!'()*]/g,
      c => `%${c.charCodeAt(0).toString(16).toUpperCase()}`
    )
    return apiClient.delete(`/api/v1/projects/${projectId}/members/${enc}`)
  },

  createInvitation(projectId, body) {
    return apiClient.post(`/api/v1/projects/${projectId}/invitations`, body)
  },

  acceptInvitation(token) {
    return apiClient.post('/api/v1/invitations/accept', { token })
  },
}
