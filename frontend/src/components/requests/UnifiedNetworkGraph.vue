<template>
  <div ref="containerRef" class="unified-graph-host relative w-full h-full min-h-0 bg-gray-50">
    <svg ref="svgRef" class="w-full block touch-none"></svg>
    <div
      v-if="tooltip.visible"
      class="absolute pointer-events-none z-20 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-xl max-w-md border border-gray-700"
      :style="{
        left: tooltip.x + 'px',
        top: tooltip.y + 'px',
        transform: 'translate(-50%, -100%)',
      }"
    >
      <pre class="whitespace-pre-wrap font-mono text-[11px] leading-relaxed">{{
        tooltip.text
      }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { filterUnifiedGraph } from '@/utils/unifiedGraphFilter'
import { formatNodeDetailLines, formatLinkDetailLines } from '@/utils/unifiedGraphFormat'

const props = defineProps({
  unifiedGraph: {
    type: Object,
    default: null,
  },
  filterText: {
    type: String,
    default: '',
  },
  segmentFocus: {
    type: String,
    default: '',
  },
  emphasizeCrossSegment: {
    type: Boolean,
    default: false,
  },
  selectedNodeId: {
    type: [String, Number],
    default: null,
  },
  selectedLinkKey: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['update:selectedNodeId', 'update:selectedLinkKey'])

const containerRef = ref(null)
const svgRef = ref(null)
const tooltip = ref({ visible: false, x: 0, y: 0, text: '' })

let svg = null
let gMain = null
let zoomBehavior = null
let simulation = null
let resizeObserver = null
let resizeRafId = null

/** Live D3 selections + data for selection / emphasis styling without full rebuild */
let graphCtx = null

let arrowMarkerSeq = 0

function buildColorScale(segments) {
  const scale = d3.scaleOrdinal(d3.schemeTableau10).domain(segments)
  return seg => scale(seg || 'Unknown')
}

function clusterCenters(segments, width, height) {
  const n = Math.max(1, segments.length)
  const cols = Math.ceil(Math.sqrt(n))
  const rows = Math.ceil(n / cols)
  const map = {}
  segments.forEach((seg, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    map[seg] = {
      x: ((col + 0.5) / cols) * width,
      y: ((row + 0.5) / rows) * height,
      col,
      row,
      cols,
      rows,
    }
  })
  return map
}

function segmentRegionLayout(segments, width, height, pad = 10) {
  const n = Math.max(1, segments.length)
  const cols = Math.ceil(Math.sqrt(n))
  const rows = Math.ceil(n / cols)
  const cellW = width / cols
  const cellH = height / rows
  const map = {}
  segments.forEach((seg, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    map[seg] = {
      x: col * cellW + pad,
      y: row * cellH + pad,
      w: cellW - pad * 2,
      h: cellH - pad * 2,
    }
  })
  return map
}

function neighborIds(selId, linkData) {
  const set = new Set([selId])
  for (const l of linkData) {
    const s = typeof l.source === 'object' ? l.source.id : l.source
    const t = typeof l.target === 'object' ? l.target.id : l.target
    if (s === selId) set.add(t)
    if (t === selId) set.add(s)
  }
  return set
}

function linkCrossSegment(d, segById) {
  const s = typeof d.source === 'object' ? d.source.id : d.source
  const t = typeof d.target === 'object' ? d.target.id : d.target
  const a = segById.get(s) || 'Unknown'
  const b = segById.get(t) || 'Unknown'
  return a !== b
}

function linkKeyFromSim(d) {
  const s = typeof d.source === 'object' ? d.source.id : d.source
  const t = typeof d.target === 'object' ? d.target.id : d.target
  return `${s}->${t}`
}

function updateVisualState() {
  if (!graphCtx) return
  const { linkSel, nodeSel, linkData, nodeData } = graphCtx
  const selN = props.selectedNodeId != null ? String(props.selectedNodeId) : null
  const selL = props.selectedLinkKey || null
  const emph = props.emphasizeCrossSegment

  const segById = new Map(nodeData.map(d => [d.id, d.segment || 'Unknown']))

  let highlightEndpoints = null
  if (selL) {
    const [a, b] = selL.split('->')
    highlightEndpoints = new Set([a, b])
  }
  const neighbors = selN ? neighborIds(selN, linkData) : null

  linkSel.each(function (d) {
    let op = 0.85
    let sw = 1.5
    if (emph && !selL && !selN) {
      const cross = linkCrossSegment(d, segById)
      op = cross ? 0.95 : 0.22
      sw = cross ? 2.2 : 1.2
    }
    if (selL) {
      const k = linkKeyFromSim(d)
      const on = k === selL
      op = on ? 1 : 0.12
      sw = on ? 2.6 : 1
    } else if (selN) {
      const s = typeof d.source === 'object' ? d.source.id : d.source
      const t = typeof d.target === 'object' ? d.target.id : d.target
      const inc = s === selN || t === selN
      op = inc ? 0.95 : 0.15
      sw = inc ? 2.1 : 1.2
    }
    d3.select(this).attr('stroke-opacity', op).attr('stroke-width', sw)
  })

  nodeSel.each(function (d) {
    let op = 1
    if (selL && highlightEndpoints) {
      op = highlightEndpoints.has(String(d.id)) ? 1 : 0.18
    } else if (selN && neighbors) {
      op = neighbors.has(String(d.id)) ? 1 : 0.2
    }
    const strokeW = selN && String(d.id) === selN ? 2.8 : 1.2
    const g = d3.select(this)
    g.style('opacity', op)
    g.select('circle').attr('stroke-width', strokeW)
  })
}

function destroyGraph() {
  graphCtx = null
  if (simulation) {
    simulation.on('tick', null)
    simulation.on('end', null)
    simulation.stop()
    simulation = null
  }
  if (svg) {
    svg.on('.zoom', null)
    svg.selectAll('*').remove()
  }
  svg = null
  gMain = null
  zoomBehavior = null
}

function runSimulation() {
  destroyGraph()
  tooltip.value.visible = false

  if (!svgRef.value || !containerRef.value || !props.unifiedGraph?.nodes?.length) return

  const { nodes: rawFiltered, links } = filterUnifiedGraph(props.unifiedGraph, {
    filterText: props.filterText,
    segmentFocus: props.segmentFocus,
  })

  if (!rawFiltered.length) {
    return
  }

  const width = Math.max(320, containerRef.value.clientWidth || 800)
  const ch = containerRef.value.clientHeight
  const height = Math.max(320, ch > 0 ? ch : Math.min(900, width * 0.65))

  svg = d3
    .select(svgRef.value)
    .attr('viewBox', [0, 0, width, height])
    .attr('width', width)
    .attr('height', height)

  gMain = svg.append('g')

  zoomBehavior = d3
    .zoom()
    .scaleExtent([0.2, 4])
    .on('zoom', event => {
      gMain.attr('transform', event.transform)
    })
  svg.call(zoomBehavior)

  const arrowId = `arrowhead-unified-${++arrowMarkerSeq}`
  svg
    .append('defs')
    .append('marker')
    .attr('id', arrowId)
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 28)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#64748b')

  const segments = [...new Set(rawFiltered.map(n => n.segment || 'Unknown'))].sort()
  const centers = clusterCenters(segments, width, height)
  const regionLayout = segmentRegionLayout(segments, width, height)
  const colorFn = buildColorScale(segments)

  const nodeData = rawFiltered.map(n => {
    const seg = n.segment || 'Unknown'
    const c = centers[seg] || { x: width / 2, y: height / 2 }
    const jitter = () => (Math.random() - 0.5) * 48
    return { ...n, x: c.x + jitter(), y: c.y + jitter() }
  })

  const linkData = links.map(l => ({
    ...l,
    source: l.source,
    target: l.target,
  }))

  gMain
    .append('rect')
    .attr('class', 'graph-bg-hit')
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .style('pointer-events', 'all')
    .on('click', event => {
      event.stopPropagation()
      emit('update:selectedNodeId', null)
      emit('update:selectedLinkKey', null)
    })

  const regionG = gMain.append('g').attr('class', 'segment-regions').style('pointer-events', 'none')

  segments.forEach(seg => {
    const r = regionLayout[seg]
    if (!r) return
    const base = d3.color(colorFn(seg))
    const fill = base ? base.copy({ opacity: 0.1 }) : null
    regionG
      .append('rect')
      .attr('x', r.x)
      .attr('y', r.y)
      .attr('width', Math.max(0, r.w))
      .attr('height', Math.max(0, r.h))
      .attr('rx', 8)
      .attr('ry', 8)
      .attr('fill', fill ? fill.formatRgb() : 'rgba(148,163,184,0.1)')
      .attr('stroke', '#cbd5e1')
      .attr('stroke-opacity', 0.45)
      .attr('stroke-width', 1)

    const label = seg.length > 42 ? `${seg.slice(0, 40)}…` : seg
    regionG
      .append('text')
      .attr('x', r.x + 8)
      .attr('y', r.y + 14)
      .attr('font-size', 10)
      .attr('font-weight', 600)
      .attr('fill', '#475569')
      .text(label)
  })

  simulation = d3
    .forceSimulation(nodeData)
    .force(
      'link',
      d3
        .forceLink(linkData)
        .id(d => d.id)
        .distance(90)
        .strength(0.4)
    )
    .force('charge', d3.forceManyBody().strength(-220))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('x', d3.forceX(d => centers[d.segment || 'Unknown']?.x ?? width / 2).strength(0.38))
    .force('y', d3.forceY(d => centers[d.segment || 'Unknown']?.y ?? height / 2).strength(0.38))
    .force('collision', d3.forceCollide().radius(32))

  const linkLayer = gMain.append('g').attr('class', 'link-layer')
  const linkSel = linkLayer
    .attr('stroke', '#94a3b8')
    .selectAll('line')
    .data(linkData)
    .join('line')
    .attr('stroke-width', 1.5)
    .attr('marker-end', `url(#${arrowId})`)
    .style('pointer-events', 'stroke')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      emit('update:selectedLinkKey', linkKeyFromSim(d))
      emit('update:selectedNodeId', null)
      updateVisualState()
    })

  const nodeLayer = gMain.append('g').attr('class', 'node-layer')
  const nodeSel = nodeLayer
    .selectAll('g')
    .data(nodeData)
    .join('g')
    .style('cursor', 'pointer')
    .call(
      d3
        .drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
        })
    )

  nodeSel
    .append('circle')
    .attr('r', 14)
    .attr('fill', d => colorFn(d.segment || 'Unknown'))
    .attr('stroke', '#1e293b')
    .attr('stroke-width', 1.2)

  nodeSel
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', 28)
    .attr('font-size', 9)
    .attr('fill', '#334155')
    .style('pointer-events', 'none')
    .text(d => {
      const t = d.label || d.network_cidr || ''
      return t.length > 18 ? `${t.slice(0, 16)}…` : t
    })

  nodeSel
    .on('click', (event, d) => {
      event.stopPropagation()
      emit('update:selectedNodeId', d.id)
      emit('update:selectedLinkKey', null)
      updateVisualState()
    })
    .on('mouseenter', (event, d) => {
      const rect = containerRef.value.getBoundingClientRect()
      tooltip.value = {
        visible: true,
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        text: formatNodeDetailLines(d).join('\n'),
      }
    })
    .on('mousemove', event => {
      const rect = containerRef.value.getBoundingClientRect()
      tooltip.value.x = event.clientX - rect.left
      tooltip.value.y = event.clientY - rect.top
    })
    .on('mouseleave', () => {
      tooltip.value.visible = false
    })

  linkSel
    .on('mouseenter', (event, d) => {
      const rect = containerRef.value.getBoundingClientRect()
      tooltip.value = {
        visible: true,
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        text: formatLinkDetailLines(d).join('\n'),
      }
    })
    .on('mousemove', event => {
      const rect = containerRef.value.getBoundingClientRect()
      tooltip.value.x = event.clientX - rect.left
      tooltip.value.y = event.clientY - rect.top
    })
    .on('mouseleave', () => {
      tooltip.value.visible = false
    })

  graphCtx = { linkSel, nodeSel, linkData, nodeData }

  simulation.on('tick', () => {
    linkSel
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    nodeSel.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  simulation.on('end', () => {
    requestAnimationFrame(() => {
      fitView(false)
      updateVisualState()
    })
  })

  updateVisualState()
}

function fitView(animated = true) {
  if (!svg || !gMain || !zoomBehavior) return
  const nodeData = gMain.select('.node-layer').selectAll('g').data()
  if (!nodeData?.length) return
  const padding = 56
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  for (const d of nodeData) {
    const x = d.x
    const y = d.y
    if (x == null || y == null || Number.isNaN(x) || Number.isNaN(y)) continue
    minX = Math.min(minX, x - 24)
    minY = Math.min(minY, y - 24)
    maxX = Math.max(maxX, x + 24)
    maxY = Math.max(maxY, y + 44)
  }
  if (!Number.isFinite(minX) || !Number.isFinite(maxX)) return
  const w = svgRef.value.clientWidth || 800
  const h = parseFloat(svg.attr('height')) || 600
  const dx = Math.max(maxX - minX, 80)
  const dy = Math.max(maxY - minY, 80)
  const scale = Math.min((w - padding * 2) / dx, (h - padding * 2) / dy, 2.5) * 0.92
  const tx = w / 2 - scale * (minX + dx / 2)
  const ty = h / 2 - scale * (minY + dy / 2)
  const transform = d3.zoomIdentity.translate(tx, ty).scale(scale)
  if (animated) {
    svg.transition().duration(400).call(zoomBehavior.transform, transform)
  } else {
    svg.call(zoomBehavior.transform, transform)
  }
}

defineExpose({ fitView, restart: runSimulation })

watch(
  () => [props.unifiedGraph, props.filterText, props.segmentFocus],
  () => {
    nextTick(() => runSimulation())
  },
  { deep: true }
)

watch(
  () => [props.selectedNodeId, props.selectedLinkKey, props.emphasizeCrossSegment],
  () => {
    nextTick(() => updateVisualState())
  }
)

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    if (resizeRafId != null) cancelAnimationFrame(resizeRafId)
    resizeRafId = requestAnimationFrame(() => {
      resizeRafId = null
      nextTick(() => runSimulation())
    })
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)
  nextTick(() => runSimulation())
})

onUnmounted(() => {
  if (resizeRafId != null) {
    cancelAnimationFrame(resizeRafId)
    resizeRafId = null
  }
  destroyGraph()
  if (resizeObserver && containerRef.value) resizeObserver.unobserve(containerRef.value)
  resizeObserver = null
})
</script>

<style scoped>
.unified-graph-host {
  min-height: 0;
}
</style>
