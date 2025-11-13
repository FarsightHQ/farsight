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
    <div v-else-if="request">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-3xl font-bold mb-2">{{ request.title }}</h1>
          <div class="flex items-center space-x-4 text-sm text-gray-600">
            <span>ID: {{ request.id }}</span>
            <StatusBadge :status="request.status" />
            <span v-if="request.external_id">External ID: {{ request.external_id }}</span>
          </div>
        </div>
        <Button variant="outline" @click="$router.push('/requests')">
          Back to List
        </Button>
      </div>

      <!-- Quick Stats -->
      <RequestStats :stats="stats" class="mb-6" />

      <!-- Action Buttons -->
      <Card class="mb-6">
        <div class="flex items-center space-x-4">
          <Button
            variant="primary"
            :disabled="processing || request.status !== 'submitted'"
            @click="handleIngest"
          >
            <Spinner v-if="processing" size="sm" class="mr-2" />
            Process CSV
          </Button>
          <Button
            variant="secondary"
            :disabled="processing || request.status !== 'ingested'"
            @click="handleComputeFacts"
          >
            <Spinner v-if="processing" size="sm" class="mr-2" />
            Compute Facts
          </Button>
          <Button
            variant="secondary"
            :disabled="processing || request.status !== 'ingested'"
            @click="handleComputeHybrid"
          >
            <Spinner v-if="processing" size="sm" class="mr-2" />
            Compute Hybrid Facts
          </Button>
        </div>
      </Card>

      <!-- Request Metadata -->
      <Card class="mb-6">
        <h2 class="text-lg font-semibold mb-4">Request Information</h2>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="font-medium text-gray-600">Status:</span>
            <span class="ml-2">
              <StatusBadge :status="request.status" />
            </span>
          </div>
          <div>
            <span class="font-medium text-gray-600">Created:</span>
            <span class="ml-2">{{ formatDate(request.created_at) }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-600">File Name:</span>
            <span class="ml-2">{{ request.source_filename }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-600">File Size:</span>
            <span class="ml-2">{{ formatFileSize(request.source_size_bytes) }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-600">SHA256:</span>
            <span class="ml-2 font-mono text-xs">{{ request.source_sha256 }}</span>
          </div>
          <div>
            <span class="font-medium text-gray-600">Created By:</span>
            <span class="ml-2">{{ request.created_by || 'system' }}</span>
          </div>
        </div>
      </Card>

      <!-- Tabs -->
      <Card>
        <RequestTabs
          :tabs="tabs"
          :active-tab="activeTab"
          @update:activeTab="activeTab = $event"
        >
          <template #overview>
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Overview</h3>
              <p class="text-gray-600">
                Request overview and basic information will be displayed here.
              </p>
            </div>
          </template>

          <template #rules>
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Rules</h3>
              <p class="text-gray-600">
                Rules list will be implemented in Phase 4.
              </p>
            </div>
          </template>

          <template #analysis>
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Analysis</h3>
              <p class="text-gray-600">
                Analysis and reporting will be implemented in Phase 5.
              </p>
            </div>
          </template>

          <template #visualization>
            <div class="space-y-4">
              <h3 class="text-lg font-semibold">Visualization</h3>
              <p class="text-gray-600">
                Network visualization will be implemented in Phase 6.
              </p>
            </div>
          </template>
        </RequestTabs>
      </Card>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Spinner from '@/components/ui/Spinner.vue'
import StatusBadge from '@/components/requests/StatusBadge.vue'
import RequestStats from '@/components/requests/RequestStats.vue'
import RequestTabs from '@/components/requests/RequestTabs.vue'

const route = useRoute()
const router = useRouter()
const { success, error } = useToast()

const loading = ref(false)
const processing = ref(false)
const request = ref(null)
const activeTab = ref('overview')

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'rules', label: 'Rules' },
  { key: 'analysis', label: 'Analysis' },
  { key: 'visualization', label: 'Visualization' },
]

const stats = computed(() => ({
  totalRules: 0, // Will be populated from API in Phase 4
  totalEndpoints: 0,
  totalServices: 0,
}))

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

const handleIngest = async () => {
  processing.value = true
  try {
    await requestsService.ingest(route.params.id)
    success('CSV processing started successfully')
    await fetchRequest() // Refresh request data
  } catch (err) {
    error(err.message || 'Failed to process CSV')
  } finally {
    processing.value = false
  }
}

const handleComputeFacts = async () => {
  processing.value = true
  try {
    await requestsService.computeFacts(route.params.id)
    success('Facts computation started successfully')
    await fetchRequest()
  } catch (err) {
    error(err.message || 'Failed to compute facts')
  } finally {
    processing.value = false
  }
}

const handleComputeHybrid = async () => {
  processing.value = true
  try {
    await requestsService.computeHybridFacts(route.params.id)
    success('Hybrid facts computation started successfully')
    await fetchRequest()
  } catch (err) {
    error(err.message || 'Failed to compute hybrid facts')
  } finally {
    processing.value = false
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

onMounted(() => {
  fetchRequest()
})
</script>
