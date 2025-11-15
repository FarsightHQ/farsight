<template>
  <Card class="p-4">
    <h3 class="text-sm font-medium text-gray-900 mb-4">Analytics</h3>
    
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-16 bg-gray-200 rounded animate-pulse"></div>
    </div>

    <div v-else-if="error" class="text-center py-4">
      <p class="text-xs text-error-600">{{ error }}</p>
    </div>

    <div v-else-if="analytics" class="space-y-4">
      <!-- Summary Stats -->
      <div class="space-y-2">
        <div class="bg-gray-50 rounded-lg p-3">
          <div class="text-xs text-gray-600">Total Assets</div>
          <div class="text-xl font-bold text-gray-900 mt-0.5">{{ analytics.total_assets || 0 }}</div>
        </div>
        <div class="bg-success-50 rounded-lg p-3">
          <div class="text-xs text-success-600">Active Assets</div>
          <div class="text-xl font-bold text-success-700 mt-0.5">{{ analytics.active_assets || 0 }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-3">
          <div class="text-xs text-gray-600">Inactive Assets</div>
          <div class="text-xl font-bold text-gray-900 mt-0.5">{{ analytics.inactive_assets || 0 }}</div>
        </div>
      </div>

      <!-- Environment Distribution -->
      <div v-if="analytics.environments && Object.keys(analytics.environments).length > 0">
        <h4 class="text-xs font-medium text-gray-700 mb-2">By Environment</h4>
        <div class="space-y-1.5">
          <div
            v-for="[env, count] in Object.entries(analytics.environments)"
            :key="env"
            class="flex items-center justify-between text-xs"
          >
            <span class="text-gray-600 truncate">{{ env || 'Unknown' }}</span>
            <div class="flex items-center space-x-1.5">
              <div class="w-20 bg-gray-200 rounded-full h-1.5">
                <div
                  class="bg-primary-600 h-1.5 rounded-full"
                  :style="{
                    width: `${(count / analytics.total_assets) * 100}%`,
                  }"
                ></div>
              </div>
              <span class="text-xs font-medium text-gray-900 w-6 text-right">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- OS Distribution -->
      <div v-if="analytics.operating_systems && Object.keys(analytics.operating_systems).length > 0">
        <h4 class="text-xs font-medium text-gray-700 mb-2">By OS</h4>
        <div class="space-y-1.5">
          <div
            v-for="[os, count] in Object.entries(analytics.operating_systems)"
            :key="os"
            class="flex items-center justify-between text-xs"
          >
            <span class="text-gray-600 truncate">{{ os || 'Unknown' }}</span>
            <div class="flex items-center space-x-1.5">
              <div class="w-20 bg-gray-200 rounded-full h-1.5">
                <div
                  class="bg-primary-600 h-1.5 rounded-full"
                  :style="{
                    width: `${(count / analytics.total_assets) * 100}%`,
                  }"
                ></div>
              </div>
              <span class="text-xs font-medium text-gray-900 w-6 text-right">{{ count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- vCPU Stats -->
      <div v-if="analytics.average_vcpu !== null && analytics.average_vcpu !== undefined" class="pt-2 border-t border-gray-200">
        <h4 class="text-xs font-medium text-gray-700 mb-2">vCPU Statistics</h4>
        <div class="space-y-1.5">
          <div>
            <div class="text-xs text-gray-600">Average vCPU</div>
            <div class="text-sm font-semibold text-gray-900">{{ analytics.average_vcpu.toFixed(2) }}</div>
          </div>
          <div>
            <div class="text-xs text-gray-600">Total vCPU</div>
            <div class="text-sm font-semibold text-gray-900">{{ analytics.total_vcpu || 0 }}</div>
          </div>
        </div>
      </div>

      <!-- Last Updated -->
      <div class="text-xs text-gray-500 pt-2 border-t border-gray-200">
        Last updated: {{ formatDate(analytics.last_updated) }}
      </div>
    </div>
  </Card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Card from '@/components/ui/Card.vue'
import { assetsService } from '@/services/assets'

const analytics = ref(null)
const loading = ref(true)
const error = ref(null)

const fetchAnalytics = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await assetsService.getAnalytics()
    analytics.value = response.data || response
  } catch (err) {
    error.value = err.message || 'Failed to load analytics'
    console.error('Error fetching analytics:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  fetchAnalytics()
})
</script>

