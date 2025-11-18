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
import { useAssetCache } from '@/composables/useAssetCache'
import { extractBaseIpFromCidr } from '@/utils/ipUtils'

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

// Selection state
const selectedIP = ref(null)

// Asset cache for fetching asset information
const { fetchAsset, getAssetForCidr } = useAssetCache()

// Constants
const RECT_WIDTH = 120
const RECT_HEIGHT = 40
const BADGE_RADIUS = 12
const LEFT_X = 0.2 // 20% from left
const RIGHT_X = 0.7 // 70% from left
const START_Y = 0.1 // 10% from top
const VERTICAL_SPACING = 80

// Grouping constants
const GROUP_PADDING = 20 // Padding around VLAN groups
const SEGMENT_PADDING = 12 // Padding around segments within VLAN
const NODE_SPACING = 60 // Spacing between nodes within segment
const GROUP_SPACING = 40 // Spacing between VLAN groups

// Color scheme - light pastel shades
const VLAN_COLORS = {
  default: '#e8f4f8', // Light blue
  border: '#b8d4e0', // Medium blue border
  text: '#5a7a8a' // Darker blue text
}

const SEGMENT_COLORS = {
  default: '#f0f8f4', // Light green
  border: '#c8e0d4', // Medium green border
  text: '#5a8a7a' // Darker green text
}

const UNCategorized_COLOR = '#f5f5f5' // Light gray for uncategorized

// Fetch assets for all IPs in the graph
const fetchAssetsForGraph = async () => {
  if (!props.graphData) return
  
  const sources = props.graphData.sources || []
  const destinations = props.graphData.destinations || []
  
  // Collect all unique IPs
  const uniqueIPs = new Set()
  sources.forEach(src => {
    if (src.network_cidr) {
      const baseIp = extractBaseIpFromCidr(src.network_cidr)
      if (baseIp) uniqueIPs.add(baseIp)
    }
  })
  destinations.forEach(dest => {
    if (dest.network_cidr) {
      const baseIp = extractBaseIpFromCidr(dest.network_cidr)
      if (baseIp) uniqueIPs.add(baseIp)
    }
  })
  
  // Fetch assets for all unique IPs (in parallel)
  await Promise.all(Array.from(uniqueIPs).map(ip => fetchAsset(ip)))
}

// Group nodes by VLAN first, then by Segment
const groupNodesByVlanAndSegment = (nodes, nodeType) => {
  const groups = {}
  
  nodes.forEach(node => {
    const cidr = node.network_cidr
    const baseIp = extractBaseIpFromCidr(cidr)
    const asset = baseIp ? getAssetForCidr(cidr) : null
    
    const vlan = asset?.vlan || 'Uncategorized'
    const segment = asset?.segment || 'Uncategorized'
    
    if (!groups[vlan]) {
      groups[vlan] = {}
    }
    if (!groups[vlan][segment]) {
      groups[vlan][segment] = []
    }
    
    // Store grouping metadata on node
    node.vlan = vlan
    node.segment = segment
    node.asset = asset
    
    groups[vlan][segment].push(node)
  })
  
  return groups
}

// Calculate positions for grouped nodes
const calculateGroupPositions = (groupedNodes, startX, startY) => {
  let currentY = startY
  const groupBounds = []
  
  Object.entries(groupedNodes).forEach(([vlan, segments]) => {
    const vlanNodes = []
    const segmentBounds = []
    let vlanStartY = currentY
    let vlanCurrentY = currentY + GROUP_PADDING
    
    Object.entries(segments).forEach(([segment, nodes]) => {
      const segmentStartY = vlanCurrentY
      let segmentCurrentY = vlanCurrentY + SEGMENT_PADDING
      
      // Position nodes within segment
      nodes.forEach((node, i) => {
        node.x = startX
        node.y = segmentCurrentY
        node.width = RECT_WIDTH
        node.height = RECT_HEIGHT
        segmentCurrentY += NODE_SPACING
      })
      
      const segmentEndY = segmentCurrentY - NODE_SPACING + RECT_HEIGHT
      segmentBounds.push({
        segment,
        startY: segmentStartY,
        endY: segmentEndY,
        nodes: nodes,
        height: segmentEndY - segmentStartY
      })
      
      vlanNodes.push(...nodes)
      vlanCurrentY = segmentEndY + SEGMENT_PADDING + GROUP_SPACING
    })
    
    const vlanEndY = vlanCurrentY - GROUP_SPACING
    groupBounds.push({
      vlan,
      startY: vlanStartY,
      endY: vlanEndY,
      segments: segmentBounds,
      nodes: vlanNodes,
      height: vlanEndY - vlanStartY
    })
    
    currentY = vlanEndY + GROUP_SPACING
  })
  
  return groupBounds
}

