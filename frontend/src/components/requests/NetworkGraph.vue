<template>
  <div ref="containerRef" class="w-full bg-gray-50 relative">
    <svg ref="svgRef" class="w-full"></svg>
    
    <!-- Tooltip -->
    <div
      v-if="tooltip.visible"
      ref="tooltipRef"
      class="absolute pointer-events-none z-10 bg-gray-900 text-white text-xs rounded px-3 py-2 shadow-lg max-w-xs"
      :style="{
        left: tooltip.x + 'px',
        top: tooltip.y + 'px',
        transform: 'translate(-50%, -100%)',
      }"
    >
      <div class="whitespace-pre-line">{{ tooltip.text }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  graphData: {
    type: Object,
    required: true,
    default: () => ({
      sources: [],
      destinations: [],
      connections: [],
      metadata: {},
    }),
  },
})

const containerRef = ref(null)
const svgRef = ref(null)
const tooltipRef = ref(null)

let svg = null
let width = 800
let height = 600

// Tooltip state
const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  text: '',
})

// Constants
const RECT_WIDTH = 120
const RECT_HEIGHT = 40
const BADGE_RADIUS = 12
const LEFT_X = 0.2 // 20% from left
const RIGHT_X = 0.7 // 70% from left
const START_Y = 0.1 // 10% from top
const VERTICAL_SPACING = 80

