<template>
  <VizWorkspaceLayout :title="''" :subtitle="''">
    <template #heading>
      <h1 class="text-base sm:text-lg font-semibold text-gray-900 leading-snug break-words">
        Unified network topology
      </h1>
      <p v-if="layoutSubtitle" class="text-xs sm:text-sm text-gray-600 mt-1 break-words">
        {{ layoutSubtitle }}
      </p>
      <p class="text-xs text-gray-500 mt-2 leading-snug">
        Directed paths show allowed reachability from merged firewall rules. Arrows are policy
        direction, not physical topology.
      </p>
    </template>

    <template #default>
      <div
        v-if="loading"
        class="absolute inset-0 flex items-center justify-center bg-gray-100 z-10"
      >
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

      <div
        v-else-if="filteredGraph.nodes.length === 0"
        class="absolute inset-0 flex items-center justify-center bg-gray-100 z-10 p-6 text-gray-600 text-center"
      >
        No nodes match the current filter or segment focus.
      </div>

      <UnifiedNetworkGraph
        v-else
        ref="graphRef"
        class="h-full w-full"
        :unified-graph="graphPayload"
        :filter-text="filterText"
        :segment-focus="segmentFocus"
        :emphasize-cross-segment="emphasizeCrossSegment"
        :show-vlan-hulls="showVlanHulls"
        :selected-node-id="selectedNodeId"
        :selected-link-key="selectedLinkKey"
        @update:selected-node-id="selectedNodeId = $event"
        @update:selected-link-key="selectedLinkKey = $event"
      />
    </template>

    <template #panel>
      <div class="space-y-1 text-sm text-gray-700">
        <p class="font-medium text-gray-900">Summary</p>
        <ul class="list-none space-y-0.5 text-xs sm:text-sm">
          <li>{{ graphSummary.nodes }} nodes</li>
          <li>{{ graphSummary.links }} links</li>
          <li v-if="graphSummary.rules != null">{{ graphSummary.rules }} rules</li>
          <li v-if="!loading && graphPayload?.nodes?.length">
            Cross-segment links: {{ crossSegmentCount }}
          </li>
        </ul>
        <p class="text-xs text-gray-500 pt-1">Hover an edge for rules and services.</p>
      </div>

      <div v-if="hasSelection" class="space-y-2 border border-gray-200 rounded-md p-3 bg-gray-50">
        <div class="flex items-start justify-between gap-2">
          <p class="text-xs font-medium text-gray-800">Selection</p>
          <button
            type="button"
            class="text-xs text-blue-600 hover:text-blue-800 shrink-0"
            @click="clearSelection"
          >
            Clear
          </button>
        </div>
        <pre
          v-if="selectionLines.length"
          class="whitespace-pre-wrap font-mono text-[11px] text-gray-800 leading-relaxed m-0"
          >{{ selectionLines.join('\n') }}</pre
        >
      </div>

      <div class="space-y-2">
        <label class="block text-xs font-medium text-gray-600" for="unified-graph-filter"
          >Filter nodes</label
        >
        <input
          id="unified-graph-filter"
          v-model="filterText"
          type="search"
          placeholder="CIDR, hostname, segment…"
          class="w-full max-w-full box-border px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div class="space-y-2">
        <label class="block text-xs font-medium text-gray-600" for="unified-segment-focus"
          >Focus segment</label
        >
        <select
          id="unified-segment-focus"
          v-model="segmentFocus"
          class="w-full max-w-full box-border px-3 py-2 border border-gray-300 rounded-md text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">All segments</option>
          <option v-for="seg in legendSegments" :key="seg" :value="seg">{{ seg }}</option>
        </select>
        <p class="text-xs text-gray-500 leading-snug">
          Shows this segment and direct neighbors (after text filter).
        </p>
      </div>

      <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <Button
          variant="outline"
          size="sm"
          class="w-full sm:flex-1 justify-center"
          @click="handleFit"
        >
          Fit to view
        </Button>
        <label
          class="flex items-center gap-2 text-xs text-gray-700 cursor-pointer select-none whitespace-nowrap"
        >
          <input v-model="emphasizeCrossSegment" type="checkbox" class="rounded border-gray-300" />
          Highlight cross-segment
        </label>
      </div>

      <div class="space-y-1">
        <label
          class="flex items-start gap-2 text-xs text-gray-700 cursor-pointer select-none"
          for="unified-show-vlan-hulls"
        >
          <input
            id="unified-show-vlan-hulls"
            v-model="showVlanHulls"
            type="checkbox"
            class="rounded border-gray-300 mt-0.5 shrink-0"
          />
          <span>
            Show VLAN outlines
            <span class="block text-[11px] text-gray-500 font-normal leading-snug mt-0.5">
              Dashed hulls from asset VLAN (larger than segment); turn off if too busy.
            </span>
          </span>
        </label>
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
import { requestsService } from '@/services/requests'
import {
  mergeUnifiedGraphData,
  extractUnifiedGraphFromRuleResponse,
} from '@/utils/unifiedGraphMerge'
import { filterUnifiedGraph, countCrossSegmentLinks } from '@/utils/unifiedGraphFilter'
import { formatNodeDetailLines, formatLinkDetailLines } from '@/utils/unifiedGraphFormat'
import { buildSegmentColorScale } from '@/utils/unifiedGraphHulls'
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
const segmentFocus = ref('')
const emphasizeCrossSegment = ref(false)
const showVlanHulls = ref(true)
const selectedNodeId = ref(null)
const selectedLinkKey = ref(null)
const graphRef = ref(null)

