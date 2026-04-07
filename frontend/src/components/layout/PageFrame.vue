<template>
  <div class="page-frame">
    <BreadcrumbTrail v-if="breadcrumbItems?.length" :items="breadcrumbItems" class="mb-3" />
    <div
      class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-6 pb-4 border-b border-theme-border-default"
    >
      <div class="min-w-0 flex-1">
        <h1
          v-if="title || $slots.title"
          class="text-2xl font-semibold text-theme-text-content"
        >
          <slot name="title">{{ title }}</slot>
        </h1>
        <div
          v-if="subtitle || $slots.subtitle"
          class="text-sm text-theme-text-muted mt-1"
        >
          <slot name="subtitle">{{ subtitle }}</slot>
        </div>
      </div>
      <div
        v-if="$slots.actions"
        class="flex flex-wrap items-center gap-2 justify-end shrink-0"
      >
        <slot name="actions" />
      </div>
    </div>
    <slot />
  </div>
</template>

<script setup>
import BreadcrumbTrail from './BreadcrumbTrail.vue'

defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  breadcrumbItems: {
    type: Array,
    default: () => [],
  },
})
</script>
