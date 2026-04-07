<template>
  <span :class="badgeClasses">
    <slot>{{ displayText }}</slot>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
  label: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'md',
    validator: (value: unknown) =>
      typeof value === 'string' && ['sm', 'md'].includes(value),
  },
})

const displayText = computed(() => props.label || props.status)

const badgeClasses = computed(() => {
  const sizeClasses = {
    sm: 'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium leading-tight',
    md: 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
  }
  const base = sizeClasses[props.size as keyof typeof sizeClasses]
  const statusLower = props.status?.toLowerCase()

  const variants = {
    submitted: 'bg-secondary-200 text-secondary-900',
    processing: 'bg-primary-100 text-primary-800',
    ingesting: 'bg-primary-100 text-primary-800',
    ingested: 'bg-success-100 text-success-800',
    completed: 'bg-success-100 text-success-800',
    success: 'bg-success-100 text-success-800',
    error: 'bg-error-100 text-error-800',
    failed: 'bg-error-100 text-error-800',
    pending: 'bg-secondary-100 text-secondary-500',
    warning: 'bg-warning-100 text-warning-800',
    skipped: 'bg-secondary-100 text-secondary-600',
    cancelled: 'bg-secondary-200 text-secondary-700',
  }

  return [base, variants[statusLower] ?? variants.submitted].join(' ')
})
</script>
