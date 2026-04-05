<template>
  <div class="viz-workspace flex h-full min-h-0 w-full min-w-0 bg-gray-100 text-gray-900">
    <!-- ~80% canvas (4:1 flex split): pan/zoom inside slot (e.g. d3.zoom) -->
    <section
      class="viz-workspace__canvas flex-[4] min-w-0 min-h-0 flex flex-col bg-gray-100"
      aria-label="Visualization canvas"
    >
      <div class="viz-workspace__canvas-inner flex-1 min-h-0 overflow-hidden relative">
        <slot />
      </div>
    </section>

    <!-- ~20% tools + metadata -->
    <aside
      class="viz-workspace__panel flex-1 min-w-[12.5rem] max-w-[22rem] shrink-0 min-h-0 flex flex-col bg-white border-l border-gray-200 shadow-sm"
      aria-label="Visualization details"
    >
      <div class="shrink-0 p-3 sm:p-4 border-b border-gray-200 flex items-start gap-2">
        <div class="min-w-0 flex-1">
          <slot name="heading">
            <h1 v-if="title" class="text-base sm:text-lg font-semibold text-gray-900 leading-snug break-words">
              {{ title }}
            </h1>
            <p v-if="subtitle" class="text-xs sm:text-sm text-gray-600 mt-1 break-words">
              {{ subtitle }}
            </p>
          </slot>
        </div>
        <button
          type="button"
          class="shrink-0 p-2 rounded-lg border border-gray-200 bg-gray-50 text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :title="hideAppChrome ? 'Exit full screen (show app navigation)' : 'Full screen (hide navigation)'"
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
import { useVizAppChrome } from '@/composables/useVizAppChrome'

const { hideAppChrome, toggleVizFullscreen } = useVizAppChrome()

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

<style scoped>
.viz-workspace {
  box-sizing: border-box;
}
</style>
