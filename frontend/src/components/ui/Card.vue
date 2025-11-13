<template>
  <div :class="cardClasses">
    <div v-if="$slots.header" class="mb-4 border-b border-gray-200 pb-4">
      <slot name="header" />
    </div>
    <slot />
    <div v-if="$slots.footer" class="mt-4 border-t border-gray-200 pt-4">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  padding: {
    type: String,
    default: 'normal',
    validator: (value) => ['none', 'sm', 'normal', 'lg'].includes(value),
  },
  shadow: {
    type: Boolean,
    default: true,
  },
})

const cardClasses = computed(() => {
  const base = 'card rounded-lg bg-white border border-gray-200'
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    normal: 'p-6',
    lg: 'p-8',
  }
  const shadowClass = props.shadow ? 'shadow-sm' : ''

  return [base, paddingClasses[props.padding], shadowClass].filter(Boolean).join(' ')
})
</script>

