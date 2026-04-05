<template>
  <Modal
    :model-value="modelValue"
    size="full"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div>
          <h3 class="text-xl font-semibold text-gray-900">Network Topology Visualization</h3>
          <p v-if="ruleTitle" class="text-sm text-gray-600 mt-1">{{ ruleTitle }}</p>
          <p v-else-if="requestTitle" class="text-sm text-gray-600 mt-1">{{ requestTitle }}</p>
        </div>
        <div v-if="summary" class="flex items-center space-x-6 text-sm">
          <div v-if="summary.rule_count" class="text-center">
            <div class="font-semibold text-gray-900">{{ summary.rule_count || 0 }}</div>
            <div class="text-gray-600">Rules</div>
          </div>
          <div class="text-center">
            <div class="font-semibold text-gray-900">{{ summary.source_count || 0 }}</div>
            <div class="text-gray-600">Sources</div>
          </div>
          <div class="text-center">
            <div class="font-semibold text-gray-900">{{ summary.destination_count || 0 }}</div>
            <div class="text-gray-600">Destinations</div>
          </div>
          <div class="text-center">
            <div class="font-semibold text-gray-900">{{ summary.service_count || 0 }}</div>
            <div class="text-gray-600">Services</div>
          </div>
        </div>
      </div>
    </template>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center h-96">
      <div class="text-center">
        <Spinner size="lg" class="mx-auto mb-4" />
        <p class="text-gray-600">Loading network topology...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center h-96">
      <div class="text-center max-w-md">
        <ExclamationTriangleIcon class="h-12 w-12 text-error-500 mx-auto mb-4" />
        <h4 class="text-lg font-semibold text-gray-900 mb-2">Failed to Load Topology</h4>
        <p class="text-gray-600 mb-2">{{ error }}</p>
        <p v-if="ruleId" class="text-sm text-gray-500 mb-4">Rule ID: {{ ruleId }}</p>
        <Button variant="primary" @click="fetchTopology">Retry</Button>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="
        !graphData ||
        !graphData.sources ||
        graphData.sources.length === 0 ||
        !graphData.destinations ||
        graphData.destinations.length === 0
      "
      class="flex items-center justify-center h-96"
    >
      <div class="text-center max-w-md">
        <InformationCircleIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h4 class="text-lg font-semibold text-gray-900 mb-2">No Network Data</h4>
        <p class="text-gray-600 mb-2">{{ emptyStateMessage }}</p>
        <p v-if="ruleId" class="text-sm text-gray-500">Rule ID: {{ ruleId }}</p>
      </div>
    </div>

    <!-- Graph Visualization -->
    <div v-else class="w-full min-h-[600px]">
      <NetworkGraph :graph-data="graphData" />
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <div class="text-xs text-gray-500">
          <p>
            Hover over elements to see details • Port count badges show number of ports per
            connection
          </p>
        </div>
        <Button variant="outline" @click="$emit('update:modelValue', false)">Close</Button>
      </div>
    </template>
  </Modal>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/vue/24/outline'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Spinner from '@/components/ui/Spinner.vue'
import NetworkGraph from './NetworkGraph.vue'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  ruleId: {
    type: [String, Number],
    default: null,
  },
  ruleTitle: {
    type: String,
    default: '',
  },
  // Optional: keep requestId for backward compatibility
  requestId: {
    type: [String, Number],
    default: null,
  },
  requestTitle: {
    type: String,
    default: '',
  },
  graphData: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:modelValue'])

const { error: showError } = useToast()

const loading = ref(false)
const error = ref(null)
const graphData = ref(null)
const summary = ref(null)
const emptyStateMessage = ref('This rule has no network topology data to visualize.')

