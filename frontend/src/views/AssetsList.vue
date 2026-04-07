<template>
  <PageFrame
    class="flex-1 min-h-0 flex flex-col"
    :scroll-body="false"
    :breadcrumb-items="breadcrumbItems"
    title="Project assets"
    subtitle="Manage and explore network assets linked to this project."
  >
      <template #actions>
        <Button variant="primary" size="sm" @click="goUpload">Upload CSV</Button>
      </template>

    <div class="flex flex-col flex-1 min-h-0 gap-3">
    <!-- View Controls Bar -->
    <div class="flex shrink-0 items-center justify-between">
      <div class="flex items-center space-x-2">
        <div class="text-sm text-theme-text-content">
          Showing {{ displayedAssets.length }} of {{ totalAssets }} assets
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <Button v-if="selectedAssets.length > 0" variant="outline" size="sm" @click="handleExport">
          Export Selected ({{ selectedAssets.length }})
        </Button>
        <Button variant="outline" size="sm" @click="handleExportAll"> Export All </Button>
      </div>
    </div>

    <!-- Three Column Layout -->
    <div class="flex-1 flex gap-4 overflow-hidden min-h-0">
      <!-- Left: Filters (Fixed Width) -->
      <div class="w-64 flex-shrink-0 overflow-y-auto">
        <AssetFilter :filters="filters" @update:filters="handleFilterUpdate" />
      </div>

      <!-- Middle: Table (Flexible) -->
      <div class="flex-1 overflow-hidden flex flex-col">
        <!-- Loading State -->
        <div v-if="loading" class="flex-1 overflow-y-auto">
          <div class="space-y-2">
            <div
              v-for="i in 10"
              :key="i"
              class="h-12 bg-theme-active/30 rounded animate-pulse"
            ></div>
          </div>
        </div>

        <!-- Empty State -->
        <Card
          v-else-if="!loading && assets.length === 0"
          class="flex-1 flex items-center justify-center"
        >
          <div class="text-center py-12">
            <svg
              class="mx-auto h-12 w-12 text-theme-text-muted"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-theme-text-content">No assets found</h3>
            <p class="mt-1 text-sm text-theme-text-muted">
              {{
                hasActiveFilters
                  ? 'Try adjusting your filters.'
                  : 'Get started by uploading a CSV file.'
              }}
            </p>
            <div class="mt-6">
              <Button variant="primary" @click="goUpload">
                Upload CSV
              </Button>
            </div>
          </div>
        </Card>

        <!-- Assets Table View -->
        <div v-else class="flex-1 overflow-y-auto">
          <AssetTable
            :assets="displayedAssets"
            :loading="loading"
            :selected-assets="selectedAssets"
            :sort-key="sortKey"
            :sort-direction="sortDirection"
            @view-asset="handleViewAsset"
            @select-asset="handleSelectAsset"
            @select-all="handleSelectAll"
            @sort="handleSort"
          />
        </div>

        <!-- Pagination -->
        <div v-if="!loading && assets.length > 0" class="mt-6 flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="text-sm text-theme-text-content">Show</span>
            <select
              v-model="pageSize"
              class="input text-sm"
              style="width: auto"
              @change="handlePageSizeChange"
            >
              <option :value="10">10</option>
              <option :value="25">25</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <span class="text-sm text-theme-text-content">per page</span>
          </div>
          <div class="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              :disabled="currentPage === 1"
              @click="goToPage(currentPage - 1)"
            >
              Previous
            </Button>
            <span class="text-sm text-theme-text-content">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <Button
              variant="outline"
              size="sm"
              :disabled="currentPage === totalPages"
              @click="goToPage(currentPage + 1)"
            >
              Next
            </Button>
          </div>
        </div>
      </div>

      <!-- Right: Analytics (Fixed Width) -->
      <div class="w-80 flex-shrink-0 overflow-y-auto">
        <AssetAnalytics />
      </div>
    </div>
    </div>
  </PageFrame>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { projectPath } from '@/utils/projectRoutes'
import PageFrame from '@/components/layout/PageFrame.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'
import { assetsService } from '@/services/assets'
import { useToast } from '@/composables/useToast'
import { exportRulesToCSV, exportRulesToJSON } from '@/services/export'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import AssetFilter from '@/components/assets/AssetFilter.vue'
import AssetTable from '@/components/assets/AssetTable.vue'
import AssetAnalytics from '@/components/assets/AssetAnalytics.vue'