// Build enhanced tooltip text with asset information
const buildTooltipText = (nodeData) => {
  const baseTooltip = nodeData.tooltip || nodeData.formatted_label || nodeData.label || ''
  const cidr = nodeData.network_cidr
  
  if (!cidr) return baseTooltip
  
  const baseIp = extractBaseIpFromCidr(cidr)
  const asset = baseIp ? getAssetForCidr(cidr) : null
  
  if (!asset) return baseTooltip
  
  // Build asset info lines
  const assetLines = []
  if (asset.hostname) assetLines.push(`Hostname: ${asset.hostname}`)
  if (asset.segment) assetLines.push(`Segment: ${asset.segment}`)
  if (asset.vlan) assetLines.push(`VLAN: ${asset.vlan}`)
  if (asset.os_name) assetLines.push(`OS: ${asset.os_name}`)
  
  if (assetLines.length === 0) return baseTooltip
  
  return `${baseTooltip}\n\n${assetLines.join('\n')}`
}

// Initialize graph
const initializeGraph = async () => {
  if (!svgRef.value || !props.graphData) return

  // Reset selection when graph is reinitialized
  selectedIP.value = null

  // Fetch assets for all IPs in the graph
  await fetchAssetsForGraph()

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

  // Calculate positions
  const leftX = width * LEFT_X
  const rightX = width * RIGHT_X
  const startY = 50 // Fixed top padding instead of percentage

  // Group sources and destinations by VLAN and Segment
  const groupedSources = groupNodesByVlanAndSegment(sources, 'source')
  const groupedDestinations = groupNodesByVlanAndSegment(destinations, 'destination')
  
  // Calculate positions for grouped sources
  const sourceGroupBounds = calculateGroupPositions(groupedSources, leftX, startY)
  
  // Calculate positions for grouped destinations
  const destinationGroupBounds = calculateGroupPositions(groupedDestinations, rightX, startY)
  
  // Calculate height based on actual grouped content
  const maxSourceHeight = sourceGroupBounds.length > 0 
    ? Math.max(...sourceGroupBounds.map(g => g.endY))
    : startY
  const maxDestHeight = destinationGroupBounds.length > 0
    ? Math.max(...destinationGroupBounds.map(g => g.endY))
    : startY
  const padding = 100 // Top and bottom padding
  height = Math.max(600, Math.max(maxSourceHeight, maxDestHeight) + padding)

  // Create SVG
  svg = d3
    .select(svgRef.value)
    .attr('width', width)
    .attr('height', height)
    .on('click', (event) => {
      // Clear selection when clicking blank SVG area
      if (event.target === svgRef.value || event.target.tagName === 'svg') {
        selectedIP.value = null
        updateHighlighting()
      }
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

  // Create groups for layering (order matters - bottom to top)
  const backgroundsGroup = svg.append('g').attr('class', 'backgrounds')
  const linksGroup = svg.append('g').attr('class', 'links')
  const rectsGroup = svg.append('g').attr('class', 'rectangles')
  const badgesGroup = svg.append('g').attr('class', 'badges')
  const labelsGroup = svg.append('g').attr('class', 'labels')
  const vlanLabelsGroup = svg.append('g').attr('class', 'vlan-labels')
  const segmentLabelsGroup = svg.append('g').attr('class', 'segment-labels')
  
  // Draw VLAN and Segment background rectangles for sources
  sourceGroupBounds.forEach(vlanGroup => {
    // Draw VLAN background (outer rectangle)
    backgroundsGroup
      .append('rect')
      .attr('class', 'vlan-group source-vlan')
      .attr('x', leftX - GROUP_PADDING)
      .attr('y', vlanGroup.startY)
      .attr('width', RECT_WIDTH + (GROUP_PADDING * 2))
      .attr('height', vlanGroup.height)
      .attr('fill', vlanGroup.vlan === 'Uncategorized' ? UNCategorized_COLOR : VLAN_COLORS.default)
      .attr('stroke', vlanGroup.vlan === 'Uncategorized' ? '#d0d0d0' : VLAN_COLORS.border)
      .attr('stroke-width', 2)
      .attr('rx', 6)
      .attr('opacity', 0.6)
    
    // Draw VLAN label
    vlanLabelsGroup
      .append('text')
      .attr('class', 'vlan-label')
      .attr('x', leftX - GROUP_PADDING + 8)
      .attr('y', vlanGroup.startY + 18)
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', vlanGroup.vlan === 'Uncategorized' ? '#888' : VLAN_COLORS.text)
      .text(`VLAN: ${vlanGroup.vlan}`)
    
    // Draw Segment backgrounds (inner rectangles)
    vlanGroup.segments.forEach(segmentGroup => {
      backgroundsGroup
        .append('rect')
        .attr('class', 'segment-group source-segment')
        .attr('x', leftX - SEGMENT_PADDING)
        .attr('y', segmentGroup.startY)
        .attr('width', RECT_WIDTH + (SEGMENT_PADDING * 2))
        .attr('height', segmentGroup.height)
        .attr('fill', segmentGroup.segment === 'Uncategorized' ? '#fafafa' : SEGMENT_COLORS.default)
        .attr('stroke', segmentGroup.segment === 'Uncategorized' ? '#e0e0e0' : SEGMENT_COLORS.border)
        .attr('stroke-width', 1.5)
        .attr('rx', 4)
        .attr('opacity', 0.5)
      
      // Draw Segment label
      segmentLabelsGroup
        .append('text')
        .attr('class', 'segment-label')
        .attr('x', leftX - SEGMENT_PADDING + 6)
        .attr('y', segmentGroup.startY + 16)
        .attr('font-size', '11px')
        .attr('font-weight', '500')
        .attr('fill', segmentGroup.segment === 'Uncategorized' ? '#aaa' : SEGMENT_COLORS.text)
        .text(`Segment: ${segmentGroup.segment}`)
    })
  })
  
  // Draw VLAN and Segment background rectangles for destinations
  destinationGroupBounds.forEach(vlanGroup => {
    // Draw VLAN background (outer rectangle)
    backgroundsGroup
      .append('rect')
      .attr('class', 'vlan-group destination-vlan')
      .attr('x', rightX - GROUP_PADDING)
      .attr('y', vlanGroup.startY)
      .attr('width', RECT_WIDTH + (GROUP_PADDING * 2))
      .attr('height', vlanGroup.height)
      .attr('fill', vlanGroup.vlan === 'Uncategorized' ? UNCategorized_COLOR : VLAN_COLORS.default)
      .attr('stroke', vlanGroup.vlan === 'Uncategorized' ? '#d0d0d0' : VLAN_COLORS.border)
      .attr('stroke-width', 2)
      .attr('rx', 6)
      .attr('opacity', 0.6)
    
    // Draw VLAN label
    vlanLabelsGroup
      .append('text')
      .attr('class', 'vlan-label')
      .attr('x', rightX - GROUP_PADDING + 8)
      .attr('y', vlanGroup.startY + 18)
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', vlanGroup.vlan === 'Uncategorized' ? '#888' : VLAN_COLORS.text)
      .text(`VLAN: ${vlanGroup.vlan}`)
    
    // Draw Segment backgrounds (inner rectangles)
    vlanGroup.segments.forEach(segmentGroup => {
      backgroundsGroup
        .append('rect')
        .attr('class', 'segment-group destination-segment')
        .attr('x', rightX - SEGMENT_PADDING)
        .attr('y', segmentGroup.startY)
        .attr('width', RECT_WIDTH + (SEGMENT_PADDING * 2))
        .attr('height', segmentGroup.height)
        .attr('fill', segmentGroup.segment === 'Uncategorized' ? '#fafafa' : SEGMENT_COLORS.default)
        .attr('stroke', segmentGroup.segment === 'Uncategorized' ? '#e0e0e0' : SEGMENT_COLORS.border)
        .attr('stroke-width', 1.5)
        .attr('rx', 4)
        .attr('opacity', 0.5)
      
      // Draw Segment label
      segmentLabelsGroup
        .append('text')
        .attr('class', 'segment-label')
        .attr('x', rightX - SEGMENT_PADDING + 6)
        .attr('y', segmentGroup.startY + 16)
        .attr('font-size', '11px')
        .attr('font-weight', '500')
        .attr('fill', segmentGroup.segment === 'Uncategorized' ? '#aaa' : SEGMENT_COLORS.text)
        .text(`Segment: ${segmentGroup.segment}`)
    })
  })

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
    .attr('class', 'connection')
    .attr('data-source-id', (d) => d.source_id)
    .attr('data-destination-id', (d) => d.destination_id)
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
    .attr('data-id', (d) => d.id)
    .attr('x', (d) => d.x)
    .attr('y', (d) => d.y)
    .attr('width', (d) => d.width)
    .attr('height', (d) => d.height)
    .attr('fill', '#4ecdc4')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('rx', 4)
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      // Toggle selection: if same IP clicked, deselect; otherwise select new IP
      selectedIP.value = selectedIP.value === d.id ? null : d.id
      updateHighlighting()
    })
    .on('mouseover', (event, d) => showTooltip(event, buildTooltipText(d)))
    .on('mouseout', hideTooltip)

  // Draw destination rectangles
  rectsGroup
    .selectAll('rect.destination')
    .data(destinations)
    .enter()
    .append('rect')
    .attr('class', 'destination')
    .attr('data-id', (d) => d.id)
    .attr('x', (d) => d.x)
    .attr('y', (d) => d.y)
    .attr('width', (d) => d.width)
    .attr('height', (d) => d.height)
    .attr('fill', '#45b7d1')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .attr('rx', 4)
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      // Toggle selection: if same IP clicked, deselect; otherwise select new IP
      selectedIP.value = selectedIP.value === d.id ? null : d.id
      updateHighlighting()
    })
    .on('mouseover', (event, d) => showTooltip(event, buildTooltipText(d)))
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
    .attr('data-id', (d) => d.id)
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
    .attr('data-id', (d) => d.id)
    .attr('x', (d) => d.x + d.width / 2)
    .attr('y', (d) => d.y + d.height / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#fff')
    .attr('font-weight', '500')
    .text((d) => d.formatted_label || d.label)
    .style('pointer-events', 'none')

  // Initial highlighting update
  updateHighlighting()
}

