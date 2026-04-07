<template>
  <div class="page-frame flex flex-col flex-1 min-h-0 min-w-0 w-full">
    <div
      v-if="breadcrumbItems?.length"
      class="shrink-0 w-full border-b border-theme-border-default bg-gray-100 px-6 py-2.5"
    >
      <BreadcrumbTrail :items="breadcrumbItems" />
    </div>
    <div
      class="shrink-0 w-full border-b border-theme-border-default bg-white px-6 py-4"
    >
      <div
        class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"
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
    </div>
    <div
      :class="[
        'flex-1 min-h-0 min-w-0 px-6 py-4',
        scrollBody ? 'overflow-y-auto' : 'overflow-hidden flex flex-col',
      ]"
    >
      <slot />
    </div>
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
  scrollBody: {
    type: Boolean,
    default: true,
  },
})
</script>
