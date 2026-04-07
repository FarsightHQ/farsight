/**
 * Build directed zone adjacency matrices from unified_graph (nodes + links).
 * Zones come from asset-enriched node fields: segment, location, or vlan.
 */

export const ZONE_GROUP_BY = /** @type {const} */ (['segment', 'location', 'vlan'])

export const ZONE_METRIC = /** @type {const} */ (['rules', 'services', 'binary'])

/** @param {Record<string, unknown>|null|undefined} node */
/** @param {'segment'|'location'|'vlan'} groupBy */
export function pickZone(node, groupBy) {
  if (!node) return 'Unknown'
  if (groupBy === 'segment') {
    const v = node.segment
    return v != null && String(v).trim() !== '' ? String(v) : 'Unknown'
  }
  if (groupBy === 'location') {
    const v = node.location
    return v != null && String(v).trim() !== '' ? String(v) : 'Unknown'
  }
  if (groupBy === 'vlan') {
    const v = node.vlan
    return v != null && String(v).trim() !== '' ? String(v) : 'Unknown'
  }
  return 'Unknown'
}

function serviceDedupeKey(s) {
  return `${s?.protocol ?? ''}\u0001${s?.port_ranges ?? ''}`
}

/**
 * @param {{ nodes?: Array<{ id?: string, segment?: string|null, location?: string|null, vlan?: string|null }>, links?: Array<{ source: string, target: string, rule_ids?: number[], services?: Array<{ protocol?: string, port_ranges?: string, formatted_ports?: string }> }> }|null|undefined} unifiedGraph
 * @param {{ groupBy?: 'segment'|'location'|'vlan', metric?: 'rules'|'services'|'binary' }} options
 */
export function buildZoneAdjacencyMatrix(unifiedGraph, options = {}) {
  const groupBy = options.groupBy ?? 'segment'
  const metric = options.metric ?? 'rules'

  const nodes = unifiedGraph?.nodes ?? []
  const links = unifiedGraph?.links ?? []

  const byId = new Map()
  for (const n of nodes) {
    if (n?.id != null) byId.set(String(n.id), n)
  }

  /** @type {Map<string, { ruleIds: Set<number>, serviceKeys: Set<string>, servicesList: Array<{protocol?: string, port_ranges?: string, formatted_ports?: string}>, linkCount: number }>} */
  const cellMap = new Map()

  for (const link of links) {
    const srcNode = byId.get(String(link.source))
    const tgtNode = byId.get(String(link.target))
    if (!srcNode || !tgtNode) continue

    const row = pickZone(srcNode, groupBy)
    const col = pickZone(tgtNode, groupBy)
    const cellKey = `${row}\u0000${col}`

    let agg = cellMap.get(cellKey)
    if (!agg) {
      agg = {
        ruleIds: new Set(),
        serviceKeys: new Set(),
        servicesList: [],
        linkCount: 0,
      }
      cellMap.set(cellKey, agg)
    }
    agg.linkCount += 1

    for (const rid of link.rule_ids ?? []) {
      const n = Number(rid)
      if (!Number.isNaN(n)) agg.ruleIds.add(n)
    }

    for (const s of link.services ?? []) {
      const sk = serviceDedupeKey(s)
      if (!agg.serviceKeys.has(sk)) {
        agg.serviceKeys.add(sk)
        agg.servicesList.push({
          protocol: s.protocol,
          port_ranges: s.port_ranges,
          formatted_ports: s.formatted_ports,
        })
      }
    }
  }

  const zoneSet = new Set()
  for (const key of cellMap.keys()) {
    const [r, c] = key.split('\u0000')
    zoneSet.add(r)
    zoneSet.add(c)
  }
  const labels = [...zoneSet].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }))
  const n = labels.length
  const labelIndex = Object.fromEntries(labels.map((l, i) => [l, i]))

  const matrix = Array.from({ length: n }, () => Array(n).fill(null))
  const cellDetail = Array.from({ length: n }, () => Array(n).fill(null))

  let maxValue = 0

  for (const [cellKey, agg] of cellMap) {
    const [rowLabel, colLabel] = cellKey.split('\u0000')
    const i = labelIndex[rowLabel]
    const j = labelIndex[colLabel]
    if (i === undefined || j === undefined) continue

    const ruleIds = [...agg.ruleIds].sort((a, b) => a - b)

    let value
    if (metric === 'binary') {
      value = 1
    } else if (metric === 'rules') {
      value = ruleIds.length
    } else {
      value = agg.serviceKeys.size
    }

    if (value != null && value > maxValue) maxValue = value

    matrix[i][j] = value
    cellDetail[i][j] = {
      rowLabel,
      colLabel,
      ruleIds,
      linkCount: agg.linkCount,
      services: agg.servicesList,
    }
  }

  return {
    rowLabels: labels,
    colLabels: labels,
    matrix,
    cellDetail,
    maxValue,
    groupBy,
    metric,
    nonEmptyCellCount: cellMap.size,
  }
}
