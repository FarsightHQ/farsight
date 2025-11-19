<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <div class="h-8 bg-gray-200 rounded animate-pulse w-1/3"></div>
      <div class="grid grid-cols-3 gap-4">
        <div v-for="i in 3" :key="i" class="h-24 bg-gray-200 rounded animate-pulse"></div>
      </div>
    </div>

    <!-- Request Details -->
    <div v-else-if="request" class="flex flex-col" style="height: calc(100vh - 12rem);">
      <!-- Header -->
      <div class="mb-6 pb-4 border-b border-gray-200 flex-shrink-0">
        <div class="flex items-start justify-between">
          <!-- Left Side: Title and Info -->
          <div class="flex-1">
            <h1 class="text-3xl font-bold mb-2">{{ request.title }}</h1>
            <div class="flex items-center flex-wrap gap-2 text-sm text-gray-600">
              <span>ID: {{ request.id }}</span>
              <StatusBadge :status="request.status" />
              <span v-if="request.external_id">External ID: {{ request.external_id }}</span>
              <span class="text-gray-400">•</span>
              <span>{{ formatDate(request.created_at) }}</span>
              <span class="text-gray-400">•</span>
              <span :title="request.source_filename">{{ request.source_filename }}</span>
              <span class="text-gray-400">•</span>
              <span>{{ formatFileSize(request.source_size_bytes) }}</span>
              <span class="text-gray-400">•</span>
              <span>{{ request.created_by || 'system' }}</span>
              <span class="text-gray-400">•</span>
              <span class="font-mono text-xs">{{ request.source_sha256 }}</span>
            </div>
          </div>

          <!-- Right Side: Action Buttons -->
          <div class="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              class="text-error-600 border-error-300 hover:bg-error-50"
              @click="handleDeleteClick"
            >
              Delete
            </Button>
            <Button variant="outline" size="sm" @click="$router.push('/requests')">
              Back to List
            </Button>
          </div>
        </div>
      </div>

      <!-- 2-Column Layout -->
      <div class="flex gap-6 flex-1 overflow-hidden min-h-0">
        <!-- Left Sidebar: Filters -->
        <aside class="w-72 flex-shrink-0 overflow-y-auto">
          <RulesFilter :filters="filters" :rules="rulesData" @update:filters="handleFilterUpdate" />
        </aside>

        <!-- Right Column: Rules List (Expanded) -->
        <main class="flex-1 overflow-y-auto min-w-0">
          <RuleDetail
            v-if="showRuleDetail && selectedRule"
            :rule="selectedRule"
            :request-id="request.id"
            @back="handleBackToRules"
            @visualize="handleVisualizeRule"
          />
          <RulesList
            v-else
            :request-id="request.id"
            :filters="filters"
            @view-rule="handleViewRule"
            @stats-updated="handleStatsUpdated"
            @rules-loaded="handleRulesLoaded"
            @visualize-rule="handleVisualizeRule"
            @visualize-multiple-rules="handleVisualizeMultipleRules"
          />
        </main>
      </div>
    </div>

    <!-- Error State -->
    <Card v-else>
      <div class="text-center py-12">
        <p class="text-gray-600">Request not found</p>
        <Button variant="primary" class="mt-4" @click="$router.push('/requests')">
          Back to Requests
        </Button>
      </div>
    </Card>

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmModal
      v-model="showDeleteModal"
      :request="request"
      :deleting="deleting"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />

    <!-- Network Graph Visualization Modal -->
    <NetworkGraphModal
      v-model="showGraphModal"
      :rule-id="selectedRuleForVisualization?.id"
      :rule-title="selectedRuleForVisualization?.title || `Rule ${selectedRuleForVisualization?.id}`"
      :graph-data="mergedGraphData"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import StatusBadge from '@/components/requests/StatusBadge.vue'
import DeleteConfirmModal from '@/components/requests/DeleteConfirmModal.vue'
import RulesList from '@/components/requests/RulesList.vue'
import RulesFilter from '@/components/requests/RulesFilter.vue'
import RuleDetail from '@/components/requests/RuleDetail.vue'
import NetworkGraphModal from '@/components/requests/NetworkGraphModal.vue'

const route = useRoute()
const router = useRouter()
const { success, error } = useToast()

const loading = ref(false)
const request = ref(null)
const showDeleteModal = ref(false)
const deleting = ref(false)
const showGraphModal = ref(false)
const selectedRule = ref(null)
const selectedRuleForVisualization = ref(null)
const mergedGraphData = ref(null)
const showRuleDetail = ref(false)
const rulesStats = ref({})
const rulesData = ref([])
const filters = ref({
  action: '',
  protocol: '',
  direction: '',
  hasFacts: '',
  selfFlow: '',
  anyAny: '',
  publicIP: '',
  hasIssues: '',
})

const fetchRequest = async () => {
  loading.value = true
  try {
    const response = await requestsService.get(route.params.id)
    request.value = response.data || response
  } catch (err) {
    error(err.message || 'Failed to load request')
    request.value = null
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const handleDeleteClick = () => {
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!request.value) return

  deleting.value = true
  try {
    await requestsService.delete(request.value.id)
    success(`Request "${request.value.title}" deleted successfully`)
    
    // Redirect to list page
    router.push('/requests')
  } catch (err) {
    error(err.message || 'Failed to delete request')
    deleting.value = false
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
}

const handleViewRule = async (rule) => {
  // If rule already has full details, show it
  if (rule.endpoints && rule.services) {
    selectedRule.value = rule
    showRuleDetail.value = true
  } else {
    // Fetch full rule details
    try {
      const { rulesService } = await import('@/services/rules')
      const response = await rulesService.getRule(rule.id)
      selectedRule.value = response.data || response
      showRuleDetail.value = true
    } catch (err) {
      error(err.message || 'Failed to load rule details')
    }
  }
}

const handleBackToRules = () => {
  showRuleDetail.value = false
  selectedRule.value = null
}

const handleFilterUpdate = (newFilters) => {
  filters.value = { ...newFilters }
}

const handleStatsUpdated = (stats) => {
  rulesStats.value = stats
}

const handleRulesLoaded = (rules) => {
  rulesData.value = rules || []
}

const handleVisualizeRule = (rule) => {
  selectedRuleForVisualization.value = rule
  mergedGraphData.value = null // Clear merged data for single rule
  showGraphModal.value = true
}

const handleVisualizeMultipleRules = (data) => {
  mergedGraphData.value = data.graphData
  selectedRuleForVisualization.value = { 
    id: data.ruleIds.join(', '), 
    title: `${data.ruleIds.length} Selected Rules` 
  }
  showGraphModal.value = true
}

onMounted(() => {
  fetchRequest()
})
</script>
