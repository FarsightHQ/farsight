<template>
  <button :class="buttonClasses" :disabled="disabled" :type="type" @click="$emit('click', $event)">
    <slot />
  </button>
</template>

<script setup>
/**
 * Size: use default md for PageFrame #actions, modal footers, and primary page CTAs.
 * Use sm only inside tables, dense toolbars, or filter sidebars.
 * Variants: one primary per screen when appropriate; outline for Back/Cancel/secondary actions.
 */
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: value => ['primary', 'secondary', 'outline', 'ghost'].includes(value),
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  type: {
    type: String,
    default: 'button',
  },
  size: {
    type: String,
    default: 'md',
    validator: value => ['sm', 'md', 'lg'].includes(value),
  },
})

const emit = defineEmits(['click'])

const buttonClasses = computed(() => {
  const base = 'btn'
  const variant = `btn-${props.variant}`
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  return [base, variant, sizeClasses[props.size]].join(' ')
})
</script>
