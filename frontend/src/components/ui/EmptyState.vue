<template>
  <Card>
    <div class="text-center py-12">
      <p class="text-theme-text-muted">{{ message }}</p>
      <div v-if="$slots.default" class="mt-4">
        <slot />
      </div>
    </div>
  </Card>
</template>

<script setup>
import Card from '@/components/ui/Card.vue'

defineProps({
  message: {
    type: String,
    required: true,
  },
})
</script>
