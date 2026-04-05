<template>
  <div class="space-y-4">
    <!-- Breadcrumb Navigation -->
    <nav class="flex items-center space-x-2 text-sm text-gray-600">
      <router-link to="/assets" class="hover:text-primary-600">Assets</router-link>
      <ChevronRightIcon class="h-4 w-4" />
      <span class="text-gray-900 font-medium">{{ ipAddress }}</span>
    </nav>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <Card class="p-6 animate-pulse">
        <div class="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div class="h-4 bg-gray-200 rounded w-1/2"></div>
      </Card>
    </div>

    <!-- Error State -->
    <Card v-else-if="error" class="p-6">
      <div class="text-center py-12">
        <p class="text-error-600 mb-4">{{ error }}</p>
        <Button variant="outline" @click="$router.push('/assets')"> Back to Assets </Button>
      </div>
    </Card>

    <!-- Asset Details -->
    <div v-else-if="asset" class="space-y-4">
      <!-- Header -->
      <Card class="p-4">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ asset.ip_address }}</h1>
            <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600">
              <StatusBadge
                :status="asset.is_active ? 'success' : 'error'"
                :label="asset.is_active ? 'Active' : 'Inactive'"
              />
              <span v-if="asset.hostname">Hostname: {{ asset.hostname }}</span>
              <span>Created: {{ formatDate(asset.created_at) }}</span>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <Button variant="outline" @click="$router.push('/assets')"> Back to Assets </Button>
          </div>
        </div>
      </Card>

      <!-- Asset Information -->
      <AssetDetailPanel :asset="asset" />

      <!-- Rule Coverage -->
      <AssetCoverage
        :source-rules="sourceRules"
        :destination-rules="destinationRules"
        :loading="rulesLoading"
        :error="rulesError"
        @view-rule="handleViewRule"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronRightIcon } from '@heroicons/vue/24/outline'
import { assetsService } from '@/services/assets'
import { rulesService } from '@/services/rules'
import { useToast } from '@/composables/useToast'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import StatusBadge from '@/components/requests/StatusBadge.vue'
import AssetDetailPanel from '@/components/assets/AssetDetailPanel.vue'
import AssetCoverage from '@/components/assets/AssetCoverage.vue'

const route = useRoute()
const router = useRouter()
const { success, error: showError } = useToast()

const asset = ref(null)
const loading = ref(true)
const error = ref(null)
const sourceRules = ref([])
const destinationRules = ref([])
const rulesLoading = ref(false)
const rulesError = ref(null)

const ipAddress = computed(() => {
  return route.params.id ? decodeURIComponent(route.params.id) : ''
})

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

    // Extract IP from asset IP address
    const ip = asset.value.ip_address.split('/')[0] // Remove CIDR if present

    // Search for rules where this IP is in source or destination
    // Note: This is a simplified approach - in production, you might want a dedicated endpoint
    // For now, we'll search through all requests and filter client-side
    // This is not ideal for large datasets, but works for MVP

    // TODO: Implement proper rule search by IP endpoint or client-side filtering
    // For now, we'll leave this as a placeholder
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
  router.push(`/rules/${rule.id}`)
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
