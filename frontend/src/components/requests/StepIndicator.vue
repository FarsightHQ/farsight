<template>
  <div class="flex items-center justify-between">
    <div v-for="(step, index) in steps" :key="step.key" class="flex items-center flex-1">
      <!-- Step Circle -->
      <div class="flex flex-col items-center flex-1">
        <div
          :class="[
            'h-10 w-10 rounded-full flex items-center justify-center border-2 transition-all',
            getStepClasses(step, index),
          ]"
        >
          <CheckIcon v-if="step.status === 'completed'" class="h-6 w-6 text-white" />
          <Spinner v-else-if="step.status === 'processing'" size="sm" color="white" />
          <span v-else class="text-sm font-medium">{{ index + 1 }}</span>
        </div>
        <div class="mt-2 text-center">
          <p
            :class="[
              'text-xs font-medium',
              step.status === 'processing' ? 'text-primary-600' : 'text-gray-600',
            ]"
          >
            {{ step.label }}
          </p>
          <p v-if="step.status === 'processing'" class="text-xs text-gray-500 mt-1">
            {{ step.progress }}%
          </p>
        </div>
      </div>

      <!-- Connector Line -->
      <div
        v-if="index < steps.length - 1"
        :class="[
          'h-0.5 flex-1 mx-2',
          step.status === 'completed' ? 'bg-primary-600' : 'bg-gray-300',
        ]"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { CheckIcon } from '@heroicons/vue/24/solid'
import Spinner from '@/components/ui/Spinner.vue'

const props = defineProps({
  steps: {
    type: Array,
    required: true,
  },
})

const getStepClasses = (step, index) => {
  if (step.status === 'completed') {
    return 'bg-primary-600 border-primary-600'
  } else if (step.status === 'processing') {
    return 'bg-primary-500 border-primary-500 animate-pulse'
  } else {
    return 'bg-white border-gray-300 text-gray-400'
  }
}
</script>
