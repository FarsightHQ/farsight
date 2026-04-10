<template>
  <PageFrame
    class="flex-1 min-h-0 flex flex-col"
    :scroll-body="false"
    :breadcrumb-items="breadcrumbItems"
    title="All rules"
    subtitle="View and analyze firewall rules across all FAR requests."
  >
    <div class="flex gap-6 flex-1 min-h-0 min-w-0 overflow-hidden">
      <!-- Left Sidebar: Filters -->
      <aside class="w-72 flex-shrink-0 overflow-y-auto">
        <RulesFilter
          :filters="filters"
          :rules="rulesData"
          :show-request-filter="true"
          @update:filters="handleFilterUpdate"
        />
      </aside>

      <!-- Middle Column: Rules List -->
      <main class="flex-1 overflow-y-auto min-w-0">
        <RulesList
          :filters="filters"
          :show-request-column="true"
          @view-rule="handleViewRule"
          @stats-updated="handleStatsUpdated"
          @rules-loaded="handleRulesLoaded"
          @visualize-rule="handleVisualizeRule"
          @visualize-multiple-rules="handleVisualizeMultipleRules"
        />
      </main>

      <!-- Right Panel: Summary Statistics -->
      <aside class="w-96 flex-shrink-0 overflow-y-auto space-y-4">
        <!-- Summary Statistics -->
        <Card v-if="summary">
          <h2 class="text-lg font-semibold mb-4">Summary Statistics</h2>
          <div class="space-y-3 text-sm">
            <div class="flex items-center justify-between">
              <span class="font-medium text-theme-text-content">Total Rules:</span>
              <span class="text-theme-text-content font-semibold">{{
                summary.total_rules || 0
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-theme-text-content">Allow Rules:</span>
              <span class="text-green-600 font-semibold">{{ summary.allow_rules || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-theme-text-content">Deny Rules:</span>
              <span class="text-red-600 font-semibold">{{ summary.deny_rules || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-theme-text-content">Unique Sources:</span>
              <span class="text-theme-text-content font-semibold">{{
                summary.unique_sources || 0
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-theme-text-content">Unique Destinations:</span>
              <span class="text-theme-text-content font-semibold">{{
                summary.unique_destinations || 0
              }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-theme-text-content">Protocols:</span>
              <span class="text-theme-text-content font-semibold">{{
                summary.protocols_used?.length || 0
              }}</span>
            </div>
            <div
              v-if="summary.protocols_used && summary.protocols_used.length > 0"
              class="mt-4 pt-4 border-t border-theme-border-card"
            >
              <span class="font-medium text-theme-text-content block mb-2">Protocols used</span>
              <div class="flex flex-wrap gap-2">
                <Badge
                  v-for="protocol in summary.protocols_used"
                  :key="protocol"
                  variant="default"
                  size="sm"
                >
                  {{ protocol }}
                </Badge>
              </div>
            </div>
          </div>
        </Card>

        <!-- Empty State -->
        <Card v-else>
          <p class="text-theme-text-muted text-sm">No summary data available</p>
        </Card>
      </aside>
    </div>

    <!-- Network Graph Modal -->
    <NetworkGraphModal
      v-model="showGraphModal"
      :rule-id="selectedRuleForVisualization?.id"
      :rule-title="
        selectedRuleForVisualization?.title || `Rule ${selectedRuleForVisualization?.id}`
      "
      :prefetched-graph="mergedGraphData"
    />
  </PageFrame>
</template>

<script setup>
import { ref, computed, defineAsyncComponent } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { projectPath } from '@/utils/projectRoutes'
import PageFrame from '@/components/layout/PageFrame.vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'
import RulesFilter from '@/components/requests/RulesFilter.vue'
import RulesList from '@/components/requests/RulesList.vue'
const NetworkGraphModal = defineAsyncComponent(
  () => import('@/components/requests/NetworkGraphModal.vue')
)

const { breadcrumbItems } = usePageBreadcrumbs()

const router = useRouter()
const route = useRoute()

const filters = ref({
  action: '',
  protocol: '',
  hasFacts: '',
  selfFlow: '',
  anyAny: '',
  direction: '',
  publicIP: '',
  hasIssues: '',
  requestId: null, // New filter for request selection (null for "All Requests")
})

const rulesData = ref([])
const summary = ref(null)
const showGraphModal = ref(false)
const selectedRuleForVisualization = ref(null)
const mergedGraphData = ref(null)

const handleFilterUpdate = newFilters => {
  filters.value = { ...filters.value, ...newFilters }
}

const handleViewRule = rule => {
  router.push(projectPath(`/rules/${rule.id}`, route.params.projectId))
}

const handleStatsUpdated = stats => {
  summary.value = stats
}

const handleRulesLoaded = rules => {
  rulesData.value = rules
}

const handleVisualizeRule = rule => {
  selectedRuleForVisualization.value = rule
  mergedGraphData.value = null
  showGraphModal.value = true
}

const handleVisualizeMultipleRules = data => {
  // RulesList emits { ruleIds: [...], graphData: mergedGraph }
  // Extract graphData from the emitted object structure
  const graphData = data.graphData || data

  // Validate graph data structure
  if (!graphData || (!graphData.sources && !graphData.destinations)) {
    console.warn('[AllRules] Invalid graph data structure:', data)
    // Still try to show modal with error state
  }

  mergedGraphData.value = graphData
  selectedRuleForVisualization.value = {
    id: 'multiple',
    title: `Selected Rules (${graphData.metadata?.rule_count || data.ruleIds?.length || 0})`,
  }
  showGraphModal.value = true
}
</script>
