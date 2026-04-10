<template>
  <div class="flex flex-col flex-1 min-h-0 min-w-0">
    <PageFrame
      class="flex-1 min-h-0 flex flex-col"
      :breadcrumb-items="breadcrumbItems"
      :title="pageTitle"
    >
      <template #subtitle>
        <div
          v-if="rule"
          class="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-theme-text-muted"
        >
          <StatusBadge
            :status="rule.action === 'allow' ? 'success' : 'error'"
            :label="rule.action"
          />
          <span v-if="rule.direction">Direction: {{ rule.direction }}</span>
          <span class="text-theme-text-muted/50">•</span>
          <span>Created: {{ formatRuleDate(rule.created_at) }}</span>
        </div>
      </template>

      <template #actions>
        <Button variant="outline" @click="handleBack">Back</Button>
        <Button
          variant="primary"
          :disabled="!rule || !hasNetworkData"
          :title="
            !rule
              ? ''
              : !hasNetworkData
                ? 'This rule has no network data to visualize'
                : 'Visualize network topology'
          "
          @click="triggerVisualize"
        >
          Visualize
        </Button>
        <Button
          variant="outline"
          :disabled="!rule || !hasNetworkData"
          :title="!hasNetworkData ? 'No network data' : 'Open unified topology in a new tab'"
          @click="openUnifiedTab"
        >
          Unified view
        </Button>
        <Button
          variant="outline"
          :disabled="!rule || !hasNetworkData"
          :title="
            !hasNetworkData
              ? 'No network data'
              : 'Open classic rule topology workspace in a new tab'
          "
          @click="openClassicTab"
        >
          Classic view (new tab)
        </Button>
        <Button
          variant="outline"
          :disabled="!rule || !hasNetworkData"
          :title="!hasNetworkData ? 'No network data' : 'Open zone adjacency heat map in a new tab'"
          @click="openZoneTab"
        >
          Zone heat map
        </Button>
      </template>

      <RuleDetailPanel v-if="rule" :rule="rule" :request-id="requestId || rule.request?.id" />

      <DetailPageSkeleton v-else-if="loading" :columns="2" :card-count="4" />

      <EmptyState v-else message="Rule not found">
        <Button variant="outline" @click="handleBack">Back</Button>
      </EmptyState>
    </PageFrame>

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
import { ref, onMounted, computed, watch, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectPath } from '@/utils/projectRoutes'
import PageFrame from '@/components/layout/PageFrame.vue'
import Button from '@/components/ui/Button.vue'
import DetailPageSkeleton from '@/components/ui/DetailPageSkeleton.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import RuleDetailPanel from '@/components/requests/RuleDetailPanel.vue'
const NetworkGraphModal = defineAsyncComponent(
  () => import('@/components/requests/NetworkGraphModal.vue')
)
import { rulesService } from '@/services/rules'
import { useToast } from '@/composables/useToast'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'
import { useRuleGraphNavigation } from '@/composables/useRuleGraphNavigation'

const route = useRoute()
const router = useRouter()
const { error: showError } = useToast()

const ruleId = computed(() => route.params.ruleId || route.params.id)
const requestId = computed(() => route.params.requestId || null)
const rule = ref(null)
const loading = ref(true)
const showGraphModal = ref(false)
const selectedRuleForVisualization = ref(null)
const mergedGraphData = ref(null)

const { hasNetworkData, openUnifiedTab, openClassicTab, openZoneTab } = useRuleGraphNavigation(rule)

const { breadcrumbItems } = usePageBreadcrumbs({
  requestTitle: computed(() => rule.value?.request?.title ?? ''),
  ruleLabel: computed(() =>
    rule.value?.id ? `Rule ${rule.value.id}` : ruleId.value ? `Rule ${ruleId.value}` : 'Rule'
  ),
})

const pageTitle = computed(() =>
  rule.value?.id ? `Rule ${rule.value.id}` : ruleId.value ? `Rule ${ruleId.value}` : 'Rule'
)

function formatRuleDate(dateString) {
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

const handleBack = () => {
  const currentRequestId = requestId.value || rule.value?.request?.id
  const pid = route.params.projectId
  if (currentRequestId) {
    router.push(projectPath(`/requests/${currentRequestId}`, pid))
  } else {
    router.push(projectPath('/rules', pid))
  }
}

function triggerVisualize() {
  if (!rule.value) return
  selectedRuleForVisualization.value = rule.value
  mergedGraphData.value = null
  showGraphModal.value = true
}

const fetchRule = async () => {
  loading.value = true
  try {
    const response = await rulesService.getRule(ruleId.value, {
      include: 'all',
    })

    const responseData = response.data || response
    const data = responseData.data || responseData

    if (data) {
      rule.value = {
        id: data.rule_id || data.id,
        action: data.rule_details?.action || data.action,
        direction: data.rule_details?.direction || data.direction,
        created_at: data.rule_details?.created_at || data.created_at,
        canonical_hash: data.rule_details?.canonical_hash || data.canonical_hash,
        request_id: data.request?.id,
        endpoints: [
          ...(data.endpoints?.sources || []).map(ep => ({
            ...ep,
            endpoint_type: 'source',
            network_cidr: ep.network_cidr || ep.cidr,
          })),
          ...(data.endpoints?.destinations || []).map(ep => ({
            ...ep,
            endpoint_type: 'destination',
            network_cidr: ep.network_cidr || ep.cidr,
          })),
        ],
        services: data.services || [],
        facts: data.facts || null,
        request: data.request || null,
      }
    } else {
      rule.value = null
    }
  } catch (err) {
    showError(err.message || 'Failed to load rule')
    rule.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (ruleId.value) {
    fetchRule()
  }
})

watch([() => route.params.ruleId, () => route.params.id, () => route.params.requestId], () => {
  if (ruleId.value) {
    fetchRule()
  }
})
</script>
