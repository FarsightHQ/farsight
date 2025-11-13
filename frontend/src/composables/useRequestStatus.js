import { ref, onUnmounted } from 'vue'
import { requestsService } from '@/services/requests'

export function useRequestStatus(requestId) {
  const request = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const pollingInterval = ref(null)
  const lastUpdated = ref(null)
  const consecutiveErrors = ref(0)
  const isPolling = ref(false)

  const fetchStatus = async () => {
    const id = typeof requestId === 'function' ? requestId.value : requestId
    if (!id) return

    loading.value = true
    error.value = null

    try {
      const response = await requestsService.get(id)
      request.value = response.data || response
      lastUpdated.value = new Date().toISOString()
      consecutiveErrors.value = 0 // Reset error count on success
    } catch (err) {
      consecutiveErrors.value++
      error.value = err.message || 'Failed to fetch request status'
      
      // Exponential backoff: increase interval on consecutive errors
      if (consecutiveErrors.value > 3) {
        stopPolling()
        console.warn('Too many consecutive polling errors, stopping poll')
      }
    } finally {
      loading.value = false
    }
  }

  const startPolling = (interval = 3000) => {
    if (pollingInterval.value) return

    isPolling.value = true
    consecutiveErrors.value = 0

    // Fetch immediately
    fetchStatus()

    // Then poll at interval
    pollingInterval.value = setInterval(() => {
      fetchStatus()
    }, interval)
  }

  const stopPolling = () => {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
    isPolling.value = false
  }

  const isProcessing = () => {
    if (!request.value) return false
    const status = request.value.status?.toLowerCase()
    return ['processing', 'ingesting'].includes(status)
  }

  const isComplete = () => {
    if (!request.value) return false
    const status = request.value.status?.toLowerCase()
    return ['ingested', 'completed'].includes(status)
  }

  const hasError = () => {
    if (!request.value) return false
    const status = request.value.status?.toLowerCase()
    return ['error', 'failed'].includes(status)
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stopPolling()
  })

  return {
    request,
    loading,
    error,
    lastUpdated,
    isPolling,
    fetchStatus,
    startPolling,
    stopPolling,
    isProcessing,
    isComplete,
    hasError,
  }
}

