<template>
  <div
    v-if="variant === 'inline'"
    class="rounded-lg border border-error-200 bg-error-50 p-4 text-error-800 text-sm"
  >
    {{ message }}
    <div v-if="$slots.default" class="mt-3">
      <slot />
    </div>
  </div>

  <Card v-else class="p-6">
    <div v-if="centered" class="text-center py-12">
      <p class="text-error-600 mb-4">{{ message }}</p>
      <slot />
    </div>
    <template v-else>
      <p class="text-error-600 mb-4">{{ message }}</p>
      <slot />
    </template>
  </Card>
</template>

<script setup>
import Card from '@/components/ui/Card.vue'

defineProps({
  message: {
    type: String,
    required: true,
  },
  variant: {
    type: String,
    default: 'inline',
    validator: v => ['inline', 'card'].includes(v),
  },
  /** When variant is card, center content (e.g. full-page error). */
  centered: {
    type: Boolean,
    default: false,
  },
})
</script>
