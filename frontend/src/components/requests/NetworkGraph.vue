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
import { formatCidrToRange } from '@/utils/ipUtils'
import { formatPortRanges } from '@/utils/portUtils'

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
let link = null
let node = null
let label = null

const tooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  text: '',
})

const legendData = ref([])

// Helper function to truncate text
const truncateText = (text, maxLength = 20) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength - 3) + '...'
}

// Helper function to format node label
const formatNodeLabel = (node) => {
  if (!node.label) return node.id || ''
  
  // Format CIDR addresses
  if (node.type === 'source' || node.type === 'destination') {
    return truncateText(formatCidrToRange(node.label), 25)
  }
  
  // Format service labels (protocol/port)
  if (node.type === 'service' && node.label.includes('/')) {
    const [protocol, ports] = node.label.split('/')
    const formattedPorts = formatPortRanges(ports)
    return `${protocol}/${formattedPorts ? truncateText(formattedPorts, 15) : 'any'}`
  }
  
  return truncateText(node.label, 25)
}

// Initialize node positions
const initializeNodePositions = (nodes, isRuleGraph = false) => {
  const centerX = width / 2
  const centerY = height / 2
  
  if (isRuleGraph && nodes.length > 0) {
    // Find the rule node (should be first or marked as center)
    const ruleNode = nodes.find(n => n.type === 'rule') || nodes[0]
    const otherNodes = nodes.filter(n => n.id !== ruleNode.id)
    
    // Place rule node at center
    ruleNode.x = centerX
    ruleNode.y = centerY
    ruleNode.fx = centerX
    ruleNode.fy = centerY
    
    // Place other nodes in a circle around the rule
    const radius = Math.min(width, height) * 0.3
    const angleStep = (2 * Math.PI) / Math.max(otherNodes.length, 1)
    
    otherNodes.forEach((n, i) => {
      const angle = i * angleStep
      n.x = centerX + radius * Math.cos(angle)
      n.y = centerY + radius * Math.sin(angle)
    })
  } else {
    // Random initial positions spread around center
    nodes.forEach((n) => {
      const angle = Math.random() * 2 * Math.PI
      const distance = Math.random() * Math.min(width, height) * 0.3
      n.x = centerX + distance * Math.cos(angle)
      n.y = centerY + distance * Math.sin(angle)
    })
  }
}

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
  const nodes = [...(props.graphData.nodes || [])] // Create copy to avoid mutating props
  const links = props.graphData.links || []
  const layoutHints = props.graphData.layout_hints || {}
  const metadata = props.graphData.metadata || {}

  // Detect if this is a rule graph (has rule node or metadata indicates it)
  const isRuleGraph = nodes.some(n => n.type === 'rule') || metadata.rule_id

  // Initialize node positions before simulation
  initializeNodePositions(nodes, isRuleGraph)

  // Ensure links have proper structure (D3 will resolve IDs to objects)
  const processedLinks = links.map((link) => ({
    source: typeof link.source === 'string' ? link.source : link.source.id || link.source,
    target: typeof link.target === 'string' ? link.target : link.target.id || link.target,
    ...link,
  }))

  // Build legend
  buildLegend(layoutHints.groups || {})

  // Calculate optimal force parameters based on graph size
  const nodeCount = nodes.length
  const linkCount = processedLinks.length
  
  // Adjust charge strength: smaller graphs need less repulsion
  const baseCharge = layoutHints.force_simulation?.charge || -300
  const chargeStrength = nodeCount < 10 ? baseCharge * 0.5 : baseCharge
  
  // Adjust link distance: more links need more space
  const baseLinkDistance = layoutHints.force_simulation?.link_distance || 150
  const linkDistance = nodeCount < 10 ? baseLinkDistance * 1.5 : baseLinkDistance

  // Create force simulation
  simulation = d3
    .forceSimulation(nodes)
    .force(
      'link',
      d3
        .forceLink(processedLinks)
        .id((d) => d.id)
        .distance(linkDistance)
    )
    .force('charge', d3.forceManyBody().strength(chargeStrength))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius((d) => (d.size || 15) + 10))
    .alpha(1) // Start with high energy
    .alphaDecay(0.02) // Slower decay for better convergence
    .velocityDecay(0.4) // Add friction

  // Add radial force for rule graphs to keep nodes around center
  if (isRuleGraph && nodes.length > 1) {
    const ruleNode = nodes.find(n => n.type === 'rule')
    if (ruleNode) {
      simulation.force('radial', d3.forceRadial(
        Math.min(width, height) * 0.25,
        width / 2,
        height / 2
      ).strength(0.1))
    }
  }

  // Create links (straight lines for now, can be curved if needed)
  const linkGroup = g.append('g').attr('class', 'links')
  
  link = linkGroup
    .selectAll('line')
    .data(processedLinks)
    .enter()
    .append('line')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .attr('stroke-width', 2)

  // Create nodes
  const nodeGroup = g.append('g').attr('class', 'nodes')
  
  node = nodeGroup
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

  // Add labels with background for readability
  const labelGroup = g.append('g').attr('class', 'labels')
  
  // Create label groups (text + background)
  const labelGroups = labelGroup
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .attr('class', 'label-group')

  // Create background rectangles for labels
  const labelBg = labelGroups
    .append('rect')
    .attr('fill', 'white')
    .attr('fill-opacity', 0.85)
    .attr('stroke', '#ddd')
    .attr('stroke-width', 1)
    .attr('rx', 3)
    .attr('ry', 3)
    .style('pointer-events', 'none')

  // Create label text
  label = labelGroups
    .append('text')
    .text((d) => formatNodeLabel(d))
    .attr('font-size', '11px')
    .attr('fill', '#333')
    .attr('text-anchor', 'middle')
    .attr('dy', '0.35em')
    .style('pointer-events', 'none')
    .style('user-select', 'none')
    .style('font-weight', '500')

  // Update label backgrounds to fit text
  label.each(function(d, i) {
    // Use setTimeout to ensure text is rendered before measuring
    setTimeout(() => {
      const bbox = this.getBBox()
      const bgNode = d3.select(labelBg.nodes()[i])
      
      if (bbox.width > 0 && bbox.height > 0) {
        bgNode
          .attr('x', bbox.x - 4)
          .attr('y', bbox.y - 2)
          .attr('width', bbox.width + 8)
          .attr('height', bbox.height + 4)
      }
    }, 0)
  })

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

    // Update label groups (text and background move together)
    labelGroups.each(function(d) {
      const labelY = d.y + (d.size || 15) + 18
      d3.select(this).attr('transform', `translate(${d.x},${labelY})`)
      
      // Update background size based on text bounding box
      const textNode = d3.select(this).select('text').node()
      const bgNode = d3.select(this).select('rect')
      
      if (textNode) {
        const bbox = textNode.getBBox()
        if (bbox.width > 0 && bbox.height > 0) {
          bgNode
            .attr('x', bbox.x - 4)
            .attr('y', bbox.y - 2)
            .attr('width', bbox.width + 8)
            .attr('height', bbox.height + 4)
        }
      }
    })
  })

  // Ensure nodes stay within bounds
  simulation.on('end', () => {
    // Release fixed positions for rule node after initial layout
    if (isRuleGraph) {
      const ruleNode = nodes.find(n => n.type === 'rule')
      if (ruleNode && ruleNode.fx !== undefined) {
        // Keep rule node fixed for a bit, then release
        setTimeout(() => {
          if (ruleNode) {
            ruleNode.fx = null
            ruleNode.fy = null
            if (simulation) {
              simulation.alpha(0.3).restart()
            }
          }
        }, 1000)
      }
    }
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
    // Reset node positions and restart simulation
    if (simulation) {
      const nodes = simulation.nodes()
      const isRuleGraph = nodes.some(n => n.type === 'rule')
      initializeNodePositions(nodes, isRuleGraph)
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