const ruleIds = computed(() => {
  const q = route.query.ruleIds
  if (!q) return []
  return String(q)
    .split(',')
    .map(s => parseInt(s.trim(), 10))
    .filter(n => !Number.isNaN(n))
})

const requestId = computed(() => {
  const q = route.query.requestId
  if (q == null || q === '') return null
  const n = parseInt(String(q), 10)
  return Number.isNaN(n) ? null : n
})

const layoutSubtitle = computed(() => {
  if (route.query.title) return String(route.query.title)
  if (requestId.value != null) return `Request #${requestId.value}`
  if (ruleIds.value.length) return `Rules: ${ruleIds.value.join(', ')}`
  return 'Open from a rule or request with graph data'
})

const legendSegments = computed(() => {
  const nodes = graphPayload.value?.nodes || []
  return [...new Set(nodes.map(n => n.segment || 'Unknown'))].sort()
})

const segmentColorFn = computed(() => buildSegmentColorScale(legendSegments.value))

function legendColor(seg) {
  return segmentColorFn.value(seg)
}

const filteredGraph = computed(() => {
  if (!graphPayload.value?.nodes?.length) {
    return { nodes: [], links: [] }
  }
  return filterUnifiedGraph(graphPayload.value, {
    filterText: filterText.value,
    segmentFocus: segmentFocus.value,
  })
})

const crossSegmentCount = computed(() =>
  countCrossSegmentLinks(filteredGraph.value.nodes, filteredGraph.value.links)
)

const graphSummary = computed(() => {
  if (loading.value || !graphPayload.value?.nodes?.length) {
    return { nodes: '—', links: '—', rules: null }
  }
  const g = graphPayload.value
  const fg = filteredGraph.value
  const rules = g.metadata?.rule_count ?? null
  return {
    nodes: fg.nodes.length,
    links: fg.links.length,
    rules,
  }
})

const selectedNode = computed(() => {
  if (selectedNodeId.value == null) return null
  const id = String(selectedNodeId.value)
  return filteredGraph.value.nodes.find(n => String(n.id) === id) || null
})

const selectedLink = computed(() => {
  if (!selectedLinkKey.value) return null
  const k = selectedLinkKey.value
  return filteredGraph.value.links.find(l => `${l.source}->${l.target}` === k) || null
})

const hasSelection = computed(() => selectedNode.value != null || selectedLink.value != null)

const selectionLines = computed(() => {
  if (selectedNode.value) return formatNodeDetailLines(selectedNode.value)
  if (selectedLink.value) return formatLinkDetailLines(selectedLink.value)
  return []
})

function clearSelection() {
  selectedNodeId.value = null
  selectedLinkKey.value = null
}

function pruneSelectionToFilter() {
  const { nodes } = filteredGraph.value
  const idSet = new Set(nodes.map(n => String(n.id)))
  if (selectedNodeId.value != null && !idSet.has(String(selectedNodeId.value))) {
    selectedNodeId.value = null
  }
  if (selectedLinkKey.value) {
    const parts = selectedLinkKey.value.split('->')
    if (parts.length !== 2 || !idSet.has(parts[0]) || !idSet.has(parts[1])) {
      selectedLinkKey.value = null
    }
  }
}

function onGlobalKeydown(e) {
  if (e.key === 'Escape') clearSelection()
}

let loadGeneration = 0

async function load() {
  const gen = ++loadGeneration
  loading.value = true
  error.value = null
  graphPayload.value = null
  clearSelection()

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

    const responses = await Promise.all(ruleIds.value.map(id => requestsService.getRuleGraph(id)))
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

watch([filteredGraph, filterText, segmentFocus], () => {
  pruneSelectionToFilter()
})

onMounted(() => {
  sidebarStateBeforeViz.value = isCollapsed.value
  setSidebarCollapsed(true, { persist: false })
  window.addEventListener('keydown', onGlobalKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown)
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
  { immediate: true }
)
</script>
