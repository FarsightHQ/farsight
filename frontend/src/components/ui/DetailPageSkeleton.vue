<template>
  <div class="space-y-6">
    <div
      v-if="showTitle"
      class="h-8 bg-theme-active/30 rounded animate-pulse"
      :class="titleWidthClass"
    />
    <div :class="gridClass">
      <div v-for="i in cardCount" :key="i" class="h-24 bg-theme-active/30 rounded animate-pulse" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  showTitle: {
    type: Boolean,
    default: true,
  },
  titleWidthClass: {
    type: String,
    default: 'w-1/3',
  },
  /** Number of Tailwind grid columns (2 or 3). */
  columns: {
    type: Number,
    default: 3,
    validator: v => [2, 3].includes(v),
  },
  cardCount: {
    type: Number,
    default: 3,
  },
})

const gridClass = computed(() => {
  const cols = props.columns === 2 ? 'grid-cols-2' : 'grid-cols-3'
  return `grid ${cols} gap-4`
})
</script>
