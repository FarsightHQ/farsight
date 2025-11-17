<template>
  <Modal :model-value="modelValue" size="full" @update:model-value="$emit('update:modelValue', $event)">
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div>
          <h3 class="text-xl font-semibold text-gray-900">Network Topology Visualization</h3>
          <p v-if="ruleTitle" class="text-sm text-gray-600 mt-1">{{ ruleTitle }}</p>
          <p v-else-if="requestTitle" class="text-sm text-gray-600 mt-1">{{ requestTitle }}</p>
        </div>
        <div v-if="summary" class="flex items-center space-x-6 text-sm">
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
        <p class="text-gray-600 mb-4">{{ error }}</p>
        <Button variant="primary" @click="fetchTopology">Retry</Button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!graphData || !graphData.topology || !graphData.topology.nodes || graphData.topology.nodes.length === 0" class="flex items-center justify-center h-96">
      <div class="text-center max-w-md">
        <InformationCircleIcon class="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h4 class="text-lg font-semibold text-gray-900 mb-2">No Network Data</h4>
        <p class="text-gray-600">This rule has no network topology data to visualize.</p>
      </div>
    </div>

    <!-- Graph Visualization -->
    <div v-else class="h-[calc(100vh-12rem)] min-h-[600px]">
      <NetworkGraph :graph-data="graphData.topology" />
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <div class="text-xs text-gray-500">
          <p>Drag nodes to reposition • Click nodes to highlight connections • Use controls to zoom/pan</p>
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
})

const emit = defineEmits(['update:modelValue'])

const { error: showError } = useToast()

const loading = ref(false)
const error = ref(null)
const graphData = ref(null)
const summary = ref(null)

const fetchTopology = async () => {
  // Prioritize ruleId over requestId
  const id = props.ruleId || props.requestId
  if (!id) return

  loading.value = true
  error.value = null

  try {
    let response
    let responseData

    if (props.ruleId) {
      // Fetch rule-specific graph data
      response = await requestsService.getRuleGraph(props.ruleId)
      const data = response.data || response
      responseData = data.data || data

      // Graph data is nested in responseData.graph when include=graph
      if (responseData.graph) {
        graphData.value = {
          topology: responseData.graph,
        }
        summary.value = {
          source_count: responseData.endpoints?.source_count || 0,
          destination_count: responseData.endpoints?.destination_count || 0,
          service_count: responseData.service_count || 0,
        }
      } else if (responseData.topology) {
        // Fallback for request-level topology format
        graphData.value = responseData
        summary.value = responseData.summary || {
          source_count: responseData.endpoints?.source_count || 0,
          destination_count: responseData.endpoints?.destination_count || 0,
          service_count: responseData.service_count || 0,
        }
      } else {
        error.value = 'No graph data available for this rule'
        graphData.value = null
        summary.value = null
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
          connections: responseData.topology?.metadata?.connection_count || responseData.topology?.links?.length || 0,
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
  (isOpen) => {
    if (isOpen && (props.ruleId || props.requestId)) {
      fetchTopology()
    }
  },
  { immediate: true }
)

// Watch for ruleId changes
watch(
  () => props.ruleId,
  (newId) => {
    if (props.modelValue && newId) {
      fetchTopology()
    }
  }
)

// Watch for requestId changes (backward compatibility)
watch(
  () => props.requestId,
  (newId) => {
    if (props.modelValue && newId && !props.ruleId) {
      fetchTopology()
    }
  }
)
</script>

