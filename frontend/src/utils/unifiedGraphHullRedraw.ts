import * as d3 from 'd3'
import { VLAN_NONE_KEY } from '@/utils/unifiedGraphKeys'
import { buildSegmentOutlineEntries, buildVlanOutlineEntries } from '@/utils/unifiedGraphHulls'

/** Single translucent fill for every VLAN hull (no per-VLAN hue). */
const VLAN_HULL_FILL = 'rgba(226, 232, 240, 0.52)'

const VLAN_PILL_FILL = '#0f172a'
const VLAN_PILL_TEXT = '#f8fafc'
const VLAN_PILL_PAD_X = 7
const VLAN_PILL_PAD_Y = 4
const VLAN_PILL_RX = 6

function formatVlanLabelText(d) {
  const t = d.label.length > 36 ? `${d.label.slice(0, 34)}…` : d.label
  return d.vlanId === VLAN_NONE_KEY ? t : `VLAN ${t}`
}

export function redrawSegmentGrouping(hullG, labelG, nodeData, colorFn) {
  const entries = buildSegmentOutlineEntries(nodeData)
  const pathJoin = hullG
    .selectAll('path')
    .data(entries, d => d.layoutKey)
    .join('path')
    .attr('stroke-linejoin', 'round')
    .attr('stroke-linecap', 'round')
    .attr('stroke-width', 1.25)

  pathJoin.each(function (d) {
    const base = d3.color(colorFn(d.seg))
    const fillC = base ? base.copy({ opacity: 0.07 }) : d3.color('#94a3b8').copy({ opacity: 0.07 })
    const strokeC = base ? base.copy({ opacity: 0.4 }) : d3.color('#64748b').copy({ opacity: 0.45 })
    d3.select(this).attr('fill', fillC.formatRgb()).attr('stroke', strokeC.formatRgb())
  })

  pathJoin.attr('d', d => d.pathD)

  const labelJoin = labelG
    .selectAll('text')
    .data(entries, d => d.layoutKey)
    .join('text')
    .attr('text-anchor', 'middle')
    .attr('font-size', 10)
    .attr('font-weight', 600)
    .attr('fill', '#475569')
    .style('paint-order', 'stroke fill')
    .attr('stroke', '#f8fafc')
    .attr('stroke-width', 4)
    .attr('pointer-events', 'none')

  labelJoin.attr('x', d => d.cx).attr('y', d => d.cy - 10)
  labelJoin.text(d => (d.seg.length > 38 ? `${d.seg.slice(0, 36)}…` : d.seg))
}

export function redrawVlanGrouping(vlanHullG, vlanLabelG, nodeData, visible) {
  if (!vlanHullG || !vlanLabelG) return

  if (!visible) {
    vlanHullG.selectAll('*').remove()
    vlanLabelG.selectAll('*').remove()
    return
  }

  const entries = buildVlanOutlineEntries(nodeData)

  const pathJoin = vlanHullG
    .selectAll('path')
    .data(entries, d => d.vlanId)
    .join('path')
    .attr('fill', VLAN_HULL_FILL)
    .attr('stroke', 'none')

  pathJoin.attr('d', d => d.pathD)

  const pillG = vlanLabelG
    .selectAll('g.vlan-label-pill')
    .data(entries, d => d.vlanId)
    .join('g')
    .attr('class', 'vlan-label-pill')
    .attr('pointer-events', 'none')
    .attr('transform', d => `translate(${d.labelX}, ${d.labelY})`)

  pillG.each(function (d) {
    const g = d3.select(this)
    g.selectAll('*').remove()
    const textStr = formatVlanLabelText(d)
    const text = g
      .append('text')
      .attr('font-size', 9)
      .attr('font-weight', 600)
      .attr('font-family', 'system-ui, -apple-system, sans-serif')
      .attr('fill', VLAN_PILL_TEXT)
      .attr('x', 0)
      .attr('y', 0)
      .attr('dominant-baseline', 'hanging')
      .text(textStr)

    const node = text.node()
    if (!node || typeof node.getBBox !== 'function') return
    const bbox = node.getBBox()
    g.insert('rect', 'text')
      .attr('x', bbox.x - VLAN_PILL_PAD_X)
      .attr('y', bbox.y - VLAN_PILL_PAD_Y)
      .attr('width', bbox.width + VLAN_PILL_PAD_X * 2)
      .attr('height', bbox.height + VLAN_PILL_PAD_Y * 2)
      .attr('rx', VLAN_PILL_RX)
      .attr('ry', VLAN_PILL_RX)
      .attr('fill', VLAN_PILL_FILL)
  })
}
