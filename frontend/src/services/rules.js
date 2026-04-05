import apiClient from './api'

export const rulesService = {
  // Get rules for a request with pagination and filtering
  getRules(requestId, params = {}) {
    const { skip = 0, limit = 100, include_summary = true } = params
    return apiClient.get(`/api/v1/far/${requestId}/rules`, {
      params: {
        skip,
        limit,
        include_summary,
      },
    })
  },

  // Get single rule details
  getRule(ruleId, options = {}) {
    const { format, include } = options
    const params = {}
    if (format) params.format = format
    if (include) params.include = include
    return apiClient.get(`/api/v1/rules/${ruleId}`, { params })
  },

  // Get rule facts (extracted from rule details)
  getRuleFacts(ruleId) {
    return apiClient.get(`/api/v1/rules/${ruleId}`, {
      params: { include: 'analysis' },
    })
  },

  // Search rules (client-side filtering for now)
  // This could be enhanced with backend search endpoint if available
  searchRules(requestId, query, params = {}) {
    // For now, fetch all rules and filter client-side
    // In future, this could use a dedicated search endpoint
    return this.getRules(requestId, { ...params, limit: 1000 })
  },
}
