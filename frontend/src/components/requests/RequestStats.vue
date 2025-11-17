<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <Card class="flex items-center space-x-4">
      <div class="flex-shrink-0">
        <div class="h-12 w-12 rounded-lg bg-primary-100 flex items-center justify-center">
          <DocumentTextIcon class="h-6 w-6 text-primary-600" />
        </div>
      </div>
      <div class="flex-1">
        <p class="text-sm font-medium text-gray-600">Total Rules</p>
        <p class="text-2xl font-bold text-gray-900">{{ stats.totalRules || 0 }}</p>
      </div>
    </Card>

    <Card class="flex items-center space-x-4">
      <div class="flex-shrink-0">
        <div class="h-12 w-12 rounded-lg bg-success-100 flex items-center justify-center">
          <ServerIcon class="h-6 w-6 text-success-600" />
        </div>
      </div>
      <div class="flex-1">
        <p class="text-sm font-medium text-gray-600">Endpoints</p>
        <p class="text-2xl font-bold text-gray-900">{{ stats.totalEndpoints || 0 }}</p>
      </div>
    </Card>

    <Card class="flex items-center space-x-4">
      <div class="flex-shrink-0">
        <div class="h-12 w-12 rounded-lg bg-warning-100 flex items-center justify-center">
          <CogIcon class="h-6 w-6 text-warning-600" />
        </div>
      </div>
      <div class="flex-1">
        <p class="text-sm font-medium text-gray-600">Services</p>
        <p class="text-2xl font-bold text-gray-900">{{ stats.totalServices || 0 }}</p>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { DocumentTextIcon, ServerIcon, CogIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({
      totalRules: 0,
      totalEndpoints: 0,
      totalServices: 0,
    }),
  },
})
</script>

