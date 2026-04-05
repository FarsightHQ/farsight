<template>
  <VizWorkspaceLayout title="Unified network topology" :subtitle="subtitle">
    <template #default>
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
        <Spinner size="lg" class="mr-3" />
        <span class="text-gray-600">Loading graph…</span>
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
        v-else-if="!graphPayload?.nodes?.length"
        class="absolute inset-0 flex items-center justify-center bg-gray-100 z-10 p-6 text-gray-600 text-center"
      >
        No unified graph data for this selection.
      </div>

      <UnifiedNetworkGraph
        v-else
        ref="graphRef"
        class="h-full w-full"
        :unified-graph="graphPayload"
        :filter-text="filterText"
      />
    </template>

    <template #panel>
      <div class="space-y-1 text-sm text-gray-700">
        <p class="font-medium text-gray-900">Summary</p>
        <ul class="list-none space-y-0.5 text-xs sm:text-sm">
          <li>{{ graphSummary.nodes }} nodes</li>
          <li>{{ graphSummary.links }} links</li>
          <li v-if="graphSummary.rules != null">{{ graphSummary.rules }} rules</li>
        </ul>
      </div>

      <div class="space-y-2">
        <label class="block text-xs font-medium text-gray-600" for="unified-graph-filter">Filter nodes</label>
        <input
          id="unified-graph-filter"
          v-model="filterText"
          type="search"
          placeholder="CIDR, hostname, segment…"
          class="w-full max-w-full box-border px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <Button variant="outline" size="sm" class="w-full justify-center" @click="handleFit">
          Fit to view
        </Button>
      </div>

      <div v-if="legendSegments.length" class="space-y-2">
        <p class="text-xs font-medium text-gray-600">Segments</p>
        <ul class="flex flex-col gap-2 list-none p-0 m-0">
          <li
            v-for="seg in legendSegments"
            :key="seg"
            class="flex items-center gap-2 text-xs text-gray-800 min-w-0"
          >
            <span
              class="w-2.5 h-2.5 rounded-full shrink-0"
              :style="{ background: legendColor(seg) }"
              aria-hidden="true"
            />
            <span class="break-words leading-snug">{{ seg }}</span>
          </li>
        </ul>
      </div>
    </template>
  </VizWorkspaceLayout>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import * as d3 from 'd3'
import { requestsService } from '@/services/requests'
import { mergeUnifiedGraphData, extractUnifiedGraphFromRuleResponse } from '@/utils/unifiedGraphMerge'
import UnifiedNetworkGraph from '@/components/requests/UnifiedNetworkGraph.vue'
import VizWorkspaceLayout from '@/components/layout/VizWorkspaceLayout.vue'
import Button from '@/components/ui/Button.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { useSidebar } from '@/composables/useSidebar'
import { useVizAppChrome } from '@/composables/useVizAppChrome'

const route = useRoute()
const { setSidebarCollapsed, isCollapsed } = useSidebar()
const { resetVizChrome } = useVizAppChrome()
const sidebarStateBeforeViz = ref(null)

const loading = ref(true)
const error = ref(null)
const graphPayload = ref(null)
const filterText = ref('')
const graphRef = ref(null)

const ruleIds = computed(() => {
  const q = route.query.ruleIds
  if (!q) return []
  return String(q)
    .split(',')
    .map((s) => parseInt(s.trim(), 10))
    .filter((n) => !Number.isNaN(n))
})

const requestId = computed(() => {
  const q = route.query.requestId
  if (q == null || q === '') return null
  const n = parseInt(String(q), 10)
  return Number.isNaN(n) ? null : n
})

const subtitle = computed(() => {
  if (route.query.title) return String(route.query.title)
  if (requestId.value != null) return `Request #${requestId.value}`
  if (ruleIds.value.length) return `Rules: ${ruleIds.value.join(', ')}`
  return 'Open from a rule or request with graph data'
})

const legendSegments = computed(() => {
  const nodes = graphPayload.value?.nodes || []
  return [...new Set(nodes.map((n) => n.segment || 'Unknown'))].sort()
})

const segmentScale = computed(() => {
  const segs = legendSegments.value
  return d3.scaleOrdinal(d3.schemeTableau10).domain(segs)
})

function legendColor(seg) {
  return segmentScale.value(seg)
}

/** Coalesced stats for the panel (stable placeholders while loading). */
const graphSummary = computed(() => {
  if (loading.value || !graphPayload.value?.nodes?.length) {
    return { nodes: '—', links: '—', rules: null }
  }
  const g = graphPayload.value
  return {
    nodes: g.metadata?.node_count ?? g.nodes.length,
    links: g.metadata?.link_count ?? g.links?.length ?? 0,
    rules: g.metadata?.rule_count ?? null,
  }
})

let loadGeneration = 0

async function load() {
  const gen = ++loadGeneration
  loading.value = true
  error.value = null
  graphPayload.value = null

  try {
    if (requestId.value != null) {
      const res = await requestsService.getNetworkTopology(requestId.value)
      if (gen !== loadGeneration) return
      const data = res.data?.data || res.data || res
      if (data.error) {
        error.value = data.error
        return
      }
      graphPayload.value = data.unified_graph || data.topology || null
      return
    }

    if (ruleIds.value.length === 0) {
      error.value = 'Missing query: pass requestId= or ruleIds= (comma-separated).'
      return
    }

    const responses = await Promise.all(ruleIds.value.map((id) => requestsService.getRuleGraph(id)))
    if (gen !== loadGeneration) return

    if (ruleIds.value.length === 1) {
      graphPayload.value = extractUnifiedGraphFromRuleResponse(responses[0])
    } else {
      graphPayload.value = mergeUnifiedGraphData(responses)
    }

    if (!graphPayload.value?.nodes?.length) {
      error.value = 'No unified_graph in API response. Ensure the backend includes graph data.'
    }
  } catch (e) {
    if (gen === loadGeneration) {
      error.value = e.message || 'Failed to load unified graph'
    }
  } finally {
    if (gen === loadGeneration) {
      loading.value = false
    }
  }
}

function handleFit() {
  graphRef.value?.fitView?.()
}

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
  () => [route.query.requestId, route.query.ruleIds],
  () => {
    load()
  },
  { immediate: true },
)
</script>