const router = useRouter()
const route = useRoute()
const { success, error } = useToast()
const { breadcrumbItems } = usePageBreadcrumbs()

const goUpload = () => {
  router.push(projectPath('/assets/upload', route.params.projectId))
}

const assets = ref([])
const loading = ref(false)
const selectedAssets = ref([])
const sortKey = ref('ip_address')
const sortDirection = ref('asc')
const currentPage = ref(1)
const pageSize = ref(100)
const totalAssets = ref(0)

const filters = reactive({
  ip_address: '',
  ip_range: '',
  segment: '',
  vlan: '',
  os_name: '',
  environment: '',
  hostname: '',
  is_active: true,
})

const hasActiveFilters = computed(() => {
  return (
    filters.ip_address !== '' ||
    filters.ip_range !== '' ||
    filters.segment !== '' ||
    filters.vlan !== '' ||
    filters.os_name !== '' ||
    filters.environment !== '' ||
    filters.hostname !== '' ||
    filters.is_active !== true
  )
})

const displayedAssets = computed(() => {
  let result = [...assets.value]

  // Client-side sorting
  if (sortKey.value) {
    result.sort((a, b) => {
      const aVal = a[sortKey.value] || ''
      const bVal = b[sortKey.value] || ''
      const comparison = aVal.toString().localeCompare(bVal.toString())
      return sortDirection.value === 'asc' ? comparison : -comparison
    })
  }

  return result
})

const totalPages = computed(() => {
  return Math.ceil(totalAssets.value / pageSize.value)
})

const fetchAssets = async () => {
  try {
    loading.value = true
    const offset = (currentPage.value - 1) * pageSize.value

    // Build filter params
    const filterParams = {
      ...filters,
      limit: pageSize.value,
      offset,
    }

    const response = await assetsService.searchAssets(filterParams)

    // Handle response structure
    const responseData = response.data || response
    assets.value = responseData.data || responseData
    totalAssets.value = responseData.pagination?.total || responseData.total || assets.value.length
  } catch (err) {
    error(err.message || 'Failed to load assets')
    console.error('Error fetching assets:', err)
  } finally {
    loading.value = false
  }
}

const handleFilterUpdate = newFilters => {
  Object.assign(filters, newFilters)
  currentPage.value = 1
  fetchAssets()
}

const handleViewAsset = asset => {
  router.push(
    projectPath(`/assets/${encodeURIComponent(asset.ip_address)}`, route.params.projectId)
  )
}

const handleSelectAsset = (assetId, checked) => {
  if (checked) {
    if (!selectedAssets.value.includes(assetId)) {
      selectedAssets.value.push(assetId)
    }
  } else {
    selectedAssets.value = selectedAssets.value.filter(id => id !== assetId)
  }
}

const handleSelectAll = checked => {
  if (checked) {
    selectedAssets.value = displayedAssets.value.map(asset => asset.id)
  } else {
    selectedAssets.value = []
  }
}

const handleSort = key => {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
}

const handleExport = () => {
  const selectedAssetsData = displayedAssets.value.filter(asset =>
    selectedAssets.value.includes(asset.id)
  )
  exportAssetsToCSV(selectedAssetsData, 'selected-assets')
}

const handleExportAll = () => {
  exportAssetsToCSV(displayedAssets.value, 'all-assets')
}

const exportAssetsToCSV = (assetsData, filename) => {
  if (assetsData.length === 0) {
    error('No assets to export')
    return
  }

  const headers = [
    'IP Address',
    'Segment',
    'VLAN',
    'OS',
    'Hostname',
    'Environment',
    'Status',
    'Created',
  ]
  const rows = assetsData.map(asset => [
    asset.ip_address,
    asset.segment || '',
    asset.vlan || '',
    asset.os_name || '',
    asset.hostname || '',
    asset.environment || '',
    asset.is_active ? 'Active' : 'Inactive',
    asset.created_at || '',
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
  ].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${filename}-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
  success(`Exported ${assetsData.length} assets to CSV`)
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  fetchAssets()
}

const goToPage = page => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchAssets()
  }
}

// Watch for filter changes
watch(
  () => filters,
  () => {
    currentPage.value = 1
    fetchAssets()
  },
  { deep: true }
)

onMounted(() => {
  fetchAssets()
})
</script>
