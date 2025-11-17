<template>
  <div ref="containerRef" class="relative w-full h-full bg-gray-50 rounded-lg overflow-hidden">
    <!-- SVG Container -->
    <svg ref="svgRef" class="w-full h-full"></svg>

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

    <!-- Controls -->
    <div class="absolute top-4 right-4 flex flex-col gap-2 z-10">
      <button
        @click="zoomIn"
        class="p-2 bg-white rounded-lg shadow-md hover:bg-gray-50 border border-gray-200"
        title="Zoom In"
      >
        <PlusIcon class="h-5 w-5 text-gray-600" />
      </button>
      <button
        @click="zoomOut"
        class="p-2 bg-white rounded-lg shadow-md hover:bg-gray-50 border border-gray-200"
        title="Zoom Out"
      >
        <MinusIcon class="h-5 w-5 text-gray-600" />
      </button>
      <button
        @click="resetView"
        class="p-2 bg-white rounded-lg shadow-md hover:bg-gray-50 border border-gray-200"
        title="Reset View"
      >
        <ArrowPathIcon class="h-5 w-5 text-gray-600" />
      </button>
    </div>

    <!-- Legend -->
    <div
      v-if="legendData.length > 0"
      class="absolute bottom-4 left-4 bg-white rounded-lg shadow-md p-4 border border-gray-200 z-10"
    >
      <h4 class="text-xs font-semibold text-gray-700 mb-2">Node Types</h4>
      <div class="space-y-1">
        <div
          v-for="item in legendData"
          :key="item.type"
          class="flex items-center space-x-2 text-xs"
        >
          <div
            class="w-4 h-4 rounded-full"
            :style="{ backgroundColor: item.color }"
          ></div>
          <span class="text-gray-600 capitalize">{{ item.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { PlusIcon, MinusIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  graphData: {
    type: Object,
    required: true,
    default: () => ({
      nodes: [],
      links: [],
      metadata: {},
      layout_hints: {},
    }),
  },
})

const containerRef = ref(null)
const svgRef = ref(null)
const tooltipRef = ref(null)

let simulation = null
let svg = null
let g = null
let zoom = null
let transform = d3.zoomIdentity
let width = 800
let height = 600

const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  text: '',
})

const legendData = ref([])

// Initialize graph
const initializeGraph = () => {
  if (!svgRef.value || !props.graphData) return

  // Clear existing content
  d3.select(svgRef.value).selectAll('*').remove()

  // Get container dimensions
  const container = containerRef.value
  if (container) {
    width = container.clientWidth || 800
    height = container.clientHeight || 600
  }

  // Create SVG
  svg = d3
    .select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  // Create main group for zoom/pan
  g = svg.append('g')

  // Set up zoom behavior
  zoom = d3
    .zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      transform = event.transform
      g.attr('transform', event.transform)
    })

  svg.call(zoom)

  // Prepare data
  const nodes = props.graphData.nodes || []
  const links = props.graphData.links || []
  const layoutHints = props.graphData.layout_hints || {}

  // Ensure links have proper structure (D3 will resolve IDs to objects)
  const processedLinks = links.map((link) => ({
    source: typeof link.source === 'string' ? link.source : link.source.id || link.source,
    target: typeof link.target === 'string' ? link.target : link.target.id || link.target,
    ...link,
  }))

  // Build legend
  buildLegend(layoutHints.groups || {})

  // Create force simulation
  simulation = d3
    .forceSimulation(nodes)
    .force(
      'link',
      d3
        .forceLink(processedLinks)
        .id((d) => d.id)
        .distance(layoutHints.force_simulation?.link_distance || 100)
    )
    .force('charge', d3.forceManyBody().strength(layoutHints.force_simulation?.charge || -300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius((d) => (d.size || 15) + 5))

  // Create links
  const link = g
    .append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(processedLinks)
    .enter()
    .append('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', 2)

  // Create nodes
  const node = g
    .append('g')
    .attr('class', 'nodes')
    .selectAll('circle')
    .data(nodes)
    .enter()
    .append('circle')
    .attr('r', (d) => d.size || 15)
    .attr('fill', (d) => d.color || '#4ecdc4')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')
    .call(drag(simulation))
    .on('mouseover', handleMouseOver)
    .on('mouseout', handleMouseOut)
    .on('click', handleNodeClick)

  // Add labels
  const label = g
    .append('g')
    .attr('class', 'labels')
    .selectAll('text')
    .data(nodes)
    .enter()
    .append('text')
    .text((d) => d.label || d.id)
    .attr('font-size', '12px')
    .attr('fill', '#333')
    .attr('text-anchor', 'middle')
    .attr('dy', (d) => (d.size || 15) + 18)
    .style('pointer-events', 'none')
    .style('user-select', 'none')

  // Update positions on simulation tick
  simulation.on('tick', () => {
    link
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y)

    node.attr('cx', (d) => d.x).attr('cy', (d) => d.y)

    label.attr('x', (d) => d.x).attr('y', (d) => d.y)
  })
}

