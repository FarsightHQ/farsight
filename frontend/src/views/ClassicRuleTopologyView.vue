<template>
  <VizWorkspaceLayout :title="''" :subtitle="''">
    <template #heading>
      <h1 class="text-base sm:text-lg font-semibold text-gray-900 leading-snug break-words">
        Rule topology (classic)
      </h1>
      <p v-if="layoutSubtitle" class="text-xs sm:text-sm text-gray-600 mt-1 break-words">
        {{ layoutSubtitle }}
      </p>
      <p class="text-xs text-gray-500 mt-2 leading-snug">
        Original flow layout: sources on the left, destinations on the right, links show allowed
        services. Policy direction, not physical topology.
      </p>
    </template>

    <template #default>
      <div class="relative h-full min-h-0 w-full min-w-0">
        <div
          v-if="loading"
          class="absolute inset-0 flex items-center justify-center bg-gray-100 z-10"
        >
          <Spinner size="lg" class="mr-3" />
          <span class="text-gray-600">Loading topology…</span>
        </div>

        <div
          v-else-if="error"
          class="absolute inset-0 flex items-center justify-center bg-gray-100 z-10 p-6"
        >
          <div class="text-center max-w-md">
            <p class="text-red-600 font-medium break-words">{{ error }}</p>
            <Button class="mt-4" variant="primary" @click="load">Retry</Button>
          </div>
        </div>

        <div
          v-else-if="!ruleIds.length"
          class="absolute inset-0 flex items-center justify-center bg-gray-100 z-10 p-6 text-gray-600 text-center text-sm"
        >
          {{ emptyStateMessage }}
        </div>

        <div
          v-else-if="!canShowGraph"
          class="absolute inset-0 flex items-center justify-center bg-gray-100 z-10 p-6"
        >
          <div class="text-center max-w-md text-gray-700">
            <p class="font-medium text-gray-900">No network data</p>
            <p class="text-sm mt-2">{{ emptyStateMessage }}</p>
          </div>
        </div>

        <div
          v-else
          class="h-full min-h-0 w-full min-w-0 overflow-y-auto overflow-x-auto overscroll-y-contain"
        >
          <!-- Let NetworkGraph height follow SVG content so this wrapper can scroll (canvas parent is overflow-hidden). -->
          <NetworkGraph class="w-full" :graph-data="graphData" />
        </div>
      </div>
    </template>

    <template #panel>
      <div v-if="summary" class="space-y-1 text-sm text-gray-700">
        <p class="font-medium text-gray-900">Summary</p>
        <ul class="list-none space-y-0.5 text-xs sm:text-sm">
          <li v-if="summary.rule_count != null">
            <span class="text-gray-600">Rules:</span>
            {{ summary.rule_count }}
          </li>
          <li>
            <span class="text-gray-600">Sources:</span>
            {{ summary.source_count ?? '—' }}
          </li>
          <li>
            <span class="text-gray-600">Destinations:</span>
            {{ summary.destination_count ?? '—' }}
          </li>
          <li>
            <span class="text-gray-600">Services (port sum):</span>
            {{ summary.service_count ?? '—' }}
          </li>
        </ul>
      </div>

      <div v-else-if="!loading && !error && ruleIds.length" class="text-sm text-gray-600">
        No summary available.
      </div>

      <div class="text-xs text-gray-500 leading-snug">
        <p>
          Hover over elements to see details. Port count badges show the number of ports per
          connection.
        </p>
      </div>

      <div v-if="ruleIds.length" class="pt-1">
        <RouterLink
          :to="{
            name: 'UnifiedGraph',
            params: { projectId: String(route.params.projectId) },
            query: {
              ruleIds: ruleIds.join(','),
              title: layoutSubtitle || undefined,
            },
          }"
          class="text-sm text-blue-600 hover:text-blue-800"
        >
          Open unified topology for these rules
        </RouterLink>
      </div>
    </template>
  </VizWorkspaceLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import VizWorkspaceLayout from '@/components/layout/VizWorkspaceLayout.vue'
import NetworkGraph from '@/components/requests/NetworkGraph.vue'
import Button from '@/components/ui/Button.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { useClassicRuleTopology } from '@/composables/useClassicRuleTopology'
import { useSidebar } from '@/composables/useSidebar'
import { useVizAppChrome } from '@/composables/useVizAppChrome'

const route = useRoute()
const { setSidebarCollapsed, isCollapsed } = useSidebar()
const { resetVizChrome } = useVizAppChrome()
const sidebarStateBeforeViz = ref(null)

const ruleIds = computed(() => {
  const q = route.query.ruleIds
  if (!q) return []
  return String(q)
    .split(',')
    .map(s => parseInt(s.trim(), 10))
    .filter(n => !Number.isNaN(n))
})

const layoutSubtitle = computed(() => {
  if (route.query.title) return String(route.query.title)
  if (ruleIds.value.length) return `Rules: ${ruleIds.value.join(', ')}`
  return ''
})

const { loading, error, graphData, summary, emptyStateMessage, load } =
  useClassicRuleTopology(ruleIds)

const canShowGraph = computed(() => {
  const g = graphData.value
  return (
    g &&
    Array.isArray(g.sources) &&
    g.sources.length > 0 &&
    Array.isArray(g.destinations) &&
    g.destinations.length > 0
  )
})

onMounted(() => {
  sidebarStateBeforeViz.value = isCollapsed.value
  setSidebarCollapsed(true, { persist: false })
})

onBeforeUnmount(() => {
  resetVizChrome()
  if (sidebarStateBeforeViz.value !== null) {
    setSidebarCollapsed(sidebarStateBeforeViz.value, { persist: false })
  }
})

watch(
  () => route.query.ruleIds,
  () => {
    load()
  },
  { immediate: true }
)
</script>
