<template>
  <div class="flex flex-col" style="height: calc(100vh - 12rem);">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 pb-4 border-b border-theme-border-default flex-shrink-0">
      <div>
        <h1 class="text-3xl font-bold mb-2">All Rules</h1>
        <p class="text-sm text-theme-text-content">View and analyze firewall rules across all FAR requests</p>
      </div>
    </div>

    <!-- 3-Column Layout -->
    <div class="flex gap-6 flex-1 overflow-hidden min-h-0">
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
              <span class="text-theme-text-content font-semibold">{{ summary.total_rules || 0 }}</span>
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
              <span class="text-theme-text-content font-semibold">{{ summary.unique_sources || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-theme-text-content">Unique Destinations:</span>
              <span class="text-theme-text-content font-semibold">{{ summary.unique_destinations || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-theme-text-content">Protocols:</span>
              <span class="text-theme-text-content font-semibold">{{ summary.protocols_used?.length || 0 }}</span>
            </div>
            <div v-if="summary.protocols_used && summary.protocols_used.length > 0" class="mt-4 pt-4 border-t border-theme-border-card">
              <span class="font-medium text-theme-text-content block mb-2">Protocols Used:</span>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="protocol in summary.protocols_used"
                  :key="protocol"
                  class="px-2 py-1 bg-theme-active text-theme-text-content rounded text-xs"
                >
                  {{ protocol }}
                </span>
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
      :rule-title="selectedRuleForVisualization?.title || `Rule ${selectedRuleForVisualization?.id}`"
      :graph-data="mergedGraphData"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import RulesFilter from '@/components/requests/RulesFilter.vue'
import RulesList from '@/components/requests/RulesList.vue'
import NetworkGraphModal from '@/components/requests/NetworkGraphModal.vue'

const router = useRouter()

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

const handleFilterUpdate = (newFilters) => {
  filters.value = { ...filters.value, ...newFilters }
}

const handleViewRule = (rule) => {
  // Navigate to standalone route for rule detail
  router.push(`/rules/${rule.id}`)
}

const handleStatsUpdated = (stats) => {
  summary.value = stats
}

const handleRulesLoaded = (rules) => {
  rulesData.value = rules
}

const handleVisualizeRule = (rule) => {
  selectedRuleForVisualization.value = rule
  mergedGraphData.value = null
  showGraphModal.value = true
}

const handleVisualizeMultipleRules = (data) => {
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