const fetchTopology = async () => {
  // If graphData is provided directly, use it
  if (props.graphData) {
    graphData.value = props.graphData
    summary.value = {
      rule_count: props.graphData.metadata?.rule_count || 0,
      source_count: props.graphData.metadata?.source_count || 0,
      destination_count: props.graphData.metadata?.destination_count || 0,
      service_count: props.graphData.metadata?.service_count || 0,
    }
    loading.value = false
    return
  }

  // Prioritize ruleId over requestId
  const id = props.ruleId || props.requestId
  if (!id) return

  loading.value = true
  error.value = null

  try {
    let response
    let responseData

    if (props.ruleId) {
      // Debug logging
      console.log('[NetworkGraphModal] Fetching graph for rule:', props.ruleId)

      // Fetch rule-specific graph data
      response = await requestsService.getRuleGraph(props.ruleId)

      // Debug logging - log full response structure
      console.log('[NetworkGraphModal] Full API response:', response)

      // Extract response data - handle multiple wrapper formats
      let data = response
      if (response.data) {
        data = response.data
        // Check if there's another nested data layer
        if (data.data) {
          data = data.data
        }
      }
      responseData = data

      // Debug logging - log extracted responseData
      console.log('[NetworkGraphModal] Extracted responseData:', responseData)
      console.log('[NetworkGraphModal] responseData.graph:', responseData.graph)

      // Graph data is nested in responseData.graph when include=graph
      if (responseData.graph) {
        const graph = responseData.graph

        // Validate graph structure
        if (!graph.sources || !Array.isArray(graph.sources)) {
          console.error('[NetworkGraphModal] Graph missing sources array:', graph)
          error.value = `Invalid graph data: missing sources array for rule ${props.ruleId}`
          graphData.value = null
          summary.value = null
          emptyStateMessage.value = 'Graph data structure is invalid (missing sources).'
          return
        }

        if (!graph.destinations || !Array.isArray(graph.destinations)) {
          console.error('[NetworkGraphModal] Graph missing destinations array:', graph)
          error.value = `Invalid graph data: missing destinations array for rule ${props.ruleId}`
          graphData.value = null
          summary.value = null
          emptyStateMessage.value = 'Graph data structure is invalid (missing destinations).'
          return
        }

        // Check if arrays are empty
        if (graph.sources.length === 0) {
          console.warn('[NetworkGraphModal] Graph has empty sources array')
          emptyStateMessage.value = 'This rule has no source networks to visualize.'
          graphData.value = graph
          summary.value = {
            rule_count: 1,
            source_count: 0,
            destination_count: graph.destinations.length || 0,
            service_count: graph.metadata?.service_count || graph.connections?.length || 0,
          }
          return
        }

        if (graph.destinations.length === 0) {
          console.warn('[NetworkGraphModal] Graph has empty destinations array')
          emptyStateMessage.value = 'This rule has no destination networks to visualize.'
          graphData.value = graph
          summary.value = {
            rule_count: 1,
            source_count: graph.sources.length || 0,
            destination_count: 0,
            service_count: graph.metadata?.service_count || graph.connections?.length || 0,
          }
          return
        }

        // New flow-style format: sources, destinations, connections
        graphData.value = graph
        summary.value = {
          rule_count: 1,
          source_count: graph.metadata?.source_count || graph.sources.length || 0,
          destination_count: graph.metadata?.destination_count || graph.destinations.length || 0,
          service_count:
            graph.metadata?.service_count ||
            graph.connections?.reduce((sum, conn) => sum + (conn.port_count || 0), 0) ||
            0,
        }

        console.log('[NetworkGraphModal] Successfully loaded graph data:', {
          sources: graph.sources.length,
          destinations: graph.destinations.length,
          connections: graph.connections?.length || 0,
        })
      } else if (responseData.topology) {
        // Fallback for request-level topology format (old format)
        graphData.value = responseData
        summary.value = responseData.summary || {
          source_count: responseData.endpoints?.source_count || 0,
          destination_count: responseData.endpoints?.destination_count || 0,
          service_count: responseData.service_count || 0,
        }
      } else {
        // Check if responseData itself has the graph structure (direct format)
        if (
          responseData.sources &&
          Array.isArray(responseData.sources) &&
          responseData.destinations &&
          Array.isArray(responseData.destinations)
        ) {
          console.log('[NetworkGraphModal] Found graph data in direct format')
          graphData.value = responseData
          summary.value = {
            rule_count: 1,
            source_count: responseData.sources.length || 0,
            destination_count: responseData.destinations.length || 0,
            service_count:
              responseData.metadata?.service_count || responseData.connections?.length || 0,
          }
        } else {
          console.error('[NetworkGraphModal] No graph data found in response:', responseData)
          error.value = `No graph data available for rule ${props.ruleId}. The rule may not have any endpoints or services.`
          graphData.value = null
          summary.value = null
          emptyStateMessage.value = 'This rule has no source or destination networks to visualize.'
        }
      }
    } else {
      // Fallback to request-level topology
      response = await requestsService.getNetworkTopology(props.requestId)
      const data = response.data || response
      responseData = data.data || data

      if (responseData.error) {
        error.value = responseData.error || 'No network topology data available'
        graphData.value = null
        summary.value = null
      } else {
        graphData.value = responseData
        summary.value = responseData.summary || {
          total_rules: responseData.topology?.metadata?.rule_count || 0,
          network_nodes: responseData.topology?.metadata?.network_count || 0,
          connections:
            responseData.topology?.metadata?.connection_count ||
            responseData.topology?.links?.length ||
            0,
        }
      }
    }
  } catch (err) {
    error.value = err.message || 'Failed to load network topology'
    graphData.value = null
    summary.value = null
    showError(error.value)
  } finally {
    loading.value = false
  }
}

// Watch for modal opening
watch(
  () => props.modelValue,
  isOpen => {
    if (isOpen && (props.ruleId || props.requestId)) {
      fetchTopology()
    }
  },
  { immediate: true }
)

// Watch for ruleId changes
watch(
  () => props.ruleId,
  newId => {
    if (props.modelValue && newId) {
      fetchTopology()
    }
  }
)

// Watch for requestId changes (backward compatibility)
watch(
  () => props.requestId,
  newId => {
    if (props.modelValue && newId && !props.ruleId) {
      fetchTopology()
    }
  }
)

// Watch for graphData prop changes
watch(
  () => props.graphData,
  newData => {
    if (newData && props.modelValue) {
      graphData.value = newData
      summary.value = {
        rule_count: newData.metadata?.rule_count || 0,
        source_count: newData.metadata?.source_count || 0,
        destination_count: newData.metadata?.destination_count || 0,
        service_count: newData.metadata?.service_count || 0,
      }
      loading.value = false
      error.value = null
    }
  },
  { immediate: true, deep: true }
)
</script>
