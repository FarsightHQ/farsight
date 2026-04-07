import { ref, watch, computed } from 'vue'
import { requestsService } from '@/services/requests'
import { useRequestStatus } from '@/composables/useRequestStatus'
import { useToast } from '@/composables/useToast'

export function usePipeline(requestId, request = null) {
  const { success, error } = useToast()
  const pipelineSteps = ref([])
  const isProcessingPipeline = ref(false)
  const processing = ref(false)

  // Use request status polling if requestId is provided
  const requestIdComputed = computed(() => {
    // Log what we receive
    console.log(
      '[usePipeline] requestIdComputed - requestId:',
      requestId,
      'Type:',
      typeof requestId
    )

    let id
    if (typeof requestId === 'function') {
      // If it's a function (like a computed ref), call it
      id = requestId()
    } else if (requestId && typeof requestId === 'object' && 'value' in requestId) {
      // If it's a ref, get its value
      id = requestId.value
    } else {
      // Otherwise use as-is
      id = requestId
    }

    console.log('[usePipeline] requestIdComputed - extracted id:', id, 'Type:', typeof id)

    // If id is an object, extract the ID property
    if (typeof id === 'object' && id !== null) {
      id = id.id || id.request_id || String(id)
      console.log('[usePipeline] requestIdComputed - after object extraction:', id)
    }

    // Ensure it's a string or number, return null if invalid
    if (id === null || id === undefined) {
      console.warn('[usePipeline] requestIdComputed - null/undefined ID')
      return null
    }

    // Convert to string for consistency (API expects string/number)
    const stringId = String(id)

    // Validate it's not an invalid string representation
    if (
      stringId === 'null' ||
      stringId === 'undefined' ||
      stringId === '[object Object]' ||
      stringId === 'NaN'
    ) {
      console.warn('[usePipeline] Invalid request ID string:', stringId, 'Original:', id)
      return null
    }

    console.log('[usePipeline] requestIdComputed - final stringId:', stringId)
    return stringId
  })

  const {
    request: polledRequest,
    startPolling,
    stopPolling,
    lastUpdated,
    isPolling,
    fetchStatus,
  } = useRequestStatus(requestIdComputed)

  // 1. Utility functions - initializePipelineSteps
  const initializePipelineSteps = (createdAt = null) => {
    const now = new Date().toISOString()
    pipelineSteps.value = [
      {
        key: 'upload',
        label: 'Upload',
        status: 'completed',
        progress: 100,
        startedAt: createdAt || now,
        completedAt: createdAt || now,
        duration: 0,
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

  // 2. Utility functions - updatePipelineStep
  const updatePipelineStep = (stepKey, updates) => {
    const step = pipelineSteps.value.find(s => s.key === stepKey)
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

  // 3. fetchRequest - used by handlers
  const fetchRequest = async () => {
    const id = requestIdComputed.value
    if (!id || id === 'null' || id === 'undefined' || id === '[object Object]' || id === 'NaN') {
      console.warn('[usePipeline] Invalid request ID for fetchRequest:', id)
      return null
    }

    try {
      const response = await requestsService.get(id)
      const result = response.data || response

      if (request && typeof request.value !== 'undefined') {
        request.value = result
      }

      // Update polled request
      if (polledRequest.value) {
        polledRequest.value = result
      }

      return result
    } catch (err) {
      error(err.message || 'Failed to load request')
      return null
    }
  }

  // 4. Handler functions - handleIngest
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

    const id = requestIdComputed.value
    if (!id || id === 'null' || id === 'undefined' || id === '[object Object]' || id === 'NaN') {
      throw new Error(`Invalid request ID for ingestion: ${id}`)
    }

    try {
      const response = await requestsService.ingest(id)
      const result = response.data || response

      if (isPipeline) {
        updatePipelineStep('ingest', {
          status: 'processing',
          progress: 75,
          results: {
            'Rules created': result.rules_created || 0,
          },
        })

        // Immediately check status after API call
        const updatedRequest = await fetchRequest()
        if (updatedRequest?.status?.toLowerCase() === 'ingested') {
          updatePipelineStep('ingest', {
            status: 'completed',
            progress: 100,
          })
          // Auto-start facts computation
          if (pipelineSteps.value.find(s => s.key === 'facts')?.status === 'pending') {
            handleComputeFacts(true)
          }
        }
      } else {
        success('CSV processing started successfully')
        await fetchRequest()
      }
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
      throw err
    } finally {
      if (!isPipeline) {
        processing.value = false
      }
    }
  }

  // 5. Handler functions - handleComputeFacts
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

    const id = requestIdComputed.value
    if (!id || id === 'null' || id === 'undefined' || id === '[object Object]' || id === 'NaN') {
      throw new Error(`Invalid request ID for facts computation: ${id}`)
    }

    try {
      const startTime = Date.now()
      const response = await requestsService.computeFacts(id)
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
        if (pipelineSteps.value.find(s => s.key === 'hybrid')?.status === 'pending') {
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
      throw err
    } finally {
      if (!isPipeline) {
        processing.value = false
      }
    }
  }

  // 6. Handler functions - handleComputeHybrid
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

    const id = requestIdComputed.value
    if (!id || id === 'null' || id === 'undefined' || id === '[object Object]' || id === 'NaN') {
      throw new Error(`Invalid request ID for hybrid facts computation: ${id}`)
    }

    try {
      const startTime = Date.now()
      const response = await requestsService.computeHybridFacts(id)
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
      throw err
    } finally {
      if (!isPipeline) {
        processing.value = false
      }
    }
  }

  // 7. updatePipelineStatus - defined AFTER handlers so it can call them
  const updatePipelineStatus = status => {
    const statusLower = status?.toLowerCase()
    const ingestStep = pipelineSteps.value.find(s => s.key === 'ingest')

    if (statusLower === 'ingested') {
      // Only update if not already completed
      if (ingestStep?.status !== 'completed') {
        updatePipelineStep('ingest', {
          status: 'completed',
          progress: 100,
        })
        // Auto-start facts computation
        if (pipelineSteps.value.find(s => s.key === 'facts')?.status === 'pending') {
          handleComputeFacts(true)
        }
      }
    } else if (statusLower === 'processing') {
      // Don't downgrade progress if it's already higher
      const currentProgress = ingestStep?.progress || 0
      if (currentProgress < 50) {
        updatePipelineStep('ingest', {
          status: 'processing',
          progress: 50,
        })
      }
    }
  }

  // 8. Watch for polled request - defined AFTER updatePipelineStatus
  watch(
    () => polledRequest.value,
    newRequest => {
      if (newRequest && isProcessingPipeline.value) {
        if (request && typeof request.value !== 'undefined') {
          request.value = newRequest
        }
        updatePipelineStatus(newRequest.status)
      }
    }
  )

  // 9. handleRetryStep
  const handleRetryStep = async stepKey => {
    // Reset step status
    const step = pipelineSteps.value.find(s => s.key === stepKey)
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

  // 10. startFullPipeline
  const startFullPipeline = async (currentRequest = null) => {
    const requestStatus = currentRequest?.status || request?.value?.status

    if (requestStatus !== 'submitted') {
      error('Request must be in submitted status to start pipeline')
      return false
    }

    isProcessingPipeline.value = true
    initializePipelineSteps(currentRequest?.created_at || request?.value?.created_at)
    startPolling(3000) // Poll every 3 seconds

    // Start with CSV ingestion
    try {
      await handleIngest(true)
      return true
    } catch (err) {
      return false
    }
  }

  return {
    // State
    pipelineSteps,
    isProcessingPipeline,
    processing,
    polledRequest,
    lastUpdated,
    isPolling,

    // Methods
    initializePipelineSteps,
    updatePipelineStep,
    updatePipelineStatus,
    fetchRequest,
    startFullPipeline,
    handleIngest,
    handleComputeFacts,
    handleComputeHybrid,
    handleRetryStep,
    startPolling,
    stopPolling,
  }
}
