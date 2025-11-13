<template>
  <div class="space-y-4">
    <!-- Facts Summary Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <!-- Self-Flow -->
      <Card
        :class="[
          'p-3',
          facts?.is_self_flow
            ? 'bg-error-50 border-error-200'
            : 'bg-success-50 border-success-200',
        ]"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Self-Flow</p>
            <p
              :class="[
                'text-lg font-semibold mt-1',
                facts?.is_self_flow ? 'text-error-700' : 'text-success-700',
              ]"
            >
              {{ facts?.is_self_flow ? 'Yes' : 'No' }}
            </p>
          </div>
          <ArrowPathIcon
            :class="['h-6 w-6', facts?.is_self_flow ? 'text-error-600' : 'text-success-600']"
          />
        </div>
      </Card>

      <!-- Source Any -->
      <Card
        :class="[
          'p-3',
          facts?.src_is_any
            ? 'bg-warning-50 border-warning-200'
            : 'bg-gray-50 border-gray-200',
        ]"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Source Any</p>
            <p
              :class="[
                'text-lg font-semibold mt-1',
                facts?.src_is_any ? 'text-warning-700' : 'text-gray-700',
              ]"
            >
              {{ facts?.src_is_any ? 'Yes' : 'No' }}
            </p>
          </div>
          <GlobeAltIcon
            :class="['h-6 w-6', facts?.src_is_any ? 'text-warning-600' : 'text-gray-400']"
          />
        </div>
      </Card>

      <!-- Destination Any -->
      <Card
        :class="[
          'p-3',
          facts?.dst_is_any
            ? 'bg-warning-50 border-warning-200'
            : 'bg-gray-50 border-gray-200',
        ]"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium text-gray-600">Dest Any</p>
            <p
              :class="[
                'text-lg font-semibold mt-1',
                facts?.dst_is_any ? 'text-warning-700' : 'text-gray-700',
              ]"
            >
              {{ facts?.dst_is_any ? 'Yes' : 'No' }}
            </p>
          </div>
          <GlobeAltIcon
            :class="['h-6 w-6', facts?.dst_is_any ? 'text-warning-600' : 'text-gray-400']"
          />
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

    <!-- Expandable Details -->
    <div v-if="facts && Object.keys(facts).length > 0">
      <button
        @click="expanded = !expanded"
        class="flex items-center justify-between w-full p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
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
              class="flex flex-col"
            >
              <span class="font-medium text-gray-700 capitalize mb-1">
                {{ formatKey(key) }}:
              </span>
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
import { ref } from 'vue'
import {
  ArrowPathIcon,
  GlobeAltIcon,
  DocumentTextIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'

const props = defineProps({
  facts: {
    type: Object,
    default: null,
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

const formatNumber = (num) => {
  if (typeof num !== 'number') return '0'
  return num.toLocaleString()
}
</script>

