import * as d3 from 'd3'
import { vlanGroupKey, LAYOUT_SEP, sortVlanIds } from '@/utils/unifiedGraphKeys'

/**
 * Coarse grid of target positions, pulled toward canvas center.
 * @param {string[]} ids - domain keys (segment names, VLAN ids, etc.)
 */
export function clusterCenters(ids, width, height, tighten = 0.66) {
  const n = Math.max(1, ids.length)
  const cols = Math.ceil(Math.sqrt(n))
  const rows = Math.ceil(n / cols)
  const cx = width / 2
  const cy = height / 2
  const map = {}
  ids.forEach((id, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    const bx = ((col + 0.5) / cols) * width
    const by = ((row + 0.5) / rows) * height
    map[id] = {
      x: cx + (bx - cx) * tighten,
      y: cy + (by - cy) * tighten,
    }
  })
  return map
}

const DEFAULT_VLAN_TIGHTEN = 0.56
const DEFAULT_SUB_SPACING = 58

/**
 * VLAN coarse grid + per-VLAN mini-grid for each segment.
 * @returns {Record<string, { x: number, y: number }>} keyed by nodeLayoutKey string
 */
export function hierarchicalClusterTargets(
  rawNodes,
  width,
  height,
  options: { vlanTighten?: number; subSpacing?: number } = {}
) {
  const vlanTighten = options.vlanTighten ?? DEFAULT_VLAN_TIGHTEN
  const subSpacing = options.subSpacing ?? DEFAULT_SUB_SPACING

  const byVlan = d3.group(rawNodes, vlanGroupKey)
  const vlans = [...byVlan.keys()].sort(sortVlanIds)
  const vlanCenters = clusterCenters(vlans, width, height, vlanTighten)
  const targets = {}

  for (const V of vlans) {
    const inVlan = byVlan.get(V) || []
    const segs = [...new Set(inVlan.map(n => n.segment || 'Unknown'))].sort()
    const nSeg = segs.length
    const cols = Math.ceil(Math.sqrt(nSeg))
    const rows = Math.ceil(nSeg / cols)
    const vc = vlanCenters[V] || { x: width / 2, y: height / 2 }
    segs.forEach((seg, i) => {
      const col = i % cols
      const row = Math.floor(i / cols)
      const ox = (col - (cols - 1) / 2) * subSpacing
      const oy = (row - (rows - 1) / 2) * subSpacing
      targets[`${V}${LAYOUT_SEP}${seg}`] = { x: vc.x + ox, y: vc.y + oy }
    })
  }

  return targets
}
