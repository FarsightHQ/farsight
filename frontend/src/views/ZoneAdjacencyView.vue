<template>
  <VizWorkspaceLayout :title="''" :subtitle="''">
    <template #heading>
      <h1 class="text-base sm:text-lg font-semibold text-gray-900 leading-snug break-words">
        Zone adjacency heat map
      </h1>
      <p v-if="layoutSubtitle" class="text-xs sm:text-sm text-gray-600 mt-1 break-words">
        {{ layoutSubtitle }}
      </p>
      <p class="text-xs text-gray-500 mt-2 leading-snug">
        Cell values aggregate directed policy edges between zones (from row → to column), derived from the
        same unified graph as the topology view.
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

      <ZoneAdjacencyHeatmap
        v-else
        :row-labels="matrixResult.rowLabels"
        :col-labels="matrixResult.colLabels"
        :matrix="matrixResult.matrix"
        :cell-detail="matrixResult.cellDetail"
        :max-value="matrixResult.maxValue"
        :metric="metric"
        :group-by="groupBy"
        :clear-stamp="heatmapClearStamp"
        @cell-select="onCellSelect"
      />
    </template>

    <template #panel>
      <div v-if="largeMatrixWarning" class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-md p-2">
        Large matrix ({{ matrixResult.rowLabels.length }}×{{ matrixResult.colLabels.length }}). Scroll the
        canvas to see all cells.
      </div>

      <div class="space-y-1 text-sm text-gray-700">
        <p class="font-medium text-gray-900">Summary</p>
        <ul class="list-none space-y-0.5 text-xs sm:text-sm">
          <li>{{ graphSummary.nodes }} nodes</li>
          <li>{{ graphSummary.links }} links</li>
          <li v-if="graphSummary.rules != null">{{ graphSummary.rules }} rules</li>
          <li v-if="!loading && graphPayload?.nodes?.length">
            Non-empty cells: {{ matrixResult.nonEmptyCellCount }}
          </li>
          <li v-if="!loading && graphPayload?.nodes?.length">Max cell value: {{ matrixResult.maxValue }}</li>
        </ul>
      </div>

      <div class="space-y-2">
        <label class="block text-xs font-medium text-gray-600" for="zone-group-by">Group by</label>
        <select
          id="zone-group-by"
          v-model="groupBy"
          class="w-full max-w-full box-border px-3 py-2 border border-gray-300 rounded-md text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="segment">Segment</option>
          <option value="location">Location</option>
          <option value="vlan">VLAN</option>
        </select>
      </div>

      <div class="space-y-2">
        <label class="block text-xs font-medium text-gray-600" for="zone-metric">Cell metric</label>
        <select
          id="zone-metric"
          v-model="metric"
          class="w-full max-w-full box-border px-3 py-2 border border-gray-300 rounded-md text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="rules">Distinct rules</option>
          <option value="services">Distinct services</option>
          <option value="binary">Binary (allowed)</option>
        </select>
      </div>

      <div
        v-if="selectedDetail"
        class="space-y-2 border border-gray-200 rounded-md p-3 bg-gray-50"
      >
        <div class="flex items-start justify-between gap-2">
          <p class="text-xs font-medium text-gray-800">Cell drill-down</p>
          <button
            type="button"
            class="text-xs text-blue-600 hover:text-blue-800 shrink-0"
            @click="clearSelection"
          >
            Clear
          </button>
        </div>
        <p class="text-xs text-gray-800 leading-snug">
          <span class="font-semibold">{{ selectedDetail.rowLabel }}</span>
          →
          <span class="font-semibold">{{ selectedDetail.colLabel }}</span>
        </p>
        <ul class="list-none text-xs text-gray-700 space-y-1 m-0 p-0">
          <li>Unified edges in cell: {{ selectedDetail.linkCount }}</li>
          <li>Distinct rules: {{ selectedDetail.ruleIds.length }}</li>
          <li>Distinct services: {{ selectedDetail.services.length }}</li>
        </ul>
        <div v-if="selectedDetail.ruleIds.length" class="space-y-1">
          <p class="text-[11px] font-medium text-gray-600">Rule IDs</p>
          <p class="text-[11px] font-mono text-gray-800 break-all leading-relaxed">
            {{ selectedDetail.ruleIds.join(', ') }}
          </p>
        </div>
        <div v-if="selectedDetail.services.length" class="space-y-1">
          <p class="text-[11px] font-medium text-gray-600">Services (sample)</p>
          <ul class="list-none m-0 p-0 max-h-40 overflow-y-auto text-[11px] font-mono text-gray-800 space-y-0.5">
            <li v-for="(s, idx) in displayedServices" :key="idx">
              {{ s.protocol }}/{{ s.formatted_ports || s.port_ranges || '—' }}
            </li>
          </ul>
          <button
            v-if="selectedDetail.services.length > servicePreviewLimit"
            type="button"
            class="text-[11px] text-blue-600 hover:text-blue-800"
            @click="showAllServices = !showAllServices"
          >
            {{ showAllServices ? 'Show less' : `Show all (${selectedDetail.services.length})` }}
          </button>
        </div>
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
import { buildZoneAdjacencyMatrix } from '@/utils/zoneAdjacencyMatrix'
import ZoneAdjacencyHeatmap from '@/components/requests/ZoneAdjacencyHeatmap.vue'
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
const groupBy = ref('segment')
const metric = ref('rules')
const selectedDetail = ref(null)
const showAllServices = ref(false)
const heatmapClearStamp = ref(0)
const servicePreviewLimit = 12

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

const matrixResult = computed(() =>
  buildZoneAdjacencyMatrix(graphPayload.value, {
    groupBy: groupBy.value,
    metric: metric.value,
  })
)

const largeMatrixWarning = computed(
  () => !loading.value && matrixResult.value.rowLabels.length > 24
)

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

const displayedServices = computed(() => {
  if (!selectedDetail.value?.services?.length) return []
  if (showAllServices.value) return selectedDetail.value.services
  return selectedDetail.value.services.slice(0, servicePreviewLimit)
})

function clearSelection() {
  selectedDetail.value = null
  showAllServices.value = false
  heatmapClearStamp.value += 1
}

function onCellSelect(payload) {
  showAllServices.value = false
  selectedDetail.value = payload?.detail ?? null
}

watch([groupBy, metric], () => {
  clearSelection()
})

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
      error.value = e.message || 'Failed to load data'
    }
  } finally {
    if (gen === loadGeneration) {
      loading.value = false
    }
  }
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
  { immediate: true }
)
</script>
