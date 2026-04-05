import * as d3 from 'd3'
import { vlanGroupKey, VLAN_NONE_KEY, nodeLayoutKey, sortVlanIds } from '@/utils/unifiedGraphKeys'

/** Reused for every hull rebuild (avoid reallocating line generators). */
const LINE_CLOSED_SMOOTH = d3.line().curve(d3.curveCatmullRomClosed.alpha(0.72))

export function buildSegmentColorScale(segments) {
  const scale = d3.scaleOrdinal(d3.schemeTableau10).domain(segments)
  return seg => scale(seg || 'Unknown')
}

export function buildVlanColorScale(vlanIds) {
  const scheme = d3.schemeObservable10.concat(d3.schemeSet3)
  return d3.scaleOrdinal(scheme).domain(vlanIds)
}

function expandHullFromCentroid(hull, pad) {
  let cx = 0
  let cy = 0
  for (const [x, y] of hull) {
    cx += x
    cy += y
  }
  cx /= hull.length
  cy /= hull.length
  return hull.map(([x, y]) => {
    const dx = x - cx
    const dy = y - cy
    const len = Math.hypot(dx, dy) || 1
    return [x + (dx / len) * pad, y + (dy / len) * pad]
  })
}

function bboxPolygonPad(xy, pad) {
  const xs = xy.map(p => p[0])
  const ys = xy.map(p => p[1])
  return [
    [Math.min(...xs) - pad, Math.min(...ys) - pad],
    [Math.max(...xs) + pad, Math.min(...ys) - pad],
    [Math.max(...xs) + pad, Math.max(...ys) + pad],
    [Math.min(...xs) - pad, Math.max(...ys) + pad],
  ]
}

export function circlePath(cx, cy, r) {
  return `M ${cx - r},${cy} A ${r},${r} 0 1,1 ${cx + r},${cy} A ${r},${r} 0 1,1 ${cx - r},${cy}`
}

/**
 * @param {Array<{x:number,y:number}>} pts
 * @param {number} pad
 * @param {number} singleRadius - circle radius when pts.length === 1
 * @returns {{ pathD: string, cx: number, cy: number } | null}
 */
function smoothOutlineFromPoints(pts, pad, singleRadius) {
  if (pts.length === 0) return null
  const xy = pts.map(p => [p.x, p.y])
  const cx = d3.mean(pts, p => p.x)
  const cy = d3.mean(pts, p => p.y)

  if (pts.length === 1) {
    return { pathD: circlePath(xy[0][0], xy[0][1], singleRadius), cx, cy }
  }

  let ring = null
  if (pts.length >= 3) {
    const hull = d3.polygonHull(xy)
    if (hull && hull.length >= 3) {
      ring = expandHullFromCentroid(hull, pad)
    } else {
      ring = bboxPolygonPad(xy, pad)
    }
  } else {
    ring = bboxPolygonPad(xy, pad)
  }

  return { pathD: LINE_CLOSED_SMOOTH(ring), cx, cy }
}

const SEGMENT_HULL_PAD = 22
const SEGMENT_SINGLE_R = 34
const VLAN_HULL_PAD = 36
const VLAN_SINGLE_R = 44

/**
 * One hull per (VLAN × segment).
 */
export function buildSegmentOutlineEntries(nodeData) {
  const byLayout = d3.group(nodeData, nodeLayoutKey)
  const keys = [...byLayout.keys()].sort()

  return keys
    .map(layoutKey => {
      const pts = byLayout.get(layoutKey) || []
      if (pts.length === 0) return null
      const seg = pts[0].segment || 'Unknown'
      const geom = smoothOutlineFromPoints(pts, SEGMENT_HULL_PAD, SEGMENT_SINGLE_R)
      if (!geom) return null
      return { layoutKey, seg, pathD: geom.pathD, cx: geom.cx, cy: geom.cy }
    })
    .filter(Boolean)
}

/**
 * One hull per VLAN (asset VLAN id).
 */
export function buildVlanOutlineEntries(nodeData) {
  const byVlan = d3.group(nodeData, vlanGroupKey)
  const vlanIds = [...byVlan.keys()].sort(sortVlanIds)

  return vlanIds
    .map(vlanId => {
      const pts = byVlan.get(vlanId) || []
      if (pts.length === 0) return null
      const label = vlanId === VLAN_NONE_KEY ? 'No VLAN' : vlanId
      const geom = smoothOutlineFromPoints(pts, VLAN_HULL_PAD, VLAN_SINGLE_R)
      if (!geom) return null
      return { vlanId, label, pathD: geom.pathD, cx: geom.cx, cy: geom.cy }
    })
    .filter(Boolean)
}
