/**
 * Merge multiple rule graph API responses into one graph for NetworkGraph (classic D3 view).
 * Deduplicates sources/destinations by network_cidr and remaps connection endpoints.
 *
 * @param {Array} responses - Raw responses from requestsService.getRuleGraph (axios-style)
 * @param {{ ruleCount: number }} options - Number of rules represented (for metadata.rule_count)
 * @returns {{ sources: Array, destinations: Array, connections: Array, metadata: object }}
 */
export function mergeRuleGraphResponses(responses, { ruleCount }) {
  const allSources = []
  const allDestinations = []
  const allConnections = []
  const sourceMap = new Map()
  const destMap = new Map()

  responses.forEach(response => {
    const data = response.data?.data || response.data || response
    const graph = data.graph || data

    if (!graph.sources || !graph.destinations) return

    graph.sources.forEach(src => {
      if (!sourceMap.has(src.network_cidr)) {
        sourceMap.set(src.network_cidr, {
          ...src,
          id: `src_merged_${sourceMap.size}`,
        })
        allSources.push(sourceMap.get(src.network_cidr))
      }
    })

    graph.destinations.forEach(dest => {
      if (!destMap.has(dest.network_cidr)) {
        destMap.set(dest.network_cidr, {
          ...dest,
          id: `dst_merged_${destMap.size}`,
          ports: [...(dest.ports || [])],
        })
        allDestinations.push(destMap.get(dest.network_cidr))
      } else {
        const existing = destMap.get(dest.network_cidr)
        if (dest.ports) {
          existing.ports.push(...dest.ports)
        }
      }
    })

    graph.connections?.forEach(conn => {
      const source = graph.sources.find(s => s.id === conn.source_id)
      const dest = graph.destinations.find(d => d.id === conn.destination_id)

      if (source && dest) {
        const mergedSource = sourceMap.get(source.network_cidr)
        const mergedDest = destMap.get(dest.network_cidr)

        if (mergedSource && mergedDest) {
          allConnections.push({
            source_id: mergedSource.id,
            destination_id: mergedDest.id,
            port_count: conn.port_count,
            services: conn.services,
          })
        }
      }
    })
  })

  return {
    sources: allSources,
    destinations: allDestinations,
    connections: allConnections,
    metadata: {
      rule_count: ruleCount,
      source_count: allSources.length,
      destination_count: allDestinations.length,
      connection_count: allConnections.length,
    },
  }
}
