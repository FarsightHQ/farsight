const DEFAULT_EMPTY_MESSAGE = 'This rule has no network topology data to visualize.'

/**
 * Unwrap axios-style or raw API response to the inner payload object.
 * @param {*} response
 * @returns {object}
 */
export function unwrapApiResponseData(response) {
  let data = response
  if (response?.data !== undefined) {
    data = response.data
    if (data?.data !== undefined) {
      data = data.data
    }
  }
  return data
}

/**
 * Normalize a getRuleGraph() response into NetworkGraph-ready graphData + summary.
 * Mirrors the rule branch of NetworkGraphModal.fetchTopology.
 *
 * @param {*} response - Raw API response
 * @param {string|number|null} ruleId - For error messages
 * @returns {{
 *   graphData: object | null,
 *   summary: object | null,
 *   error: string | null,
 *   emptyStateMessage: string
 * }}
 */
export function normalizeRuleGraphApiResponse(response, ruleId) {
  const rid = ruleId != null ? String(ruleId) : ''
  const responseData = unwrapApiResponseData(response)

  if (responseData.graph) {
    const graph = responseData.graph

    if (!graph.sources || !Array.isArray(graph.sources)) {
      return {
        graphData: null,
        summary: null,
        error: `Invalid graph data: missing sources array for rule ${rid}`,
        emptyStateMessage: 'Graph data structure is invalid (missing sources).',
      }
    }

    if (!graph.destinations || !Array.isArray(graph.destinations)) {
      return {
        graphData: null,
        summary: null,
        error: `Invalid graph data: missing destinations array for rule ${rid}`,
        emptyStateMessage: 'Graph data structure is invalid (missing destinations).',
      }
    }

    if (graph.sources.length === 0) {
      return {
        graphData: graph,
        summary: {
          rule_count: 1,
          source_count: 0,
          destination_count: graph.destinations.length || 0,
          service_count: graph.metadata?.service_count || graph.connections?.length || 0,
        },
        error: null,
        emptyStateMessage: 'This rule has no source networks to visualize.',
      }
    }

    if (graph.destinations.length === 0) {
      return {
        graphData: graph,
        summary: {
          rule_count: 1,
          source_count: graph.sources.length || 0,
          destination_count: 0,
          service_count: graph.metadata?.service_count || graph.connections?.length || 0,
        },
        error: null,
        emptyStateMessage: 'This rule has no destination networks to visualize.',
      }
    }

    return {
      graphData: graph,
      summary: {
        rule_count: 1,
        source_count: graph.metadata?.source_count || graph.sources.length || 0,
        destination_count: graph.metadata?.destination_count || graph.destinations.length || 0,
        service_count:
          graph.metadata?.service_count ||
          graph.connections?.reduce((sum, conn) => sum + (conn.port_count || 0), 0) ||
          0,
      },
      error: null,
      emptyStateMessage: DEFAULT_EMPTY_MESSAGE,
    }
  }

  if (responseData.topology) {
    return {
      graphData: responseData,
      summary: responseData.summary || {
        source_count: responseData.endpoints?.source_count || 0,
        destination_count: responseData.endpoints?.destination_count || 0,
        service_count: responseData.service_count || 0,
      },
      error: null,
      emptyStateMessage: DEFAULT_EMPTY_MESSAGE,
    }
  }

  if (
    responseData.sources &&
    Array.isArray(responseData.sources) &&
    responseData.destinations &&
    Array.isArray(responseData.destinations)
  ) {
    return {
      graphData: responseData,
      summary: {
        rule_count: 1,
        source_count: responseData.sources.length || 0,
        destination_count: responseData.destinations.length || 0,
        service_count:
          responseData.metadata?.service_count || responseData.connections?.length || 0,
      },
      error: null,
      emptyStateMessage: DEFAULT_EMPTY_MESSAGE,
    }
  }

  return {
    graphData: null,
    summary: null,
    error: `No graph data available for rule ${rid}. The rule may not have any endpoints or services.`,
    emptyStateMessage: 'This rule has no source or destination networks to visualize.',
  }
}