// Initialize graph
const initializeGraph = () => {
  if (!svgRef.value || !props.graphData) return

  // Clear existing content - remove all SVG elements including any lingering port circles
  const svgSelection = d3.select(svgRef.value)
  svgSelection.selectAll('*').remove()
  // Explicitly remove any port circle elements by class (extra safety)
  svgSelection.selectAll('.port-circle, .ports circle, circle[class*="port"]').remove()

  // Extract data
  const sources = props.graphData.sources || []
  const destinations = props.graphData.destinations || []
  const connections = props.graphData.connections || []

  if (sources.length === 0 || destinations.length === 0) {
    return
  }

  // Get container width
  const container = containerRef.value
  if (container) {
    width = container.clientWidth || 800
  }

  // Calculate height based on content
  const maxItems = Math.max(sources.length, destinations.length)
  const padding = 100 // Top and bottom padding
  height = Math.max(600, padding + maxItems * VERTICAL_SPACING + RECT_HEIGHT)

  // Create SVG
  svg = d3
    .select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  // Calculate positions
  const leftX = width * LEFT_X
  const rightX = width * RIGHT_X
  const startY = 50 // Fixed top padding instead of percentage

  // Position source rectangles
  sources.forEach((src, i) => {
    src.x = leftX
    src.y = startY + i * VERTICAL_SPACING
    src.width = RECT_WIDTH
    src.height = RECT_HEIGHT
  })

  // Position destination rectangles
  destinations.forEach((dst, i) => {
    dst.x = rightX
    dst.y = startY + i * VERTICAL_SPACING
    dst.width = RECT_WIDTH
    dst.height = RECT_HEIGHT
  })

  // Calculate connection line positions
  connections.forEach((conn) => {
    const source = sources.find((s) => s.id === conn.source_id)
    const dest = destinations.find((d) => d.id === conn.destination_id)

    if (source && dest) {
      conn.x1 = source.x + source.width
      conn.y1 = source.y + source.height / 2
      conn.x2 = dest.x
      conn.y2 = dest.y + dest.height / 2

      // Midpoint for badge
      conn.badgeX = (conn.x1 + conn.x2) / 2
      conn.badgeY = (conn.y1 + conn.y2) / 2
    }
  })

  // Create groups for layering
  const linksGroup = svg.append('g').attr('class', 'links')
  const rectsGroup = svg.append('g').attr('class', 'rectangles')
  const badgesGroup = svg.append('g').attr('class', 'badges')
  const labelsGroup = svg.append('g').attr('class', 'labels')

  // Draw connection lines (curved)
  const lineGenerator = d3
    .line()
    .curve(d3.curveBasis)
    .x((d) => d[0])
    .y((d) => d[1])

  linksGroup
    .selectAll('path')
    .data(connections)
    .enter()
    .append('path')
    .attr('d', (d) => {
      // Create curved path
      const midX = (d.x1 + d.x2) / 2
      return lineGenerator([
        [d.x1, d.y1],
        [midX, d.y1],
        [midX, d.y2],
        [d.x2, d.y2],
      ])
    })
    .attr('fill', 'none')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', 2)

  // Draw source rectangles
  rectsGroup
    .selectAll('rect.source')
    .data(sources)
    .enter()
    .append('rect')
    .attr('class', 'source')
    .attr('x', (d) => d.x)
    .attr('y', (d) => d.y)
    .attr('width', (d) => d.width)
    .attr('height', (d) => d.height)
    .attr('fill', '#4ecdc4')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('rx', 4)
    .style('cursor', 'pointer')
    .on('mouseover', (event, d) => showTooltip(event, d.tooltip || d.formatted_label))
    .on('mouseout', hideTooltip)

  // Draw destination rectangles
  rectsGroup
    .selectAll('rect.destination')
    .data(destinations)
    .enter()
    .append('rect')
    .attr('class', 'destination')
    .attr('x', (d) => d.x)
    .attr('y', (d) => d.y)
    .attr('width', (d) => d.width)
    .attr('height', (d) => d.height)
    .attr('fill', '#45b7d1')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('rx', 4)
    .style('cursor', 'pointer')
    .on('mouseover', (event, d) => showTooltip(event, d.tooltip || d.formatted_label))
    .on('mouseout', hideTooltip)

  // Draw port count badges on connection lines
  badgesGroup
    .selectAll('g.badge')
    .data(connections)
    .enter()
    .append('g')
    .attr('class', 'badge')
    .attr('transform', (d) => `translate(${d.badgeX}, ${d.badgeY})`)
    .append('circle')
    .attr('r', BADGE_RADIUS)
    .attr('fill', 'white')
    .attr('stroke', '#999')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')
    .on('mouseover', (event, d) => {
      const servicesText = d.services
        .map((s) => `${s.protocol}/${s.formatted_ports || 'any'}`)
        .join('\n')
      showTooltip(event, `Ports: ${d.port_count}\n\n${servicesText}`)
    })
    .on('mouseout', hideTooltip)

  // Add badge text
  badgesGroup
    .selectAll('g.badge')
    .append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .attr('font-size', '11px')
    .attr('font-weight', 'bold')
    .attr('fill', '#333')
    .text((d) => d.port_count.toString())
    .style('pointer-events', 'none')

  // Draw labels for source rectangles
  labelsGroup
    .selectAll('text.source-label')
    .data(sources)
    .enter()
    .append('text')
    .attr('class', 'source-label')
    .attr('x', (d) => d.x + d.width / 2)
    .attr('y', (d) => d.y + d.height / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#fff')
    .attr('font-weight', '500')
    .text((d) => d.formatted_label || d.label)
    .style('pointer-events', 'none')

  // Draw labels for destination rectangles
  labelsGroup
    .selectAll('text.destination-label')
    .data(destinations)
    .enter()
    .append('text')
    .attr('class', 'destination-label')
    .attr('x', (d) => d.x + d.width / 2)
    .attr('y', (d) => d.y + d.height / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#fff')
    .attr('font-weight', '500')
    .text((d) => d.formatted_label || d.label)
    .style('pointer-events', 'none')
}

// Tooltip functions
const showTooltip = (event, text) => {
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect()
    tooltip.value = {
      visible: true,
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
      text: text,
    }
  }
}

const hideTooltip = () => {
  tooltip.value.visible = false
}

// Watch for data changes
watch(
  () => props.graphData?.sources?.length,
  () => {
    if (props.graphData && props.graphData.sources && props.graphData.sources.length > 0) {
      nextTick(() => {
        initializeGraph()
      })
    }
  }
)

onMounted(() => {
  if (props.graphData && props.graphData.sources) {
    nextTick(() => {
      initializeGraph()
    })
  }
})

onUnmounted(() => {
  // Cleanup if needed
})
</script>

<style scoped>
.links path {
  stroke: #999;
  stroke-opacity: 0.6;
}

.rectangles rect {
  cursor: pointer;
  transition: stroke-width 0.2s;
}

.rectangles rect:hover {
  stroke-width: 3;
}

.badges circle {
  cursor: pointer;
}

.labels text {
  font-family: system-ui, -apple-system, sans-serif;
  pointer-events: none;
  user-select: none;
}
</style>
