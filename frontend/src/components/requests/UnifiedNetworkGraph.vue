<template>
  <div ref="containerRef" class="unified-graph-host relative w-full h-full min-h-0 bg-gray-50">
    <svg ref="svgRef" class="w-full block touch-none"></svg>
    <div
      v-if="tooltip.visible"
      class="absolute pointer-events-none z-20 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-xl max-w-md border border-gray-700"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px', transform: 'translate(-50%, -100%)' }"
    >
      <pre class="whitespace-pre-wrap font-mono text-[11px] leading-relaxed">{{ tooltip.text }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  unifiedGraph: {
    type: Object,
    default: null,
  },
  filterText: {
    type: String,
    default: '',
  },
})

const containerRef = ref(null)
const svgRef = ref(null)
const tooltip = ref({ visible: false, x: 0, y: 0, text: '' })

let svg = null
let gMain = null
let zoomBehavior = null
let simulation = null
let resizeObserver = null

function buildColorScale(nodes) {
  const segments = [...new Set(nodes.map((n) => n.segment || 'Unknown'))].sort()
  const scale = d3.scaleOrdinal(d3.schemeTableau10).domain(segments)
  return (n) => scale(n.segment || 'Unknown')
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
    }
  })
  return map
}

function formatNodeTooltip(d) {
  const lines = [d.label || d.network_cidr]
  if (d.network_cidr) lines.push(`CIDR: ${d.network_cidr}`)
  if (d.segment) lines.push(`Segment: ${d.segment}`)
  if (d.vlan != null && d.vlan !== '') lines.push(`VLAN: ${d.vlan}`)
  if (d.environment) lines.push(`Env: ${d.environment}`)
  if (d.location) lines.push(`Location: ${d.location}`)
  if (d.asset?.hostname) lines.push(`Hostname: ${d.asset.hostname}`)
  return lines.join('\n')
}

function formatLinkTooltip(d) {
  const lines = [d.label || 'Connection']
  if (d.rule_ids?.length) lines.push(`Rules: ${d.rule_ids.join(', ')}`)
  if (d.services?.length) {
    const svc = d.services.map((s) => `${s.protocol}/${s.formatted_ports || s.port_ranges}`).join(', ')
    lines.push(`Services: ${svc}`)
  }
  return lines.join('\n')
}

function destroyGraph() {
  if (simulation) {
    simulation.stop()
    simulation = null
  }
  if (svg) {
    svg.selectAll('*').remove()
  }
}

function runSimulation() {
  destroyGraph()
  tooltip.value.visible = false

  if (!svgRef.value || !containerRef.value || !props.unifiedGraph?.nodes?.length) return

  const rawNodes = props.unifiedGraph.nodes
  const rawLinks = props.unifiedGraph.links || []

  const q = (props.filterText || '').trim().toLowerCase()
  const nodes = rawNodes.filter((n) => {
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
  const idSet = new Set(nodes.map((d) => d.id))
  const links = rawLinks.filter((l) => idSet.has(l.source) && idSet.has(l.target))

  if (!nodes.length) {
    return
  }

  const width = Math.max(320, containerRef.value.clientWidth || 800)
  const ch = containerRef.value.clientHeight
  const height = Math.max(320, ch > 0 ? ch : Math.min(900, width * 0.65))

  svg = d3.select(svgRef.value).attr('viewBox', [0, 0, width, height]).attr('width', width).attr('height', height)

  gMain = svg.append('g')

  zoomBehavior = d3
    .zoom()
    .scaleExtent([0.2, 4])
    .on('zoom', (event) => {
      gMain.attr('transform', event.transform)
    })
  svg.call(zoomBehavior)

  svg.append('defs')
    .append('marker')
    .attr('id', 'arrowhead-unified')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 28)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#64748b')

  const segments = [...new Set(nodes.map((n) => n.segment || 'Unknown'))].sort()
  const centers = clusterCenters(segments, width, height)
  const colorFn = buildColorScale(nodes)

  const nodeData = nodes.map((n) => ({ ...n }))
  const linkData = links.map((l) => ({
    ...l,
    source: l.source,
    target: l.target,
  }))

  simulation = d3
    .forceSimulation(nodeData)
    .force(
      'link',
      d3
        .forceLink(linkData)
        .id((d) => d.id)
        .distance(90)
        .strength(0.4),
    )
    .force('charge', d3.forceManyBody().strength(-220))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force(
      'x',
      d3
        .forceX((d) => centers[d.segment || 'Unknown']?.x ?? width / 2)
        .strength(0.18),
    )
    .force(
      'y',
      d3
        .forceY((d) => centers[d.segment || 'Unknown']?.y ?? height / 2)
        .strength(0.18),
    )
    .force('collision', d3.forceCollide().radius(32))

  const linkLayer = gMain.append('g').attr('class', 'link-layer')
  const linkSel = linkLayer
    .attr('stroke', '#94a3b8')
    .attr('stroke-opacity', 0.85)
    .selectAll('line')
    .data(linkData)
    .join('line')
    .attr('stroke-width', 1.5)
    .attr('marker-end', 'url(#arrowhead-unified)')

  const nodeLayer = gMain.append('g').attr('class', 'node-layer')
  const nodeSel = nodeLayer
    .selectAll('g')
    .data(nodeData)
    .join('g')
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
        }),
    )

  nodeSel
    .append('circle')
    .attr('r', 14)
    .attr('fill', (d) => colorFn(d))
    .attr('stroke', '#1e293b')
    .attr('stroke-width', 1.2)

  nodeSel
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', 28)
    .attr('font-size', 9)
    .attr('fill', '#334155')
    .text((d) => {
      const t = d.label || d.network_cidr || ''
      return t.length > 18 ? `${t.slice(0, 16)}…` : t
    })

  nodeSel
    .on('mouseenter', (event, d) => {
      const rect = containerRef.value.getBoundingClientRect()
      tooltip.value = {
        visible: true,
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
        text: formatNodeTooltip(d),
      }
    })
    .on('mousemove', (event) => {
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
        text: formatLinkTooltip(d),
      }
    })
    .on('mousemove', (event) => {
      const rect = containerRef.value.getBoundingClientRect()
      tooltip.value.x = event.clientX - rect.left
      tooltip.value.y = event.clientY - rect.top
    })
    .on('mouseleave', () => {
      tooltip.value.visible = false
    })

  simulation.on('tick', () => {
    linkSel
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y)

    nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`)
  })

  simulation.on('end', () => {
    requestAnimationFrame(() => fitView(false))
  })
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
    if (x == null || y == null || Number.isNaN(x) || Number.isNaN(y)) return
    minX = Math.min(minX, x - 24)
    minY = Math.min(minY, y - 24)
    maxX = Math.max(maxX, x + 24)
    maxY = Math.max(maxY, y + 44)
  }
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
  () => [props.unifiedGraph, props.filterText],
  () => {
    nextTick(() => runSimulation())
  },
  { deep: true },
)

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    nextTick(() => runSimulation())
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)
  nextTick(() => runSimulation())
})

onUnmounted(() => {
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
