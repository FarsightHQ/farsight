<template>
  <div class="space-y-4">
    <PageFrame
      :breadcrumb-items="breadcrumbItems"
      :title="pageTitle"
    >
      <template v-if="asset" #subtitle>
        <div class="flex flex-wrap items-center gap-2 text-theme-text-muted">
          <StatusBadge
            :status="asset.is_active ? 'success' : 'error'"
            :label="asset.is_active ? 'Active' : 'Inactive'"
          />
          <span v-if="asset.hostname">Hostname: {{ asset.hostname }}</span>
          <span>Created: {{ formatDate(asset.created_at) }}</span>
        </div>
      </template>

      <template #actions>
        <Button variant="outline" @click="goAssetsList">Back to assets</Button>
      </template>

      <div v-if="loading" class="space-y-6">
        <Card class="p-6 animate-pulse">
          <div class="h-8 bg-theme-active/30 rounded w-1/3 mb-4"></div>
          <div class="h-4 bg-theme-active/30 rounded w-1/2"></div>
        </Card>
      </div>

      <Card v-else-if="error" class="p-6">
        <div class="text-center py-12">
          <p class="text-error-600 mb-4">{{ error }}</p>
          <Button variant="outline" @click="goAssetsList">Back to assets</Button>
        </div>
      </Card>

      <div v-else-if="asset" class="space-y-4">
        <AssetDetailPanel :asset="asset" />
        <AssetCoverage
          :source-rules="sourceRules"
          :destination-rules="destinationRules"
          :loading="rulesLoading"
          :error="rulesError"
          @view-rule="handleViewRule"
        />
      </div>
    </PageFrame>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectPath } from '@/utils/projectRoutes'
import { assetsService } from '@/services/assets'
import PageFrame from '@/components/layout/PageFrame.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import StatusBadge from '@/components/requests/StatusBadge.vue'
import AssetDetailPanel from '@/components/assets/AssetDetailPanel.vue'
import AssetCoverage from '@/components/assets/AssetCoverage.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const route = useRoute()
const router = useRouter()
const ipAddress = computed(() => {
  return route.params.id ? decodeURIComponent(route.params.id) : ''
})

const { breadcrumbItems } = usePageBreadcrumbs({
  assetLabel: ipAddress,
})

const asset = ref(null)
const loading = ref(true)
const error = ref(null)

const pageTitle = computed(() => asset.value?.ip_address || ipAddress.value || 'Asset')

const goAssetsList = () => {
  router.push(projectPath('/assets', route.params.projectId))
}
const sourceRules = ref([])
const destinationRules = ref([])
const rulesLoading = ref(false)
const rulesError = ref(null)

const fetchAsset = async () => {
  if (!ipAddress.value) {
    error.value = 'IP address is required'
    loading.value = false
    return
  }

  try {
    loading.value = true
    error.value = null
    const response = await assetsService.getAssetByIp(ipAddress.value)
    asset.value = response.data || response
  } catch (err) {
    error.value = err.message || 'Failed to load asset'
    console.error('Error fetching asset:', err)
  } finally {
    loading.value = false
  }
}

const fetchRelatedRules = async () => {
  if (!asset.value) return

  try {
    rulesLoading.value = true
    rulesError.value = null
    sourceRules.value = []
    destinationRules.value = []
  } catch (err) {
    rulesError.value = err.message || 'Failed to load related rules'
    console.error('Error fetching related rules:', err)
  } finally {
    rulesLoading.value = false
  }
}

const handleViewRule = rule => {
  router.push(projectPath(`/rules/${rule.id}`, route.params.projectId))
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

onMounted(async () => {
  await fetchAsset()
  if (asset.value) {
    await fetchRelatedRules()
  }
})
</script>
