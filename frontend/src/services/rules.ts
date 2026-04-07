import apiClient from './api'
import { getActiveProjectId } from '../utils/projectContext'

function projectFarBase() {
  const id = getActiveProjectId()
  if (!id) {
    throw new Error('No project selected. Choose a project in the header or open Projects.')
  }
  return `/api/v1/projects/${id}/far`
}

function projectRulesBase() {
  const id = getActiveProjectId()
  if (!id) {
    throw new Error('No project selected. Choose a project in the header or open Projects.')
  }
  return `/api/v1/projects/${id}/rules`
}

export const rulesService = {
  getRules(
    requestId: string | number,
    params: { skip?: number; limit?: number; include_summary?: boolean } = {}
  ) {
    const { skip = 0, limit = 100, include_summary = true } = params
    return apiClient.get(`${projectFarBase()}/${requestId}/rules`, {
      params: {
        skip,
        limit,
        include_summary,
      },
    })
  },

  getRule(ruleId: string | number, options: { format?: string; include?: string } = {}) {
    const { format, include } = options
    const params: Record<string, string> = {}
    if (format) params.format = format
    if (include) params.include = include
    return apiClient.get(`${projectRulesBase()}/${ruleId}`, { params })
  },

  getRuleFacts(ruleId) {
    return apiClient.get(`${projectRulesBase()}/${ruleId}`, {
      params: { include: 'analysis' },
    })
  },

  searchRules(requestId, query, params = {}) {
    return this.getRules(requestId, { ...params, limit: 1000 })
  },
}
