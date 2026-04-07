<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-medium text-gray-900">Processing History</h3>
      <button
        v-if="hasCompletedSteps"
        class="text-xs text-primary-600 hover:text-primary-700 font-medium"
        @click="expanded = !expanded"
      >
        {{ expanded ? 'Collapse All' : 'Expand All' }}
      </button>
    </div>

    <div class="relative">
      <!-- Timeline Line -->
      <div
        class="absolute left-5 top-0 bottom-0 w-0.5"
        :class="hasCompletedSteps ? 'bg-primary-600' : 'bg-gray-300'"
      ></div>

      <!-- Timeline Items -->
      <div class="space-y-4">
        <div v-for="(step, index) in steps" :key="step.key" class="relative pl-12">
          <!-- Timeline Dot -->
          <div
            class="absolute left-0 top-1 h-10 w-10 rounded-full flex items-center justify-center border-2 z-10"
            :class="getStepDotClass(step)"
          >
            <CheckIcon v-if="step.status === 'completed'" class="h-5 w-5 text-white" />
            <XMarkIcon v-else-if="step.status === 'error'" class="h-5 w-5 text-white" />
            <Spinner v-else-if="step.status === 'processing'" size="sm" color="white" />
            <span v-else class="text-xs font-medium text-gray-400">{{ index + 1 }}</span>
          </div>

          <!-- Step Content -->
          <div
            class="bg-white border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow"
            :class="getStepCardClass(step)"
            @click="toggleStep(step.key)"
          >
            <!-- Step Header -->
            <div class="flex items-center justify-between">
              <div class="flex-1">
                <div class="flex items-center space-x-2">
                  <h4 class="text-sm font-semibold text-gray-900">{{ step.label }}</h4>
                  <StatusBadge :status="step.status" size="sm" />
                </div>
                <div class="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                  <span v-if="step.startedAt">
                    Started: {{ formatTimestamp(step.startedAt) }}
                  </span>
                  <span v-if="step.completedAt">
                    Completed: {{ formatTimestamp(step.completedAt) }}
                  </span>
                  <span v-if="step.duration" class="font-medium text-gray-700">
                    Duration: {{ formatDuration(step.duration) }}
                  </span>
                </div>
              </div>
              <ChevronDownIcon
                v-if="hasStepDetails(step)"
                :class="[
                  'h-5 w-5 text-gray-400 transition-transform',
                  expandedSteps.has(step.key) && 'rotate-180',
                ]"
              />
            </div>

            <!-- Step Details (Expandable) -->
            <Transition
              enter-active-class="transition-all duration-300 ease-out"
              enter-from-class="opacity-0 max-h-0"
              enter-to-class="opacity-100 max-h-96"
              leave-active-class="transition-all duration-300 ease-in"
              leave-from-class="opacity-100 max-h-96"
              leave-to-class="opacity-0 max-h-0"
            >
              <div v-if="expandedSteps.has(step.key) || expanded" class="mt-4 pt-4 border-t">
                <!-- Progress (if processing) -->
                <div
                  v-if="step.status === 'processing' && step.progress !== undefined"
                  class="mb-4"
                >
                  <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{{ step.progress }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div
                      class="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      :style="{ width: `${step.progress}%` }"
                    ></div>
                  </div>
                </div>

                <!-- Description -->
                <p v-if="step.description" class="text-sm text-gray-600 mb-4">
                  {{ step.description }}
                </p>

                <!-- Results Summary -->
                <div v-if="step.results && Object.keys(step.results).length > 0" class="mb-4">
                  <h5 class="text-xs font-medium text-gray-700 mb-2">Results:</h5>
                  <ResultsSummary :results="step.results" :result-type="getResultType(step.key)" />
                </div>

                <!-- Error Details -->
                <div
                  v-if="step.error"
                  class="mt-4 p-3 bg-error-50 border border-error-200 rounded-lg"
                >
                  <div class="flex items-start justify-between">
                    <div class="flex-1">
                      <h5 class="text-xs font-medium text-error-800 mb-1">Error:</h5>
                      <p class="text-sm text-error-700">{{ step.error }}</p>
                    </div>
                    <button
                      class="ml-2 text-error-600 hover:text-error-800"
                      title="Copy error message"
                      @click.stop="copyError(step.error)"
                    >
                      <DocumentDuplicateIcon class="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <!-- Warnings -->
                <div v-if="step.warnings && step.warnings.length > 0" class="mt-4">
                  <h5 class="text-xs font-medium text-warning-700 mb-2">Warnings:</h5>
                  <div class="space-y-2">
                    <div
                      v-for="(warning, idx) in step.warnings"
                      :key="idx"
                      class="p-2 bg-warning-50 border border-warning-200 rounded text-sm text-warning-700"
                    >
                      {{ warning }}
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  CheckIcon,
  XMarkIcon,
  ChevronDownIcon,
  DocumentDuplicateIcon,
} from '@heroicons/vue/24/outline'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import Spinner from '@/components/ui/Spinner.vue'
import ResultsSummary from './ResultsSummary.vue'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  steps: {
    type: Array,
    required: true,
  },
})

const { success } = useToast()
const expandedSteps = ref(new Set())
const expanded = ref(false)

const hasCompletedSteps = computed(() => {
  return props.steps.some(s => s.status === 'completed' || s.status === 'error')
})

const toggleStep = stepKey => {
  if (expandedSteps.value.has(stepKey)) {
    expandedSteps.value.delete(stepKey)
  } else {
    expandedSteps.value.add(stepKey)
  }
}

const hasStepDetails = step => {
  return (
    step.description ||
    (step.results && Object.keys(step.results).length > 0) ||
    step.error ||
    (step.warnings && step.warnings.length > 0) ||
    (step.status === 'processing' && step.progress !== undefined)
  )
}

const getStepDotClass = step => {
  if (step.status === 'completed') {
    return 'bg-primary-600 border-primary-600'
  } else if (step.status === 'error') {
    return 'bg-error-600 border-error-600'
  } else if (step.status === 'processing') {
    return 'bg-primary-500 border-primary-500 animate-pulse'
  } else {
    return 'bg-white border-gray-300'
  }
}

const getStepCardClass = step => {
  if (step.status === 'error') {
    return 'border-error-200'
  } else if (step.status === 'completed') {
    return 'border-primary-200'
  } else if (step.status === 'processing') {
    return 'border-primary-300 shadow-sm'
  } else {
    return 'border-gray-200'
  }
}

const formatTimestamp = timestamp => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const formatDuration = duration => {
  if (typeof duration === 'number') {
    if (duration < 1000) return `${duration}ms`
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`
    const minutes = Math.floor(duration / 60000)
    const seconds = ((duration % 60000) / 1000).toFixed(1)
    return `${minutes}m ${seconds}s`
  }
  return duration || 'N/A'
}

const getResultType = stepKey => {
  if (stepKey === 'ingest') return 'ingestion'
  if (stepKey === 'facts') return 'facts'
  if (stepKey === 'hybrid') return 'hybrid'
  return 'general'
}

const copyError = async errorText => {
  try {
    await navigator.clipboard.writeText(errorText)
    success('Error message copied to clipboard')
  } catch (err) {
    console.error('Failed to copy error:', err)
  }
}
</script>
