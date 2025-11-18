<template>
  <span :class="badgeClasses">
    <slot>{{ status }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) =>
      ['submitted', 'processing', 'ingested', 'completed', 'error', 'failed', 'pending'].includes(
        value?.toLowerCase()
      ),
  },
})

const badgeClasses = computed(() => {
  const base = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'
  const statusLower = props.status?.toLowerCase()

  const variants = {
    submitted: 'bg-gray-100 text-gray-800',
    processing: 'bg-primary-100 text-primary-800',
    ingested: 'bg-success-100 text-success-800',
    completed: 'bg-success-100 text-success-800',
    error: 'bg-error-100 text-error-800',
    failed: 'bg-error-100 text-error-800',
    pending: 'bg-gray-100 text-gray-600',
  }

  return [base, variants[statusLower] || variants.submitted].join(' ')
})
</script>

