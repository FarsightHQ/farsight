<template>
  <nav
    aria-label="Breadcrumb"
    :class="[
      'text-theme-text-muted flex flex-wrap items-center gap-x-1 gap-y-1',
      compact ? 'text-xs' : 'text-sm',
    ]"
  >
    <template v-for="(item, i) in items" :key="i">
      <ChevronRightIcon
        v-if="i > 0"
        :class="['shrink-0 text-theme-text-muted/50 mx-0.5', compact ? 'h-3 w-3' : 'h-4 w-4']"
        aria-hidden="true"
      />
      <router-link
        v-if="item.to && !item.current"
        :to="item.to"
        class="hover:text-primary-600 truncate max-w-[10rem] sm:max-w-[14rem]"
      >
        {{ item.label }}
      </router-link>
      <span
        v-else-if="item.current"
        class="text-theme-text-content font-medium truncate max-w-[12rem] sm:max-w-[16rem]"
        aria-current="page"
      >
        {{ item.label }}
      </span>
      <span v-else class="text-theme-text-muted truncate max-w-[10rem] sm:max-w-[14rem]">
        {{ item.label }}
      </span>
    </template>
  </nav>
</template>

<script setup>
import { ChevronRightIcon } from '@heroicons/vue/24/outline'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  compact: {
    type: Boolean,
    default: false,
  },
})
</script>
