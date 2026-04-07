<template>
  <div class="h-full flex flex-col overflow-hidden bg-theme-content min-h-0">
    <AppHeader v-if="!hideAppChrome" />

    <div class="flex-1 flex overflow-hidden min-h-0">
      <AppSidebar v-if="!hideAppChrome" />

      <div class="flex-1 flex flex-col overflow-hidden min-w-0 min-h-0">
        <main
          :class="[
            'flex-1 bg-theme-content min-h-0 flex flex-col overflow-hidden',
          ]"
        >
          <div
            :class="[
              'flex flex-1 flex-col min-h-0 min-w-0 overflow-hidden',
              isVizWorkspaceRoute ? 'p-0' : '',
            ]"
          >
            <slot />
          </div>
        </main>

        <AppFooter v-if="!hideAppChrome" />
      </div>
    </div>

    <Toast />
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
import AppFooter from './AppFooter.vue'
import Toast from '../ui/Toast.vue'
import { useVizAppChrome } from '@/composables/useVizAppChrome'

const route = useRoute()
const { hideAppChrome, resetVizChrome } = useVizAppChrome()

const isVizWorkspaceRoute = computed(() =>
  route.matched.some(record => record.meta.vizWorkspace === true)
)

watch(
  () => route.fullPath,
  () => {
    if (!isVizWorkspaceRoute.value) resetVizChrome()
  }
)
</script>
