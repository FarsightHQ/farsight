import { ref, onUnmounted } from 'vue'
import { requestsService } from '@/services/requests'

export function useRequestStatus(requestId) {
  const request = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const pollingInterval = ref(null)

  const fetchStatus = async () => {
    const id = typeof requestId === 'function' ? requestId.value : requestId
    if (!id) return

    loading.value = true
    error.value = null

    try {
      const response = await requestsService.get(id)
      request.value = response.data || response
    } catch (err) {
      error.value = err.message || 'Failed to fetch request status'
    } finally {
      loading.value = false
    }
  }

  const startPolling = (interval = 3000) => {
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
    fetchStatus,
    startPolling,
    stopPolling,
    isProcessing,
    isComplete,
    hasError,
  }
}

