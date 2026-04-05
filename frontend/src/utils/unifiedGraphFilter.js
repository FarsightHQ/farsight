/**
 * Shared filtering for unified topology (text search + optional segment focus).
 * Segment focus: nodes in segment S plus one-hop neighbors (within the text-filtered set).
 */

export function filterUnifiedGraph(graph, { filterText = '', segmentFocus = '' } = {}) {
  const rawNodes = graph?.nodes || []
  const rawLinks = graph?.links || []
  const q = String(filterText || '')
    .trim()
    .toLowerCase()

  let nodes = rawNodes.filter(n => {
    if (!q) return true
    const hay = [
      n.network_cidr,
      n.label,
      n.segment,
      n.vlan,
      n.environment,
      n.location,
      n.asset?.hostname,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return hay.includes(q)
  })

  const focus = String(segmentFocus || '').trim()
  if (focus) {
    const allowed = new Set(nodes.map(n => n.id))
    const core = new Set(nodes.filter(n => (n.segment || 'Unknown') === focus).map(n => n.id))
    if (core.size === 0) {
      nodes = []
    } else {
      const keep = new Set(core)
      for (const l of rawLinks) {
        const s = l.source
        const t = l.target
        if (core.has(s) && allowed.has(t)) keep.add(t)
        if (core.has(t) && allowed.has(s)) keep.add(s)
      }
      nodes = nodes.filter(n => keep.has(n.id))
    }
  }

  const idSet = new Set(nodes.map(d => d.id))
  const links = rawLinks.filter(l => idSet.has(l.source) && idSet.has(l.target))
  return { nodes, links }
}

export function countCrossSegmentLinks(nodes, links) {
  const byId = new Map(nodes.map(n => [n.id, n]))
  let c = 0
  for (const l of links) {
    const a = byId.get(l.source)
    const b = byId.get(l.target)
    if (!a || !b) continue
    const sa = a.segment || 'Unknown'
    const sb = b.segment || 'Unknown'
    if (sa !== sb) c += 1
  }
  return c
}

export function unifiedLinkKey(l) {
  const s = typeof l.source === 'object' ? l.source.id : l.source
  const t = typeof l.target === 'object' ? l.target.id : l.target
  return `${s}->${t}`
}
