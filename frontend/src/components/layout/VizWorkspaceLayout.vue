<template>
  <div
    class="viz-workspace flex flex-1 h-full min-h-0 w-full min-w-0 bg-theme-content text-theme-text-content"
  >
    <!-- ~80% canvas (4:1 flex split): pan/zoom inside slot (e.g. d3.zoom) -->
    <section
      class="viz-workspace__canvas flex-[4] min-w-0 min-h-0 flex flex-col bg-theme-content"
      aria-label="Visualization canvas"
    >
      <div
        v-if="breadcrumbItems.length"
        class="shrink-0 px-2 py-1.5 sm:px-3 border-b border-theme-border-default bg-theme-card/90 backdrop-blur-sm"
      >
        <BreadcrumbTrail :items="breadcrumbItems" compact />
      </div>
      <div class="viz-workspace__canvas-inner flex-1 min-h-0 overflow-hidden relative">
        <slot />
      </div>
    </section>

    <!-- ~20% tools + metadata -->
    <aside
      class="viz-workspace__panel flex-1 min-w-[12.5rem] max-w-[22rem] shrink-0 min-h-0 flex flex-col bg-theme-card border-l border-theme-border-default shadow-sm"
      aria-label="Visualization details"
    >
      <div class="shrink-0 p-3 sm:p-4 border-b border-theme-border-default flex items-start gap-2">
        <div class="min-w-0 flex-1">
          <slot name="heading">
            <h1
              v-if="title"
              class="text-base sm:text-lg font-semibold text-theme-text-content leading-snug break-words"
            >
              {{ title }}
            </h1>
            <p v-if="subtitle" class="text-xs sm:text-sm text-theme-text-muted mt-1 break-words">
              {{ subtitle }}
            </p>
          </slot>
        </div>
        <button
          type="button"
          class="shrink-0 p-2 rounded-lg border border-theme-border-default bg-secondary-100 text-secondary-900 hover:bg-secondary-200 focus:outline-none focus:ring-2 focus:ring-primary-600"
          :title="
            hideAppChrome
              ? 'Exit full screen (show app navigation)'
              : 'Full screen (hide navigation)'
          "
          :aria-label="hideAppChrome ? 'Exit full screen' : 'Enter full screen'"
          :aria-pressed="hideAppChrome"
          @click="toggleVizFullscreen"
        >
          <ArrowsPointingOutIcon v-if="!hideAppChrome" class="h-5 w-5" aria-hidden="true" />
          <ArrowsPointingInIcon v-else class="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      <div class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-3 sm:p-4 space-y-4">
        <slot name="panel" />
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ArrowsPointingOutIcon, ArrowsPointingInIcon } from '@heroicons/vue/24/outline'
import BreadcrumbTrail from '@/components/layout/BreadcrumbTrail.vue'
import { useVizAppChrome } from '@/composables/useVizAppChrome'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const { hideAppChrome, toggleVizFullscreen } = useVizAppChrome()
const { breadcrumbItems } = usePageBreadcrumbs()

defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
})
</script>
