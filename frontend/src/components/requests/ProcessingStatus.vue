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
    <div v-if="currentStep?.results" class="mt-4 p-4 bg-gray-50 rounded-lg">
      <h4 class="text-sm font-medium text-gray-900 mb-2">Results:</h4>
      <div class="space-y-1 text-sm text-gray-600">
        <div v-for="(value, key) in currentStep.results" :key="key" class="flex justify-between">
          <span class="capitalize">{{ key.replace(/_/g, ' ') }}:</span>
          <span class="font-medium">{{ value }}</span>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="currentStep?.error" class="mt-4 p-4 bg-error-50 border border-error-200 rounded-lg">
      <p class="text-sm text-error-800">{{ currentStep.error }}</p>
    </div>
  </div>
</template>

<script setup>
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  currentStep: {
    type: Object,
    default: null,
  },
})
</script>

