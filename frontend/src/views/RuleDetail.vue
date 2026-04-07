<template>
  <div class="flex flex-col flex-1 min-h-0 min-w-0">
    <PageFrame
      class="flex-1 min-h-0 flex flex-col"
      :breadcrumb-items="breadcrumbItems"
      :title="pageTitle"
      subtitle="Firewall rule details and coverage."
    >
      <template #actions>
        <Button variant="outline" size="sm" @click="handleBack">Back</Button>
      </template>

      <RuleDetail
        v-if="rule"
        :rule="rule"
        :request-id="requestId || rule.request?.id"
        :loading="loading"
        @back="handleBack"
        @visualize="handleVisualizeRule"
      />
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
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectPath } from '@/utils/projectRoutes'
import PageFrame from '@/components/layout/PageFrame.vue'
import Button from '@/components/ui/Button.vue'
import RuleDetail from '@/components/requests/RuleDetail.vue'
import NetworkGraphModal from '@/components/requests/NetworkGraphModal.vue'
import { rulesService } from '@/services/rules'
import { useToast } from '@/composables/useToast'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

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

const { breadcrumbItems } = usePageBreadcrumbs({
  requestTitle: computed(() => rule.value?.request?.title ?? ''),
  ruleLabel: computed(() =>
    rule.value?.id ? `Rule ${rule.value.id}` : ruleId.value ? `Rule ${ruleId.value}` : 'Rule'
  ),
})

const pageTitle = computed(() =>
  rule.value?.id ? `Rule ${rule.value.id}` : ruleId.value ? `Rule ${ruleId.value}` : 'Rule'
)

const handleBack = () => {
  const currentRequestId = requestId.value || rule.value?.request?.id
  const pid = route.params.projectId
  if (currentRequestId) {
    router.push(projectPath(`/requests/${currentRequestId}`, pid))
  } else {
    router.push(projectPath('/rules', pid))
  }
}

const handleVisualizeRule = r => {
  selectedRuleForVisualization.value = r
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
