<template>
  <div class="space-y-4">
    <!-- Health Status Badge (if available) - Show in major facts only -->
    <div v-if="facts?.health_status && !showOnlyDetailed" class="flex items-center justify-start">
      <Card
        :class="[
          'p-3 inline-flex items-center space-x-2',
          getHealthStatusClass(facts.health_status),
        ]"
      >
        <component
          :is="getHealthStatusIcon(facts.health_status)"
          :class="['h-5 w-5', getHealthStatusIconClass(facts.health_status)]"
        />
        <div>
          <p class="text-xs font-medium">Health Status</p>
          <p :class="['text-sm font-semibold', getHealthStatusTextClass(facts.health_status)]">
            {{ formatHealthStatus(facts.health_status) }}
          </p>
        </div>
        <span
          v-if="facts.tuple_summary?.problem_count > 0"
          :class="[
            'ml-2 px-2 py-1 rounded-full text-xs font-medium',
            getHealthStatusBadgeClass(facts.health_status),
          ]"
        >
          {{ facts.tuple_summary.problem_count }} problem{{
            facts.tuple_summary.problem_count !== 1 ? 's' : ''
          }}
        </span>
      </Card>
    </div>

    <!-- Hybrid Facts Summary (if available) - Show in major facts only -->
    <div
      v-if="facts?.tuple_summary && !showOnlyDetailed"
      class="grid grid-cols-1 md:grid-cols-3 gap-3"
    >
      <Card
        :class="[
          'p-3',
          facts.tuple_summary.problem_count > 0
            ? 'bg-error-50 border-error-200'
            : 'bg-success-50 border-success-200',
        ]"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Problematic Tuples</p>
            <p
              :class="[
                'text-lg font-semibold mt-1',
                facts.tuple_summary.problem_count > 0 ? 'text-error-700' : 'text-success-700',
              ]"
            >
              {{ formatNumber(facts.tuple_summary.problem_count || 0) }}
            </p>
          </div>
          <ExclamationTriangleIcon
            :class="[
              'h-6 w-6',
              facts.tuple_summary.problem_count > 0 ? 'text-error-600' : 'text-success-600',
            ]"
          />
        </div>
      </Card>

      <Card class="p-3 bg-success-50 border-success-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Clean Tuples</p>
            <p class="text-lg font-semibold text-success-700 mt-1">
              {{ formatNumber(facts.tuple_summary.clean_count || 0) }}
            </p>
          </div>
          <CheckCircleIcon class="h-6 w-6 text-success-600" />
        </div>
      </Card>

      <Card class="p-3 bg-primary-50 border-primary-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Total Tuples</p>
            <p class="text-lg font-semibold text-primary-700 mt-1">
              {{ formatNumber(facts.tuple_summary.total_count || 0) }}
            </p>
          </div>
          <DocumentTextIcon class="h-6 w-6 text-primary-600" />
        </div>
      </Card>
    </div>

    <!-- Facts Summary Cards - Show in major facts only -->
    <div v-if="!showOnlyDetailed" class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <!-- Self-Flow -->
      <Card
        :class="[
          'p-3',
          isSelfFlow ? 'bg-error-50 border-error-200' : 'bg-success-50 border-success-200',
        ]"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Self-Flow</p>
            <p
              :class="[
                'text-lg font-semibold mt-1',
                isSelfFlow ? 'text-error-700' : 'text-success-700',
              ]"
            >
              {{ isSelfFlow ? 'Yes' : 'No' }}
            </p>
          </div>
          <ArrowPathIcon :class="['h-6 w-6', isSelfFlow ? 'text-error-600' : 'text-success-600']" />
        </div>
      </Card>

      <!-- Source Any -->
      <Card
        :class="[
          'p-3',
          isSrcAny ? 'bg-warning-50 border-warning-200' : 'bg-gray-50 border-gray-200',
        ]"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Source Any</p>
            <p
              :class="[
                'text-lg font-semibold mt-1',
                isSrcAny ? 'text-warning-700' : 'text-gray-700',
              ]"
            >
              {{ isSrcAny ? 'Yes' : 'No' }}
            </p>
          </div>
          <GlobeAltIcon :class="['h-6 w-6', isSrcAny ? 'text-warning-600' : 'text-gray-400']" />
        </div>
      </Card>

      <!-- Destination Any -->
      <Card
        :class="[
          'p-3',
          isDstAny ? 'bg-warning-50 border-warning-200' : 'bg-gray-50 border-gray-200',
        ]"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Dest Any</p>
            <p
              :class="[
                'text-lg font-semibold mt-1',
                isDstAny ? 'text-warning-700' : 'text-gray-700',
              ]"
            >
              {{ isDstAny ? 'Yes' : 'No' }}
            </p>
          </div>
          <GlobeAltIcon :class="['h-6 w-6', isDstAny ? 'text-warning-600' : 'text-gray-400']" />
        </div>
      </Card>

      <!-- Tuple Estimate -->
      <Card class="p-3 bg-primary-50 border-primary-200">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Tuple Estimate</p>
            <p class="text-lg font-semibold text-primary-700 mt-1">
              {{ formatNumber(facts?.tuple_estimate || 0) }}
            </p>
          </div>
          <DocumentTextIcon class="h-6 w-6 text-primary-600" />
        </div>
      </Card>
    </div>

    <!-- Detailed Facts - Always expanded when showOnlyDetailed is true -->
    <div v-if="showOnlyDetailed && facts && Object.keys(facts).length > 0">
      <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div
            v-for="(value, key) in facts"
            :key="key"
            :class="[
              'flex flex-col p-2 rounded',
              isProblematicField(key, value) ? 'bg-error-50 border border-error-200' : '',
            ]"
          >
            <span class="font-medium text-gray-700 capitalize mb-1"> {{ formatKey(key) }}: </span>
            <span class="text-gray-600 font-mono text-xs">
              {{ formatValue(value) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Expandable Details - Original behavior when neither prop is set -->
    <div v-if="!showOnlyMajor && !showOnlyDetailed && facts && Object.keys(facts).length > 0">
      <button
        class="flex items-center justify-between w-full p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
        @click="expanded = !expanded"
      >
        <span class="text-sm font-medium text-gray-700">
          {{ expanded ? 'Hide' : 'Show' }} Detailed Facts
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
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div
              v-for="(value, key) in facts"
              :key="key"
              :class="[
                'flex flex-col p-2 rounded',
                isProblematicField(key, value) ? 'bg-error-50 border border-error-200' : '',
              ]"
            >
              <span class="font-medium text-gray-700 capitalize mb-1"> {{ formatKey(key) }}: </span>
              <span class="text-gray-600 font-mono text-xs">
                {{ formatValue(value) }}
              </span>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- No Facts -->
    <Card v-else class="p-4 bg-gray-50">
      <p class="text-sm text-gray-600 text-center">No facts computed for this rule</p>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  ArrowPathIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  ChevronDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'

const props = defineProps({
  facts: {
    type: Object,
    default: null,
  },
  showOnlyMajor: {
    type: Boolean,
    default: false,
  },
  showOnlyDetailed: {
    type: Boolean,
    default: false,
  },
})

const expanded = ref(false)

// Computed properties for problematic fields to ensure proper boolean evaluation
const isSelfFlow = computed(() => {
  return Boolean(props.facts?.is_self_flow)
})

const isSrcAny = computed(() => {
  return Boolean(props.facts?.src_is_any)
})

const isDstAny = computed(() => {
  return Boolean(props.facts?.dst_is_any)
})

const formatKey = key => {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .toLowerCase()
    .replace(/\b\w/g, l => l.toUpperCase())
}

const formatValue = value => {
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  if (typeof value === 'number') {
    return value.toLocaleString()
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const formatNumber = num => {
  if (typeof num !== 'number') return '0'
  return num.toLocaleString()
}

const formatHealthStatus = status => {
  const statusMap = {
    critical: 'Critical',
    warning: 'Warning',
    clean: 'Clean',
  }
  return statusMap[status] || status
}

const getHealthStatusClass = status => {
  const classMap = {
    critical: 'bg-error-50 border-error-200',
    warning: 'bg-warning-50 border-warning-200',
    clean: 'bg-success-50 border-success-200',
  }
  return classMap[status] || 'bg-gray-50 border-gray-200'
}

const getHealthStatusTextClass = status => {
  const classMap = {
    critical: 'text-error-700',
    warning: 'text-warning-700',
    clean: 'text-success-700',
  }
  return classMap[status] || 'text-gray-700'
}

const getHealthStatusIconClass = status => {
  const classMap = {
    critical: 'text-error-600',
    warning: 'text-warning-600',
    clean: 'text-success-600',
  }
  return classMap[status] || 'text-gray-600'
}

const getHealthStatusIcon = status => {
  if (status === 'critical') return XCircleIcon
  if (status === 'warning') return ExclamationTriangleIcon
  return CheckCircleIcon
}

const getHealthStatusBadgeClass = status => {
  const classMap = {
    critical: 'bg-error-200 text-error-800',
    warning: 'bg-warning-200 text-warning-800',
    clean: 'bg-success-200 text-success-800',
  }
  return classMap[status] || 'bg-gray-200 text-gray-800'
}

const isProblematicField = (key, value) => {
  // Check if this field indicates a problem
  const problematicKeys = [
    'is_self_flow',
    'src_is_any',
    'dst_is_any',
    'src_has_public',
    'dst_has_public',
  ]

  if (problematicKeys.includes(key)) {
    return value === true
  }

  // Check tuple_summary for problem_count
  if (key === 'tuple_summary' && typeof value === 'object') {
    return value?.problem_count > 0
  }

  return false
}
</script>