// Drag behavior
const drag = (simulation) => {
  const dragstarted = (event, d) => {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }

  const dragged = (event, d) => {
    d.fx = event.x
    d.fy = event.y
  }

  const dragended = (event, d) => {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }

  return d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended)
}

// Mouse event handlers
const handleMouseOver = (event, d) => {
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect()
    tooltip.value = {
      visible: true,
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
      text: d.tooltip || d.label || d.id,
    }
  }
}

const handleMouseOut = () => {
  tooltip.value.visible = false
}

const handleNodeClick = (event, d) => {
  // Highlight connected nodes
  if (svg && g) {
    const connectedNodeIds = new Set([d.id])
    const connectedLinks = []

    props.graphData.links?.forEach((link) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id || link.source
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id || link.target
      if (sourceId === d.id || targetId === d.id) {
        connectedNodeIds.add(sourceId === d.id ? targetId : sourceId)
        connectedLinks.push(link)
      }
    })

    // Update node opacity
    g.selectAll('circle').attr('opacity', (node) => {
      return connectedNodeIds.has(node.id) ? 1 : 0.2
    })

    // Update link opacity
    g.selectAll('line').attr('opacity', (link) => {
      return connectedLinks.includes(link) ? 1 : 0.1
    })

    // Reset after 2 seconds
    setTimeout(() => {
      if (g) {
        g.selectAll('circle').attr('opacity', 1)
        g.selectAll('line').attr('opacity', 0.6)
      }
    }, 2000)
  }
}

// Build legend from groups
const buildLegend = (groups) => {
  const legend = []
  const labels = {
    source: 'Source Network',
    destination: 'Destination Network',
    service: 'Service',
    rule: 'Rule',
    network: 'Network',
  }

  Object.entries(groups).forEach(([type, config]) => {
    legend.push({
      type,
      label: labels[type] || type,
      color: config.color || '#4ecdc4',
    })
  })

  legendData.value = legend
}

// Zoom controls
const zoomIn = () => {
  if (svg && zoom) {
    svg.transition().call(zoom.scaleBy, 1.5)
  }
}

const zoomOut = () => {
  if (svg && zoom) {
    svg.transition().call(zoom.scaleBy, 1 / 1.5)
  }
}

const resetView = () => {
  if (svg && zoom) {
    svg.transition().call(zoom.transform, d3.zoomIdentity)
    // Reset node positions
    if (simulation) {
      simulation.alpha(1).restart()
    }
  }
}

// Watch for data changes
watch(
  () => props.graphData,
  () => {
    if (props.graphData && props.graphData.nodes) {
      nextTick(() => {
        initializeGraph()
      })
    }
  },
  { deep: true }
)

// Handle resize
const handleResize = () => {
  if (containerRef.value && svgRef.value) {
    width = containerRef.value.clientWidth || 800
    height = containerRef.value.clientHeight || 600

    if (svg) {
      svg.attr('width', width).attr('height', height)

      if (simulation) {
        simulation.force('center', d3.forceCenter(width / 2, height / 2))
        simulation.alpha(0.3).restart()
      }
    }
  }
}

onMounted(() => {
  if (props.graphData && props.graphData.nodes) {
    nextTick(() => {
      initializeGraph()
    })
  }

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.links line {
  stroke: #999;
  stroke-opacity: 0.6;
}

.nodes circle {
  cursor: pointer;
  transition: r 0.2s;
}

.nodes circle:hover {
  stroke-width: 3;
}

.labels text {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 12px;
  pointer-events: none;
}
</style>

