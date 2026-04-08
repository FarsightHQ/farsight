<template>
  <div class="flex flex-col flex-1 min-h-0 min-w-0">
    <PageFrame
      class="flex-1 min-h-0 flex flex-col"
      :scroll-body="false"
      :breadcrumb-items="breadcrumbItems"
      :title="pageTitle"
    >
      <template v-if="request" #subtitle>
        <div class="flex flex-wrap items-center gap-x-2 gap-y-1 text-theme-text-muted">
          <span>ID: {{ request.id }}</span>
          <StatusBadge :status="request.status" />
          <span v-if="request.external_id">External ID: {{ request.external_id }}</span>
          <span class="text-theme-text-muted/50">•</span>
          <span>{{ formatDate(request.created_at) }}</span>
          <span class="text-theme-text-muted/50">•</span>
          <span :title="request.source_filename" class="truncate max-w-[12rem]">{{
            request.source_filename
          }}</span>
          <span class="text-theme-text-muted/50">•</span>
          <span>{{ formatFileSize(request.source_size_bytes) }}</span>
          <span class="text-theme-text-muted/50">•</span>
          <span>Uploaded by: {{ request.created_by || '—' }}</span>
          <span class="text-theme-text-muted/50">•</span>
          <span class="font-mono text-xs">{{ request.source_sha256 }}</span>
        </div>
      </template>

      <template #actions>
        <template v-if="request">
          <Button variant="danger" @click="handleDeleteClick">Delete</Button>
          <Button variant="outline" @click="goRequestsList">Back to list</Button>
        </template>
      </template>

      <DetailPageSkeleton v-if="loading" :columns="3" :card-count="3" />

      <div v-else-if="request" class="flex flex-col flex-1 min-h-0 overflow-hidden">
        <div class="flex gap-6 flex-1 min-h-0 overflow-hidden">
          <aside class="w-72 flex-shrink-0 overflow-y-auto">
            <RulesFilter
              :filters="filters"
              :rules="rulesData"
              @update:filters="handleFilterUpdate"
            />
          </aside>
          <main class="flex-1 overflow-y-auto min-w-0">
            <RulesList
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

      <EmptyState v-else message="Request not found">
        <Button variant="primary" @click="goRequestsList">Back to Requests</Button>
      </EmptyState>
    </PageFrame>

    <DeleteConfirmModal
      v-model="showDeleteModal"
      :request="request"
      :deleting="deleting"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />

    <NetworkGraphModal
      v-model="showGraphModal"
      :rule-id="selectedRuleForVisualization?.id"
      :rule-title="
        selectedRuleForVisualization?.title || `Rule ${selectedRuleForVisualization?.id}`
      "
      :prefetched-graph="mergedGraphData"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectPath } from '@/utils/projectRoutes'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'
import PageFrame from '@/components/layout/PageFrame.vue'
import Button from '@/components/ui/Button.vue'
import DetailPageSkeleton from '@/components/ui/DetailPageSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import DeleteConfirmModal from '@/components/requests/DeleteConfirmModal.vue'
import RulesList from '@/components/requests/RulesList.vue'
import RulesFilter from '@/components/requests/RulesFilter.vue'
const NetworkGraphModal = defineAsyncComponent(() =>
  import('@/components/requests/NetworkGraphModal.vue')
)
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const route = useRoute()
const router = useRouter()
const { success, error } = useToast()

const request = ref(null)
const loading = ref(false)
const { breadcrumbItems } = usePageBreadcrumbs({
  requestTitle: computed(() => request.value?.title ?? ''),
})

const pageTitle = computed(() => {
  if (loading.value) return 'Request'
  if (request.value?.title) return request.value.title
  return route.params.id ? `Request ${route.params.id}` : 'Request'
})

const goRequestsList = () => {
  router.push(projectPath('/requests', route.params.projectId))
}

const showDeleteModal = ref(false)
const deleting = ref(false)
const showGraphModal = ref(false)
const selectedRuleForVisualization = ref(null)
const mergedGraphData = ref(null)
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

const formatDate = dateString => {
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

const formatFileSize = bytes => {
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
    router.push(projectPath('/requests', route.params.projectId))
  } catch (err) {
    error(err.message || 'Failed to delete request')
    deleting.value = false
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
}

const handleViewRule = async rule => {
  router.push(projectPath(`/requests/${route.params.id}/rules/${rule.id}`, route.params.projectId))
}

const handleFilterUpdate = newFilters => {
  filters.value = { ...newFilters }
}

const handleStatsUpdated = stats => {
  rulesStats.value = stats
}

const handleRulesLoaded = rules => {
  rulesData.value = rules || []
}

const handleVisualizeRule = rule => {
  selectedRuleForVisualization.value = rule
  mergedGraphData.value = null
  showGraphModal.value = true
}

const handleVisualizeMultipleRules = data => {
  mergedGraphData.value = data.graphData
  selectedRuleForVisualization.value = {
    id: data.ruleIds.join(', '),
    title: `${data.ruleIds.length} Selected Rules`,
  }
  showGraphModal.value = true
}

onMounted(() => {
  fetchRequest()
})
</script>
