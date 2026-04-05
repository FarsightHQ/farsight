/** Resolve D3-sim link endpoint ids (strings or node objects). */
export function linkEndpointIds(d) {
  return {
    sourceId: typeof d.source === 'object' ? d.source.id : d.source,
    targetId: typeof d.target === 'object' ? d.target.id : d.target,
  }
}

export function linkKeyFromSim(d) {
  const { sourceId, targetId } = linkEndpointIds(d)
  return `${sourceId}->${targetId}`
}

export function linkCrossSegment(d, segById) {
  const { sourceId, targetId } = linkEndpointIds(d)
  const a = segById.get(sourceId) || 'Unknown'
  const b = segById.get(targetId) || 'Unknown'
  return a !== b
}

export function neighborIds(selId, linkData) {
  const set = new Set([selId])
  for (const l of linkData) {
    const { sourceId, targetId } = linkEndpointIds(l)
    if (sourceId === selId) set.add(targetId)
    if (targetId === selId) set.add(sourceId)
  }
  return set
}

/** Cubic Bézier along chord with perpendicular bend (for force-graph edges). */
export function curvedLinkPath(d) {
  const sx = d.source.x
  const sy = d.source.y
  const tx = d.target.x
  const ty = d.target.y
  const dx = tx - sx
  const dy = ty - sy
  const dist = Math.hypot(dx, dy) || 1
  const nx = -dy / dist
  const ny = dx / dist
  const bend = dist * 0.22 * (d._curveSide || 1)
  const c1x = sx + dx * 0.32 + nx * bend
  const c1y = sy + dy * 0.32 + ny * bend
  const c2x = sx + dx * 0.68 + nx * bend
  const c2y = sy + dy * 0.68 + ny * bend
  return `M${sx},${sy} C${c1x},${c1y} ${c2x},${c2y} ${tx},${ty}`
}
