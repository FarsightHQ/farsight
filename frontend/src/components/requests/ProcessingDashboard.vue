<template>
  <Card>
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold text-gray-900">Processing Pipeline</h2>
        <Button
          v-if="canCancel"
          variant="outline"
          size="sm"
          @click="$emit('cancel')"
        >
          Cancel
        </Button>
      </div>

      <!-- Step Indicator -->
      <StepIndicator :steps="steps" />

      <!-- Overall Progress -->
      <div>
        <div class="flex items-center justify-between text-sm text-gray-600 mb-1">
          <span>Overall Progress</span>
          <span>{{ overallProgress }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-3">
          <div
            class="bg-primary-600 h-3 rounded-full transition-all duration-300"
            :style="{ width: `${overallProgress}%` }"
          ></div>
        </div>
      </div>

      <!-- Current Step Status -->
      <ProcessingStatus :current-step="currentStepData" />

      <!-- Processing Timeline -->
      <div v-if="completedSteps.length > 0" class="border-t pt-4">
        <h3 class="text-sm font-medium text-gray-900 mb-3">Completed Steps</h3>
        <div class="space-y-2">
          <div
            v-for="step in completedSteps"
            :key="step.key"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <CheckIcon class="h-5 w-5 text-success-600" />
              <div>
                <p class="text-sm font-medium text-gray-900">{{ step.label }}</p>
                <p v-if="step.duration" class="text-xs text-gray-500">
                  Completed in {{ step.duration }}
                </p>
              </div>
            </div>
            <div v-if="step.results" class="text-xs text-gray-600">
              <span v-for="(value, key) in step.results" :key="key" class="ml-2">
                {{ key }}: {{ value }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import { CheckIcon } from '@heroicons/vue/24/solid'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import StepIndicator from './StepIndicator.vue'
import ProcessingStatus from './ProcessingStatus.vue'

const props = defineProps({
  steps: {
    type: Array,
    required: true,
  },
  canCancel: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['cancel'])

const overallProgress = computed(() => {
  const totalSteps = props.steps.length
  const completedSteps = props.steps.filter((s) => s.status === 'completed').length
  const processingStep = props.steps.find((s) => s.status === 'processing')
  const processingProgress = processingStep?.progress || 0

  if (completedSteps === totalSteps) return 100

  const baseProgress = (completedSteps / totalSteps) * 100
  const stepProgress = processingProgress / totalSteps

  return Math.round(baseProgress + stepProgress)
})

const currentStepData = computed(() => {
  return props.steps.find((s) => s.status === 'processing') || null
})

const completedSteps = computed(() => {
  return props.steps.filter((s) => s.status === 'completed')
})
</script>

