<template>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <!-- Total Rules -->
    <Card class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600">Total Rules</p>
          <p class="text-2xl font-bold text-gray-900 mt-1">
            {{ formatNumber(stats?.total_rules || 0) }}
          </p>
        </div>
        <div class="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
          <DocumentTextIcon class="h-6 w-6 text-primary-600" />
        </div>
      </div>
    </Card>

    <!-- Allow vs Deny -->
    <Card class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600">Allow / Deny</p>
          <div class="flex items-center space-x-2 mt-1">
            <span class="text-lg font-semibold text-success-600">
              {{ formatNumber(stats?.allow_rules || 0) }}
            </span>
            <span class="text-gray-400">/</span>
            <span class="text-lg font-semibold text-error-600">
              {{ formatNumber(stats?.deny_rules || 0) }}
            </span>
          </div>
        </div>
        <div class="h-12 w-12 bg-success-100 rounded-lg flex items-center justify-center">
          <CheckCircleIcon class="h-6 w-6 text-success-600" />
        </div>
      </div>
    </Card>

    <!-- Unique Sources -->
    <Card class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600">Source Networks</p>
          <p class="text-2xl font-bold text-gray-900 mt-1">
            {{ formatNumber(stats?.unique_sources || 0) }}
          </p>
        </div>
        <div class="h-12 w-12 bg-info-100 rounded-lg flex items-center justify-center">
          <ArrowRightIcon class="h-6 w-6 text-info-600" />
        </div>
      </div>
    </Card>

    <!-- Unique Destinations -->
    <Card class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600">Dest Networks</p>
          <p class="text-2xl font-bold text-gray-900 mt-1">
            {{ formatNumber(stats?.unique_destinations || 0) }}
          </p>
        </div>
        <div class="h-12 w-12 bg-warning-100 rounded-lg flex items-center justify-center">
          <ArrowLeftIcon class="h-6 w-6 text-warning-600" />
        </div>
      </div>
    </Card>

    <!-- Unique Protocols -->
    <Card class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600">Protocols</p>
          <p class="text-2xl font-bold text-gray-900 mt-1">
            {{ formatNumber(stats?.unique_protocols || 0) }}
          </p>
        </div>
        <div class="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
          <GlobeAltIcon class="h-6 w-6 text-purple-600" />
        </div>
      </div>
    </Card>

    <!-- Rules with Facts -->
    <Card class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600">With Facts</p>
          <p class="text-2xl font-bold text-gray-900 mt-1">
            {{ formatNumber(stats?.rules_with_facts || 0) }}
          </p>
          <p class="text-xs text-gray-500 mt-1">{{ factsPercentage }}% coverage</p>
        </div>
        <div class="h-12 w-12 bg-primary-100 rounded-lg flex items-center justify-center">
          <InformationCircleIcon class="h-6 w-6 text-primary-600" />
        </div>
      </div>
    </Card>

    <!-- Self-Flow Rules -->
    <Card class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600">Self-Flow</p>
          <p class="text-2xl font-bold text-gray-900 mt-1">
            {{ formatNumber(stats?.self_flow_count || 0) }}
          </p>
        </div>
        <div class="h-12 w-12 bg-warning-100 rounded-lg flex items-center justify-center">
          <ArrowPathIcon class="h-6 w-6 text-warning-600" />
        </div>
      </div>
    </Card>

    <!-- Any/Any Rules -->
    <Card class="p-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600">Any/Any Rules</p>
          <p class="text-2xl font-bold text-gray-900 mt-1">
            {{ formatNumber(anyAnyCount) }}
          </p>
        </div>
        <div class="h-12 w-12 bg-error-100 rounded-lg flex items-center justify-center">
          <ExclamationTriangleIcon class="h-6 w-6 text-error-600" />
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  DocumentTextIcon,
  CheckCircleIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  GlobeAltIcon,
  InformationCircleIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({}),
  },
})

const formatNumber = num => {
  if (typeof num !== 'number') return '0'
  return num.toLocaleString()
}

const factsPercentage = computed(() => {
  const total = props.stats?.total_rules || 0
  const withFacts = props.stats?.rules_with_facts || 0
  if (total === 0) return 0
  return Math.round((withFacts / total) * 100)
})

const anyAnyCount = computed(() => {
  return (props.stats?.src_any_count || 0) + (props.stats?.dst_any_count || 0)
})
</script>
