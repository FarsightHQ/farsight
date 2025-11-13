<template>
  <div class="space-y-4">
    <!-- Current Step Info -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ currentStep?.label }}</h3>
        <p class="text-sm text-gray-600">{{ currentStep?.description || 'Processing...' }}</p>
      </div>
      <StatusBadge :status="currentStep?.status || 'processing'" />
    </div>

    <!-- Progress Bar -->
    <div v-if="currentStep?.status === 'processing'">
      <div class="flex items-center justify-between text-sm text-gray-600 mb-1">
        <span>Progress</span>
        <span>{{ currentStep?.progress || 0 }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-primary-600 h-2 rounded-full transition-all duration-300"
          :style="{ width: `${currentStep?.progress || 0}%` }"
        ></div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="currentStep?.results && Object.keys(currentStep.results).length > 0" class="mt-4">
      <h4 class="text-sm font-medium text-gray-900 mb-3">Results:</h4>
      <ResultsSummary
        :results="currentStep.results"
        :result-type="getResultType(currentStep.key)"
      />
    </div>

    <!-- Error Message -->
    <div v-if="currentStep?.error" class="mt-4 p-4 bg-error-50 border border-error-200 rounded-lg">
      <div class="flex items-start justify-between">
        <div class="flex-1">
          <h5 class="text-sm font-medium text-error-800 mb-1">Error Details:</h5>
          <p class="text-sm text-error-700 whitespace-pre-wrap">{{ currentStep.error }}</p>
          <button
            v-if="currentStep.error"
            @click="copyError(currentStep.error)"
            class="mt-2 text-xs text-error-600 hover:text-error-800 flex items-center space-x-1"
          >
            <DocumentDuplicateIcon class="h-4 w-4" />
            <span>Copy error message</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Warnings -->
    <div v-if="currentStep?.warnings && currentStep.warnings.length > 0" class="mt-4">
      <h5 class="text-sm font-medium text-warning-700 mb-2">Warnings:</h5>
      <div class="space-y-2">
        <div
          v-for="(warning, idx) in currentStep.warnings"
          :key="idx"
          class="p-3 bg-warning-50 border border-warning-200 rounded-lg text-sm text-warning-700"
        >
          {{ warning }}
        </div>
      </div>
    </div>

    <!-- Duration Display -->
    <div v-if="currentStep?.duration" class="mt-4 text-sm text-gray-600">
      <span class="font-medium">Duration:</span>
      <span class="ml-2">{{ formatDuration(currentStep.duration) }}</span>
    </div>
  </div>
</template>

<script setup>
import { DocumentDuplicateIcon } from '@heroicons/vue/24/outline'
import StatusBadge from './StatusBadge.vue'
import ResultsSummary from './ResultsSummary.vue'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  currentStep: {
    type: Object,
    default: null,
  },
})

const { success } = useToast()

const getResultType = (stepKey) => {
  if (!stepKey) return 'general'
  if (stepKey === 'ingest') return 'ingestion'
  if (stepKey === 'facts') return 'facts'
  if (stepKey === 'hybrid') return 'hybrid'
  return 'general'
}

const formatDuration = (duration) => {
  if (typeof duration === 'number') {
    if (duration < 1000) return `${duration}ms`
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`
    const minutes = Math.floor(duration / 60000)
    const seconds = ((duration % 60000) / 1000).toFixed(1)
    return `${minutes}m ${seconds}s`
  }
  return duration || 'N/A'
}

const copyError = async (errorText) => {
  try {
    await navigator.clipboard.writeText(errorText)
    success('Error message copied to clipboard')
  } catch (err) {
    console.error('Failed to copy error:', err)
  }
}
</script>

