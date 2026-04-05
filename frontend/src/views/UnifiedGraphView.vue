<template>
  <div class="flex flex-col bg-gray-100 min-h-[calc(100dvh-9rem)]">
    <header class="bg-white border-b border-gray-200 px-6 py-4 flex flex-wrap items-center gap-4 shrink-0">
      <div class="flex-1 min-w-0">
        <h1 class="text-xl font-semibold text-gray-900 truncate">Unified network topology</h1>
        <p class="text-sm text-gray-600 mt-0.5 truncate">{{ subtitle }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <input
          v-model="filterText"
          type="search"
          placeholder="Filter nodes…"
          class="px-3 py-2 border border-gray-300 rounded-md text-sm w-48 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <Button variant="outline" size="sm" @click="handleFit">Fit to view</Button>
      </div>
    </header>

    <div v-if="loading" class="flex-1 flex items-center justify-center p-12">
      <Spinner size="lg" class="mr-3" />
      <span class="text-gray-600">Loading graph…</span>
    </div>

    <div v-else-if="error" class="flex-1 flex items-center justify-center p-12">
      <div class="text-center max-w-md">
        <p class="text-red-600 font-medium">{{ error }}</p>
        <Button class="mt-4" variant="primary" @click="load">Retry</Button>
      </div>
    </div>

    <div v-else-if="!graphPayload?.nodes?.length" class="flex-1 flex items-center justify-center p-12 text-gray-600">
      No unified graph data for this selection.
    </div>

    <main v-else class="flex-1 flex flex-col p-4 min-h-0 overflow-hidden">
      <div class="flex flex-wrap gap-4 mb-3 text-xs text-gray-600 shrink-0">
        <span>{{ graphPayload.metadata?.node_count ?? graphPayload.nodes.length }} nodes</span>
        <span>{{ graphPayload.metadata?.link_count ?? graphPayload.links?.length ?? 0 }} links</span>
        <span v-if="graphPayload.metadata?.rule_count != null">{{ graphPayload.metadata.rule_count }} rules</span>
      </div>
      <div class="flex-1 min-h-0">
        <UnifiedNetworkGraph ref="graphRef" :unified-graph="graphPayload" :filter-text="filterText" />
      </div>
      <div v-if="legendSegments.length" class="mt-4 flex flex-wrap gap-2">
        <span class="text-xs font-medium text-gray-500 w-full">Segments</span>
        <span
          v-for="seg in legendSegments"
          :key="seg"
          class="inline-flex items-center gap-1 px-2 py-1 rounded bg-white border border-gray-200 text-xs text-gray-700"
        >
          <span class="w-2 h-2 rounded-full" :style="{ background: legendColor(seg) }" />
          {{ seg }}
        </span>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import * as d3 from 'd3'
import { requestsService } from '@/services/requests'
import { mergeUnifiedGraphData, extractUnifiedGraphFromRuleResponse } from '@/utils/unifiedGraphMerge'
import UnifiedNetworkGraph from '@/components/requests/UnifiedNetworkGraph.vue'
import Button from '@/components/ui/Button.vue'
import Spinner from '@/components/ui/Spinner.vue'
import { useSidebar } from '@/composables/useSidebar'

const route = useRoute()
const { setSidebarCollapsed, isCollapsed } = useSidebar()
/** Snapshot so we restore sidebar when leaving this page (does not overwrite localStorage). */
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

async function load() {
  loading.value = true
  error.value = null
  graphPayload.value = null

  try {
    if (requestId.value != null) {
      const res = await requestsService.getNetworkTopology(requestId.value)
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

    if (ruleIds.value.length === 1) {
      graphPayload.value = extractUnifiedGraphFromRuleResponse(responses[0])
    } else {
      graphPayload.value = mergeUnifiedGraphData(responses)
    }

    if (!graphPayload.value?.nodes?.length) {
      error.value = 'No unified_graph in API response. Ensure the backend includes graph data.'
    }
  } catch (e) {
    error.value = e.message || 'Failed to load unified graph'
  } finally {
    loading.value = false
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
