import * as d3 from 'd3'
import { VLAN_NONE_KEY } from '@/utils/unifiedGraphKeys'
import { buildSegmentOutlineEntries, buildVlanOutlineEntries } from '@/utils/unifiedGraphHulls'

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

export function redrawVlanGrouping(vlanHullG, vlanLabelG, nodeData, visible, vlanColorFn) {
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
    .attr('stroke-linejoin', 'round')
    .attr('stroke-linecap', 'round')
    .attr('stroke-dasharray', '7 5')
    .attr('stroke-width', 2)

  pathJoin.each(function (d) {
    const el = d3.select(this)
    if (d.vlanId === VLAN_NONE_KEY) {
      el.attr('fill', 'rgba(148, 163, 184, 0.06)').attr('stroke', 'rgba(71, 85, 105, 0.65)')
    } else {
      const base = d3.color(vlanColorFn(d.vlanId))
      const fillC = base
        ? base.copy({ opacity: 0.08 })
        : d3.color('#818cf8').copy({ opacity: 0.08 })
      const strokeC = base
        ? base.copy({ opacity: 0.75 })
        : d3.color('#6366f1').copy({ opacity: 0.8 })
      el.attr('fill', fillC.formatRgb()).attr('stroke', strokeC.formatRgb())
    }
  })

  pathJoin.attr('d', d => d.pathD)

  const labelJoin = vlanLabelG
    .selectAll('text')
    .data(entries, d => d.vlanId)
    .join('text')
    .attr('text-anchor', 'middle')
    .attr('font-size', 9)
    .attr('font-weight', 600)
    .attr('font-style', 'italic')
    .attr('fill', '#4338ca')
    .style('paint-order', 'stroke fill')
    .attr('stroke', '#f8fafc')
    .attr('stroke-width', 3)
    .attr('pointer-events', 'none')

  labelJoin
    .attr('x', d => d.cx)
    .attr('y', d => d.cy + 4)
    .text(d => {
      const t = d.label.length > 32 ? `${d.label.slice(0, 30)}…` : d.label
      return d.vlanId === VLAN_NONE_KEY ? t : `VLAN ${t}`
    })
}
