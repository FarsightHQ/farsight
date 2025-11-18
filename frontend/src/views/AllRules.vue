<template>
  <div class="flex flex-col" style="height: calc(100vh - 12rem);">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 pb-4 border-b border-gray-200 flex-shrink-0">
      <div>
        <h1 class="text-3xl font-bold mb-2">All Rules</h1>
        <p class="text-sm text-gray-600">View and analyze firewall rules across all FAR requests</p>
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
        <RuleDetail
          v-if="showRuleDetail && selectedRule"
          :rule="selectedRule"
          @back="handleBackToRules"
        />
        <RulesList
          v-else
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
              <span class="font-medium text-gray-600">Total Rules:</span>
              <span class="text-gray-900 font-semibold">{{ summary.total_rules || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-600">Allow Rules:</span>
              <span class="text-green-600 font-semibold">{{ summary.allow_rules || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-600">Deny Rules:</span>
              <span class="text-red-600 font-semibold">{{ summary.deny_rules || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-600">Unique Sources:</span>
              <span class="text-gray-900 font-semibold">{{ summary.unique_sources || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-600">Unique Destinations:</span>
              <span class="text-gray-900 font-semibold">{{ summary.unique_destinations || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-600">Protocols:</span>
              <span class="text-gray-900 font-semibold">{{ summary.protocols_used?.length || 0 }}</span>
            </div>
            <div v-if="summary.protocols_used && summary.protocols_used.length > 0" class="mt-4 pt-4 border-t">
              <span class="font-medium text-gray-600 block mb-2">Protocols Used:</span>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="protocol in summary.protocols_used"
                  :key="protocol"
                  class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                >
                  {{ protocol }}
                </span>
              </div>
            </div>
          </div>
        </Card>

        <!-- Empty State -->
        <Card v-else>
          <p class="text-gray-500 text-sm">No summary data available</p>
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
import Card from '@/components/ui/Card.vue'
import RulesFilter from '@/components/requests/RulesFilter.vue'
import RulesList from '@/components/requests/RulesList.vue'
import RuleDetail from '@/components/requests/RuleDetail.vue'
import NetworkGraphModal from '@/components/requests/NetworkGraphModal.vue'

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
const showRuleDetail = ref(false)
const selectedRule = ref(null)
const showGraphModal = ref(false)
const selectedRuleForVisualization = ref(null)
const mergedGraphData = ref(null)

const handleFilterUpdate = (newFilters) => {
  filters.value = { ...filters.value, ...newFilters }
}

const handleViewRule = (rule) => {
  selectedRule.value = rule
  showRuleDetail.value = true
}

const handleBackToRules = () => {
  showRuleDetail.value = false
  selectedRule.value = null
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

