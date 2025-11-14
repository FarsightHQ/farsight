<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <div class="h-8 bg-gray-200 rounded animate-pulse w-1/3"></div>
      <div class="grid grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="h-24 bg-gray-200 rounded animate-pulse"></div>
      </div>
    </div>

    <!-- Request Details -->
    <div v-else-if="request">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold mb-2">{{ request.title }}</h1>
          <div class="flex items-center space-x-4 text-sm text-gray-600">
            <span>ID: {{ request.id }}</span>
            <StatusBadge :status="request.status" />
            <span v-if="request.external_id">External ID: {{ request.external_id }}</span>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <Button
            variant="outline"
            class="text-error-600 border-error-300 hover:bg-error-50"
            @click="handleDeleteClick"
          >
            Delete
          </Button>
          <Button variant="outline" @click="$router.push('/requests')">
            Back to List
          </Button>
        </div>
      </div>

      <!-- Quick Stats -->
      <RequestStats :stats="stats" class="mb-6" />

      <!-- Processing Dashboard -->
      <ProcessingDashboard
        v-if="isProcessingPipeline"
        :steps="pipelineSteps"
        :can-cancel="false"
        class="mb-6"
        @retry="handleRetryStep"
      />
      
      <!-- Polling Status Indicator -->
      <div v-if="isProcessingPipeline && isPolling" class="mb-4 text-xs text-gray-500 flex items-center space-x-2">
        <div class="h-2 w-2 bg-primary-500 rounded-full animate-pulse"></div>
        <span>Live updates active</span>
        <span v-if="lastUpdated" class="text-gray-400">
          • Last updated: {{ formatTime(lastUpdated) }}
        </span>
      </div>

      <!-- Action Buttons (shown when not processing) -->
      <Card v-else class="mb-6">
        <div class="flex items-center space-x-4">
          <Button
            variant="primary"
            :disabled="processing || request.status !== 'submitted'"
            @click="handleIngest"
          >
            <Spinner v-if="processing" size="sm" class="mr-2" />
            Process CSV
          </Button>
          <Button
            variant="secondary"
            :disabled="processing || request.status !== 'ingested'"
            @click="handleComputeFacts"
          >
            <Spinner v-if="processing" size="sm" class="mr-2" />
            Compute Facts
          </Button>
          <Button
            variant="secondary"
            :disabled="processing || request.status !== 'ingested'"
            @click="handleComputeHybrid"
          >
            <Spinner v-if="processing" size="sm" class="mr-2" />
            Compute Hybrid Facts
          </Button>
          <Button
            v-if="request.status === 'submitted'"
            variant="outline"
            @click="startFullPipeline"
          >
            Run Full Pipeline
          </Button>
        </div>
      </Card>

      <!-- Request Metadata -->
      <Card class="mb-6">
        <h2 class="text-lg font-semibold mb-4">Request Information</h2>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="font-medium text-gray-600">Status:</span>
            <span class="ml-2">
              <StatusBadge :status="request.status" />
            </span>
          </div>
          <div>
            <span class="font-medium text-gray-600">Created:</span>
            <span class="ml-2">{{ formatDate(request.created_at) }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-600">File Name:</span>
            <span class="ml-2">{{ request.source_filename }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-600">File Size:</span>
            <span class="ml-2">{{ formatFileSize(request.source_size_bytes) }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-600">SHA256:</span>
            <span class="ml-2 font-mono text-xs">{{ request.source_sha256 }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-600">Created By:</span>
            <span class="ml-2">{{ request.created_by || 'system' }}</span>
          </div>
        </div>
      </Card>

      <!-- Tabs -->
      <Card>
        <RequestTabs
          :tabs="tabs"
          :active-tab="activeTab"
          @update:activeTab="activeTab = $event"
        >
          <template #overview>
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Overview</h3>
              <p class="text-gray-600">
                Request overview and basic information will be displayed here.
              </p>
            </div>
          </template>

          <template #rules>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold">Rules</h3>
                <Button variant="outline" @click="$router.push(`/requests/${request.id}/rules`)">
                  View All Rules
                </Button>
              </div>
              <RuleDetail
                v-if="showRuleDetail && selectedRule"
                :rule="selectedRule"
                :request-id="request.id"
                @back="handleBackToRules"
              />
              <RulesList
                v-else
                :request-id="request.id"
                @view-rule="handleViewRule"
              />
            </div>
          </template>

          <template #analysis>
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Analysis</h3>
              <p class="text-gray-600">
                Analysis and reporting will be implemented in Phase 5.
              </p>
            </div>
          </template>

          <template #visualization>
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Visualization</h3>
              <p class="text-gray-600">
                Network visualization will be implemented in Phase 6.
              </p>
            </div>
          </template>
        </RequestTabs>
      </Card>
    </div>

    <!-- Error State -->
    <Card v-else>
      <div class="text-center py-12">
        <p class="text-gray-600">Request not found</p>
        <Button variant="primary" class="mt-4" @click="$router.push('/requests')">
          Back to Requests
        </Button>
      </div>
    </Card>

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmModal
      v-model="showDeleteModal"
      :request="request"
      :deleting="deleting"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'
import { useRequestStatus } from '@/composables/useRequestStatus'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Spinner from '@/components/ui/Spinner.vue'
import StatusBadge from '@/components/requests/StatusBadge.vue'
import RequestStats from '@/components/requests/RequestStats.vue'
import RequestTabs from '@/components/requests/RequestTabs.vue'
import ProcessingDashboard from '@/components/requests/ProcessingDashboard.vue'
import DeleteConfirmModal from '@/components/requests/DeleteConfirmModal.vue'
import RulesList from '@/components/requests/RulesList.vue'
import RuleDetail from '@/components/requests/RuleDetail.vue'

const route = useRoute()
const router = useRouter()
const { success, error } = useToast()

const loading = ref(false)
const processing = ref(false)
const request = ref(null)
const activeTab = ref('overview')
const isProcessingPipeline = ref(false)
const pipelineSteps = ref([])
const showDeleteModal = ref(false)
const deleting = ref(false)
const selectedRule = ref(null)
const showRuleDetail = ref(false)

// Use request status polling
const requestId = computed(() => route.params.id)
const {
  request: polledRequest,
  startPolling,
  stopPolling,
  lastUpdated,
  isPolling,
} = useRequestStatus(requestId)

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'rules', label: 'Rules' },
  { key: 'analysis', label: 'Analysis' },
  { key: 'visualization', label: 'Visualization' },
]

const stats = computed(() => ({
  totalRules: 0, // Will be populated from API in Phase 4
  totalEndpoints: 0,
  totalServices: 0,
}))

const initializePipelineSteps = () => {
  const now = new Date().toISOString()
  pipelineSteps.value = [
    {
      key: 'upload',
      label: 'Upload',
      status: 'completed',
      progress: 100,
      startedAt: request.value?.created_at || now,
      completedAt: request.value?.created_at || now,
      duration: 0, // Upload is instant
    },
    {
      key: 'ingest',
      label: 'Process CSV',
      status: 'pending',
      progress: 0,
      startedAt: null,
      completedAt: null,
      duration: null,
    },
    {
      key: 'facts',
      label: 'Compute Facts',
      status: 'pending',
      progress: 0,
      startedAt: null,
      completedAt: null,
      duration: null,
    },
    {
      key: 'hybrid',
      label: 'Compute Hybrid',
      status: 'pending',
      progress: 0,
      startedAt: null,
      completedAt: null,
      duration: null,
    },
  ]
}

const updatePipelineStep = (stepKey, updates) => {
  const step = pipelineSteps.value.find((s) => s.key === stepKey)
  if (step) {
    // Track start time if status changes to processing
    if (updates.status === 'processing' && !step.startedAt) {
      updates.startedAt = new Date().toISOString()
    }
    
    // Calculate duration if step is completed
    if (updates.status === 'completed' || updates.status === 'error') {
      if (step.startedAt && !step.completedAt) {
        updates.completedAt = new Date().toISOString()
        const startTime = new Date(step.startedAt).getTime()
        const endTime = new Date(updates.completedAt).getTime()
        updates.duration = endTime - startTime
      }
    }
    
    Object.assign(step, updates)
  }
}

const fetchRequest = async () => {
  loading.value = true
  try {
    const response = await requestsService.get(route.params.id)
    request.value = response.data || response

    // Update polled request
    if (polledRequest.value) {
      polledRequest.value = request.value
    }
  } catch (err) {
    error(err.message || 'Failed to load request')
    request.value = null
  } finally {
    loading.value = false
  }
}

// Watch for route query param to start processing
watch(
  () => route.query.startProcessing,
  (shouldStart) => {
    if (shouldStart === 'true' && request.value?.status === 'submitted') {
      startFullPipeline()
      // Remove query param
      router.replace({ query: {} })
    }
  },
  { immediate: true }
)

// Watch polled request for status updates
watch(
  () => polledRequest.value,
  (newRequest) => {
    if (newRequest && isProcessingPipeline.value) {
      request.value = newRequest
      updatePipelineStatus(newRequest.status)
    }
  }
)

const updatePipelineStatus = (status) => {
  const statusLower = status?.toLowerCase()

  if (statusLower === 'ingested') {
    updatePipelineStep('ingest', {
      status: 'completed',
      progress: 100,
    })
    // Auto-start facts computation
    if (pipelineSteps.value.find((s) => s.key === 'facts')?.status === 'pending') {
      handleComputeFacts(true)
    }
  } else if (statusLower === 'processing') {
    updatePipelineStep('ingest', {
      status: 'processing',
      progress: 50,
    })
  }
}

const startFullPipeline = async () => {
  if (request.value?.status !== 'submitted') {
    error('Request must be in submitted status to start pipeline')
    return
  }

  isProcessingPipeline.value = true
  initializePipelineSteps()
  startPolling(3000) // Poll every 3 seconds

  // Start with CSV ingestion
  await handleIngest(true)
}

const handleIngest = async (isPipeline = false) => {
  if (!isPipeline) {
    processing.value = true
  } else {
    updatePipelineStep('ingest', {
      status: 'processing',
      progress: 0,
      description: 'Processing CSV file and creating firewall rules...',
    })
  }

  try {
    const response = await requestsService.ingest(route.params.id)
    const result = response.data || response

    if (isPipeline) {
      updatePipelineStep('ingest', {
        status: 'processing',
        progress: 75,
        results: {
          'Rules created': result.rules_created || 0,
        },
      })
    } else {
      success('CSV processing started successfully')
    }

    await fetchRequest()
  } catch (err) {
    if (isPipeline) {
      updatePipelineStep('ingest', {
        status: 'error',
        error: err.message || 'Failed to process CSV',
      })
      isProcessingPipeline.value = false
      stopPolling()
    } else {
      error(err.message || 'Failed to process CSV')
    }
  } finally {
    if (!isPipeline) {
      processing.value = false
    }
  }
}

const handleComputeFacts = async (isPipeline = false) => {
  if (!isPipeline) {
    processing.value = true
  } else {
    updatePipelineStep('facts', {
      status: 'processing',
      progress: 0,
      description: 'Computing standard facts for all rules...',
    })
  }

  try {
    const startTime = Date.now()
    const response = await requestsService.computeFacts(route.params.id)
    const result = response.data || response
    const duration = Date.now() - startTime

    if (isPipeline) {
      updatePipelineStep('facts', {
        status: 'completed',
        progress: 100,
        results: {
          rules_updated: result.rules_updated || result.rules_total || 0,
          rules_total: result.rules_total || 0,
          self_flow_count: result.self_flow_count || 0,
          duration_ms: result.duration_ms || duration,
        },
      })
      // Auto-start hybrid facts
      if (pipelineSteps.value.find((s) => s.key === 'hybrid')?.status === 'pending') {
        await handleComputeHybrid(true)
      } else {
        // Pipeline complete
        isProcessingPipeline.value = false
        stopPolling()
        success('Processing pipeline completed successfully!')
      }
    } else {
      success('Facts computation completed successfully')
    }

    await fetchRequest()
  } catch (err) {
    if (isPipeline) {
      updatePipelineStep('facts', {
        status: 'error',
        error: err.message || 'Failed to compute facts',
      })
      isProcessingPipeline.value = false
      stopPolling()
    } else {
      error(err.message || 'Failed to compute facts')
    }
  } finally {
    if (!isPipeline) {
      processing.value = false
    }
  }
}

const handleRetryStep = async (stepKey) => {
  // Reset step status
  const step = pipelineSteps.value.find((s) => s.key === stepKey)
  if (step) {
    step.status = 'pending'
    step.progress = 0
    step.error = null
    step.startedAt = null
    step.completedAt = null
    step.duration = null
    step.results = null
  }

  // Trigger the appropriate handler
  if (stepKey === 'ingest') {
    await handleIngest(isProcessingPipeline.value)
  } else if (stepKey === 'facts') {
    await handleComputeFacts(isProcessingPipeline.value)
  } else if (stepKey === 'hybrid') {
    await handleComputeHybrid(isProcessingPipeline.value)
  }
}

const handleComputeHybrid = async (isPipeline = false) => {
  if (!isPipeline) {
    processing.value = true
  } else {
    updatePipelineStep('hybrid', {
      status: 'processing',
      progress: 0,
      description: 'Computing hybrid facts with selective tuple storage...',
    })
  }

  try {
    const startTime = Date.now()
    const response = await requestsService.computeHybridFacts(route.params.id)
    const result = response.data || response
    const duration = Date.now() - startTime

    if (isPipeline) {
      updatePipelineStep('hybrid', {
        status: 'completed',
        progress: 100,
        results: {
          rules_processed: result.rules_processed || 0,
          tuples_created: result.tuples_created || result.tuples_stored || 0,
          duration_ms: result.duration_ms || duration,
        },
      })
      // Pipeline complete
      isProcessingPipeline.value = false
      stopPolling()
      success('Processing pipeline completed successfully!')
    } else {
      success('Hybrid facts computation completed successfully')
    }

    await fetchRequest()
  } catch (err) {
    if (isPipeline) {
      updatePipelineStep('hybrid', {
        status: 'error',
        error: err.message || 'Failed to compute hybrid facts',
      })
      isProcessingPipeline.value = false
      stopPolling()
    } else {
      error(err.message || 'Failed to compute hybrid facts')
    }
  } finally {
    if (!isPipeline) {
      processing.value = false
    }
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const handleDeleteClick = () => {
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!request.value) return

  deleting.value = true
  try {
    await requestsService.delete(request.value.id)
    success(`Request "${request.value.title}" deleted successfully`)
    
    // Redirect to list page
    router.push('/requests')
  } catch (err) {
    error(err.message || 'Failed to delete request')
    deleting.value = false
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const handleViewRule = async (rule) => {
  // Navigate to standalone rule detail page
  router.push(`/rules/${rule.id}`)
}

const handleBackToRules = () => {
  showRuleDetail.value = false
  selectedRule.value = null
}

onMounted(() => {
  fetchRequest()
  initializePipelineSteps()
})
</script>
