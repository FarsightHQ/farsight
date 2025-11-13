<template>
  <div class="space-y-3">
    <!-- Key Metrics Grid -->
    <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
      <div
        v-for="(value, key) in formattedMetrics"
        :key="key"
        class="p-3 bg-white rounded-lg border"
        :class="getMetricClass(key, value)"
      >
        <div class="text-xs font-medium text-gray-500 uppercase tracking-wide">
          {{ formatKey(key) }}
        </div>
        <div class="mt-1 text-lg font-semibold" :class="getMetricValueClass(key, value)">
          {{ value }}
        </div>
      </div>
    </div>

    <!-- Expandable Details -->
    <div v-if="hasDetails" class="mt-4">
      <button
        @click="expanded = !expanded"
        class="flex items-center justify-between w-full p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <span class="text-sm font-medium text-gray-700">
          {{ expanded ? 'Hide' : 'Show' }} Details
        </span>
        <ChevronDownIcon
          :class="['h-5 w-5 text-gray-500 transition-transform', expanded && 'rotate-180']"
        />
      </button>

      <Transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 max-h-0"
        enter-to-class="opacity-100 max-h-96"
        leave-active-class="transition-all duration-300 ease-in"
        leave-from-class="opacity-100 max-h-96"
        leave-to-class="opacity-0 max-h-0"
      >
        <div v-if="expanded" class="mt-2 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div class="space-y-2 text-sm">
            <div
              v-for="(value, key) in rawResults"
              :key="key"
              class="flex justify-between py-1 border-b border-gray-200 last:border-0"
            >
              <span class="font-medium text-gray-700 capitalize">{{ formatKey(key) }}:</span>
              <span class="text-gray-600 font-mono text-xs">{{ formatValue(value) }}</span>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  results: {
    type: Object,
    default: () => ({}),
  },
  resultType: {
    type: String,
    default: 'general', // 'ingestion', 'facts', 'hybrid', 'general'
  },
})

const expanded = ref(false)

const formatKey = (key) => {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .toLowerCase()
    .replace(/\b\w/g, (l) => l.toUpperCase())
}

const formatValue = (value) => {
  if (typeof value === 'number') {
    return value.toLocaleString()
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const formatDuration = (ms) => {
  if (typeof ms !== 'number') return ms
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const minutes = Math.floor(ms / 60000)
  const seconds = ((ms % 60000) / 1000).toFixed(1)
  return `${minutes}m ${seconds}s`
}

const rawResults = computed(() => props.results || {})

const formattedMetrics = computed(() => {
  const metrics = {}
  const results = rawResults.value

  // Extract key metrics based on result type
  if (props.resultType === 'ingestion') {
    if (results.rules_created !== undefined) metrics['Rules Created'] = formatNumber(results.rules_created)
    if (results.rules_total !== undefined) metrics['Total Rules'] = formatNumber(results.rules_total)
    if (results.duration_ms !== undefined) metrics['Duration'] = formatDuration(results.duration_ms)
  } else if (props.resultType === 'facts') {
    if (results.rules_updated !== undefined) metrics['Rules Updated'] = formatNumber(results.rules_updated)
    if (results.rules_total !== undefined) metrics['Total Rules'] = formatNumber(results.rules_total)
    if (results.self_flow_count !== undefined) metrics['Self Flows'] = formatNumber(results.self_flow_count)
    if (results.duration_ms !== undefined) metrics['Duration'] = formatDuration(results.duration_ms)
  } else if (props.resultType === 'hybrid') {
    if (results.rules_processed !== undefined) metrics['Rules Processed'] = formatNumber(results.rules_processed)
    if (results.tuples_created !== undefined) metrics['Tuples Created'] = formatNumber(results.tuples_created)
    if (results.duration_ms !== undefined) metrics['Duration'] = formatDuration(results.duration_ms)
  } else {
    // General: show first 6 key metrics
    const keys = Object.keys(results).slice(0, 6)
    keys.forEach((key) => {
      const value = results[key]
      if (key.includes('duration') || key.includes('time')) {
        metrics[formatKey(key)] = formatDuration(value)
      } else if (typeof value === 'number') {
        metrics[formatKey(key)] = formatNumber(value)
      } else {
        metrics[formatKey(key)] = formatValue(value)
      }
    })
  }

  return metrics
})

const formatNumber = (num) => {
  if (typeof num !== 'number') return num
  return num.toLocaleString()
}

const hasDetails = computed(() => {
  return Object.keys(rawResults.value).length > Object.keys(formattedMetrics.value).length
})

const getMetricClass = (key, value) => {
  const keyLower = key.toLowerCase()
  if (keyLower.includes('error') || keyLower.includes('failed')) {
    return 'border-error-200 bg-error-50'
  }
  if (keyLower.includes('warning')) {
    return 'border-warning-200 bg-warning-50'
  }
  return 'border-gray-200'
}

const getMetricValueClass = (key, value) => {
  const keyLower = key.toLowerCase()
  if (keyLower.includes('error') || keyLower.includes('failed')) {
    return 'text-error-700'
  }
  if (keyLower.includes('warning')) {
    return 'text-warning-700'
  }
  if (keyLower.includes('duration') || keyLower.includes('time')) {
    return 'text-primary-700'
  }
  return 'text-gray-900'
}
</script>

