<template>
  <div class="space-y-6">
    <!-- Breadcrumb Navigation -->
    <nav class="flex items-center space-x-2 text-sm text-gray-600">
      <router-link to="/requests" class="hover:text-primary-600">Requests</router-link>
      <ChevronRightIcon class="h-4 w-4" />
      <router-link
        v-if="rule?.request"
        :to="`/requests/${rule.request.id}`"
        class="hover:text-primary-600"
      >
        Request {{ rule.request.id }}
      </router-link>
      <ChevronRightIcon v-if="rule?.request" class="h-4 w-4" />
      <router-link
        v-if="rule?.request"
        :to="`/requests/${rule.request.id}/rules`"
        class="hover:text-primary-600"
      >
        Rules
      </router-link>
      <ChevronRightIcon class="h-4 w-4" />
      <span class="text-gray-900 font-medium">Rule {{ ruleId }}</span>
    </nav>

    <!-- Rule Detail Component -->
    <RuleDetail
      v-if="rule"
      :rule="rule"
      :request-id="rule.request?.id"
      :loading="loading"
      @back="handleBack"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronRightIcon } from '@heroicons/vue/24/outline'
import RuleDetail from '@/components/requests/RuleDetail.vue'
import { rulesService } from '@/services/rules'
import { useToast } from '@/composables/useToast'

const route = useRoute()
const router = useRouter()
const { error: showError } = useToast()

const ruleId = computed(() => route.params.id)
const rule = ref(null)
const loading = ref(true)

const handleBack = () => {
  if (rule.value?.request?.id) {
    router.push(`/requests/${rule.value.request.id}/rules`)
  } else {
    router.push('/requests')
  }
}

const fetchRule = async () => {
  loading.value = true
  try {
    const response = await rulesService.getRule(ruleId.value, {
      include: 'all',
    })
    
    const responseData = response.data || response
    const data = responseData.data || responseData
    
    // Transform the data to match component expectations
    if (data) {
      rule.value = {
        id: data.rule_id || data.id,
        action: data.rule_details?.action || data.action,
        direction: data.rule_details?.direction || data.direction,
        created_at: data.rule_details?.created_at || data.created_at,
        canonical_hash: data.rule_details?.canonical_hash || data.canonical_hash,
        request_id: data.request?.id,
        endpoints: [
          ...(data.endpoints?.sources || []).map((ep) => ({
            ...ep,
            endpoint_type: 'source',
            network_cidr: ep.network_cidr || ep.cidr,
          })),
          ...(data.endpoints?.destinations || []).map((ep) => ({
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
</script>

