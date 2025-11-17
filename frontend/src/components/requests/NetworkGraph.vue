<template>
  <div ref="containerRef" class="w-full h-full bg-gray-50">
    <svg ref="svgRef" class="w-full h-full"></svg>
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
      nodes: [],
      links: [],
      metadata: {},
      layout_hints: {},
    }),
  },
})

const containerRef = ref(null)
const svgRef = ref(null)

let simulation = null
let svg = null
let width = 800
let height = 600
let link = null
let node = null
let label = null


// Initialize graph
const initializeGraph = () => {
  if (!svgRef.value || !props.graphData) return

  // Clear existing content
  d3.select(svgRef.value).selectAll('*').remove()

  // Stop existing simulation
  if (simulation) {
    simulation.stop()
  }

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

  // Prepare data
  const nodes = [...(props.graphData.nodes || [])] // Create copy to avoid mutating props
  const links = props.graphData.links || []

  // Simple random initial positioning
  nodes.forEach((n) => {
    n.x = width / 2 + (Math.random() - 0.5) * 200
    n.y = height / 2 + (Math.random() - 0.5) * 200
  })

  // Ensure links have proper structure (D3 will resolve IDs to objects)
  const processedLinks = links.map((link) => ({
    source: typeof link.source === 'string' ? link.source : link.source.id || link.source,
    target: typeof link.target === 'string' ? link.target : link.target.id || link.target,
    ...link,
  }))

  // Create force simulation
  simulation = d3
    .forceSimulation(nodes)
    .force('link', d3.forceLink(processedLinks).id((d) => d.id).distance(150))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius((d) => (d.size || 15) + 10))
    .alphaDecay(0.02) // Allow simulation to stop naturally after stabilizing

  // Create links
  link = svg
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
  node = svg
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

  // Create labels
  label = svg
    .append('g')
    .attr('class', 'labels')
    .selectAll('text')
    .data(nodes)
    .enter()
    .append('text')
    .text((d) => d.label || d.id)
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('text-anchor', 'middle')
    .style('pointer-events', 'none')

  // Update positions on simulation tick
  simulation.on('tick', () => {
    // Update links
    link
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y)

    // Update nodes
    node.attr('cx', (d) => d.x).attr('cy', (d) => d.y)

    // Update labels
    label.attr('x', (d) => d.x).attr('y', (d) => d.y + (d.size || 15) + 18)
  })
}

// Watch for data changes (shallow watch to avoid infinite loop from position updates)
watch(
  () => props.graphData?.nodes?.length,
  () => {
    if (props.graphData && props.graphData.nodes && props.graphData.nodes.length > 0) {
      nextTick(() => {
        initializeGraph()
      })
    }
  }
)

onMounted(() => {
  if (props.graphData && props.graphData.nodes) {
    nextTick(() => {
      initializeGraph()
    })
  }
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
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

