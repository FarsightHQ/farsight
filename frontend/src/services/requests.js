import apiClient from './api'
import { getActiveProjectId } from '../utils/projectContext'

function projectFarBase() {
  const id = getActiveProjectId()
  if (!id) {
    throw new Error('No project selected. Choose a project in the header or open Projects.')
  }
  return `/api/v1/projects/${id}/far`
}

export const requestsService = {
  list(skip = 0, limit = 100) {
    return apiClient.get(projectFarBase(), {
      params: { skip, limit },
    })
  },

  get(id) {
    return apiClient.get(`${projectFarBase()}/${id}`)
  },

  create(title, file, externalId = null) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('title', title)
    if (externalId) {
      formData.append('external_id', externalId)
    }

    return apiClient.post(projectFarBase(), formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  ingest(id) {
    return apiClient.post(`${projectFarBase()}/${id}/ingest`)
  },

  computeFacts(id) {
    return apiClient.post(`${projectFarBase()}/${id}/facts/compute`)
  },

  computeHybridFacts(id) {
    return apiClient.post(`${projectFarBase()}/${id}/facts/compute-hybrid`)
  },

  delete(id) {
    return apiClient.delete(`${projectFarBase()}/${id}`)
  },

  getNetworkTopology(id) {
    return apiClient.get(`${projectFarBase()}/${id}/network-topology`)
  },

  getRuleGraph(ruleId) {
    const id = getActiveProjectId()
    if (!id) {
      throw new Error('No project selected. Choose a project in the header or open Projects.')
    }
    return apiClient.get(`/api/v1/projects/${id}/rules/${ruleId}`, {
      params: { include: 'graph' },
    })
  },

  getAllRules(params = {}) {
    const id = getActiveProjectId()
    if (!id) {
      throw new Error('No project selected. Choose a project in the header or open Projects.')
    }
    return apiClient.get(`/api/v1/projects/${id}/rules`, {
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
