/**
 * Merge unified_graph payloads from multiple rule detail API responses.
 * Nodes dedupe by network_cidr; links merge by (source node id, target node id).
 */

function serviceKey(s) {
  return `${s.protocol || ''}|${s.port_ranges || ''}`
}

export function mergeUnifiedGraphData(responses) {
  const nodeByCidr = new Map()
  const linkMap = new Map()

  for (const response of responses) {
    const data = response.data?.data || response.data || response
    const ug = data.unified_graph
    if (!ug?.nodes?.length) continue

    for (const n of ug.nodes) {
      const cidr = n.network_cidr
      if (!cidr) continue
      if (!nodeByCidr.has(cidr)) {
        nodeByCidr.set(cidr, { ...n })
      } else {
        const ex = nodeByCidr.get(cidr)
        ex.asset = ex.asset || n.asset
        ex.segment = ex.segment || n.segment
        ex.vlan = ex.vlan || n.vlan
        ex.environment = ex.environment || n.environment
        ex.location = ex.location || n.location
      }
    }

    for (const l of ug.links || []) {
      const k = `${l.source}|${l.target}`
      if (!linkMap.has(k)) {
        linkMap.set(k, {
          source: l.source,
          target: l.target,
          type: l.type || 'traffic_flow',
          rule_ids: [...(l.rule_ids || [])],
          rules: [...(l.rules || [])],
          services: [...(l.services || [])],
          label: l.label,
        })
      } else {
        const ex = linkMap.get(k)
        const rid = new Set(ex.rule_ids)
        for (const r of l.rule_ids || []) rid.add(r)
        ex.rule_ids = [...rid].sort((a, b) => a - b)

        const seenRules = new Set((ex.rules || []).map((r) => r.id))
        for (const r of l.rules || []) {
          if (r && !seenRules.has(r.id)) {
            seenRules.add(r.id)
            ex.rules.push(r)
          }
        }

        const sk = new Set((ex.services || []).map(serviceKey))
        for (const s of l.services || []) {
          const key = serviceKey(s)
          if (!sk.has(key)) {
            sk.add(key)
            ex.services.push(s)
          }
        }
        ex.label =
          ex.rule_ids.length > 1 ? `Rules ${ex.rule_ids.join(', ')}` : `Rule ${ex.rule_ids[0]}`
      }
    }
  }

  const nodes = [...nodeByCidr.values()]
  const links = [...linkMap.values()]

  const ruleIdSet = new Set()
  for (const l of links) {
    for (const rid of l.rule_ids || []) ruleIdSet.add(rid)
  }

  return {
    nodes,
    links,
    metadata: {
      schema_version: 1,
      node_count: nodes.length,
      link_count: links.length,
      rule_count: ruleIdSet.size,
    },
  }
}

export function extractUnifiedGraphFromRuleResponse(response) {
  const data = response.data?.data || response.data || response
  return data.unified_graph || null
}