// Update highlighting based on selected IP
const updateHighlighting = () => {
  if (!svg || !props.graphData) return

  const selectedId = selectedIP.value
  const sources = props.graphData.sources || []
  const destinations = props.graphData.destinations || []
  const connections = props.graphData.connections || []

  // Find all connected IP IDs
  let connectedIPIds = new Set()
  if (selectedId) {
    // Find all connections involving the selected IP
    connections.forEach(conn => {
      if (conn.source_id === selectedId) {
        // Selected is a source, highlight connected destinations
        connectedIPIds.add(conn.destination_id)
      } else if (conn.destination_id === selectedId) {
        // Selected is a destination, highlight connected sources
        connectedIPIds.add(conn.source_id)
      }
    })
    // Also include the selected IP itself
    connectedIPIds.add(selectedId)
  }

  // Update source rectangles
  svg
    .selectAll('rect.source')
    .each(function (d) {
      const rect = d3.select(this)
      const isSelected = d.id === selectedId
      const isConnected = connectedIPIds.has(d.id)
      
      if (isSelected || isConnected) {
        rect
          .attr('opacity', 1)
          .attr('stroke-width', 4)
          .attr('stroke', '#ffd700') // Gold border for selected/connected
      } else if (selectedId) {
        rect.attr('opacity', 0.3)
        rect.attr('stroke-width', 2)
        rect.attr('stroke', '#fff')
      } else {
        rect.attr('opacity', 1)
        rect.attr('stroke-width', 2)
        rect.attr('stroke', '#fff')
      }
    })

  // Update destination rectangles
  svg
    .selectAll('rect.destination')
    .each(function (d) {
      const rect = d3.select(this)
      const isSelected = d.id === selectedId
      const isConnected = connectedIPIds.has(d.id)
      
      if (isSelected || isConnected) {
        rect
          .attr('opacity', 1)
          .attr('stroke-width', 4)
          .attr('stroke', '#ffd700') // Gold border for selected/connected
      } else if (selectedId) {
        rect.attr('opacity', 0.3)
        rect.attr('stroke-width', 2)
        rect.attr('stroke', '#fff')
      } else {
        rect.attr('opacity', 1)
        rect.attr('stroke-width', 2)
        rect.attr('stroke', '#fff')
      }
    })

  // Update connection lines
  svg
    .selectAll('path.connection')
    .each(function (d) {
      const path = d3.select(this)
      const isRelated = selectedId && (d.source_id === selectedId || d.destination_id === selectedId)
      
      if (isRelated) {
        path
          .attr('stroke-opacity', 1)
          .attr('stroke-width', 3)
          .attr('stroke', '#666')
      } else if (selectedId) {
        path
          .attr('stroke-opacity', 0.2)
          .attr('stroke-width', 2)
          .attr('stroke', '#999')
      } else {
        path
          .attr('stroke-opacity', 0.6)
          .attr('stroke-width', 2)
          .attr('stroke', '#999')
      }
    })

  // Update port count badges
  svg
    .selectAll('g.badge')
    .each(function (d) {
      const badge = d3.select(this)
      const isRelated = selectedId && (d.source_id === selectedId || d.destination_id === selectedId)
      
      if (isRelated) {
        badge.select('circle').attr('opacity', 1)
        badge.select('text').attr('opacity', 1)
      } else if (selectedId) {
        badge.select('circle').attr('opacity', 0.2)
        badge.select('text').attr('opacity', 0.2)
      } else {
        badge.select('circle').attr('opacity', 1)
        badge.select('text').attr('opacity', 1)
      }
    })

  // Update labels to match their rectangles
  svg
    .selectAll('text.source-label, text.destination-label')
    .each(function (d) {
      const label = d3.select(this)
      const isSelected = d.id === selectedId
      const isConnected = connectedIPIds.has(d.id)
      
      if (isSelected || isConnected) {
        label.attr('opacity', 1)
      } else if (selectedId) {
        label.attr('opacity', 0.3)
      } else {
        label.attr('opacity', 1)
      }
    })
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
  transition: stroke-opacity 0.3s ease, stroke-width 0.3s ease, stroke 0.3s ease;
}

.rectangles rect {
  cursor: pointer;
  transition: opacity 0.3s ease, stroke-width 0.3s ease, stroke 0.3s ease;
}

.rectangles rect:hover {
  stroke-width: 3;
}

.badges circle {
  cursor: pointer;
  transition: opacity 0.3s ease;
}

.badges text {
  transition: opacity 0.3s ease;
}

.labels text {
  font-family: system-ui, -apple-system, sans-serif;
  pointer-events: none;
  user-select: none;
  transition: opacity 0.3s ease;
}
</style>
