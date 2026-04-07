<template>
  <div class="flex flex-col min-h-0" style="height: 100%">
    <PageFrame
      :breadcrumb-items="breadcrumbItems"
      title="Global assets"
    >
      <template #subtitle>
        <span class="text-theme-text-muted">
          Organization-wide registry. Upload CSVs from
          <router-link :to="uploadHintLink" class="text-primary-600 hover:underline"
            >project assets</router-link
          >.
        </span>
      </template>
      <template #actions>
        <router-link :to="uploadHintLink" custom v-slot="{ navigate }">
          <Button variant="outline" size="sm" @click="navigate">Upload in project</Button>
        </router-link>
      </template>

    <div class="flex-1 flex gap-4 overflow-hidden min-h-0 min-w-0">
      <div class="w-64 flex-shrink-0 overflow-y-auto">
        <AssetFilter :filters="filters" @update:filters="handleFilterUpdate" />
      </div>
      <div class="flex-1 overflow-hidden flex flex-col">
        <div v-if="loading" class="flex-1 overflow-y-auto">
          <div class="space-y-2">
            <div
              v-for="i in 10"
              :key="i"
              class="h-12 bg-theme-active/30 rounded animate-pulse"
            ></div>
          </div>
        </div>
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
      </div>
    </div>
    </PageFrame>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageFrame from '@/components/layout/PageFrame.vue'
import Button from '@/components/ui/Button.vue'
import AssetFilter from '@/components/assets/AssetFilter.vue'
import AssetTable from '@/components/assets/AssetTable.vue'
import { registryAssetsService } from '@/services/registryAssets'
import { projectPath } from '@/utils/projectRoutes'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const router = useRouter()
const { breadcrumbItems } = usePageBreadcrumbs()
const assets = ref([])
const loading = ref(false)
const selectedAssets = ref([])
const sortKey = ref('ip_address')
const sortDirection = ref('asc')
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

const uploadHintLink = computed(() => projectPath('/assets/upload'))

const displayedAssets = computed(() => {
  const list = [...assets.value]
  if (!sortKey.value) return list
  return list.sort((a, b) => {
    const aVal = a[sortKey.value] || ''
    const bVal = b[sortKey.value] || ''
    const c = aVal.toString().localeCompare(bVal.toString())
    return sortDirection.value === 'asc' ? c : -c
  })
})

async function fetchAssets() {
  loading.value = true
  try {
    const filterParams = {
      ...filters,
      limit: 500,
      offset: 0,
    }
    const response = await registryAssetsService.search(filterParams)
    assets.value = response.data ?? []
    totalAssets.value =
      response.pagination?.total ?? response.total ?? assets.value.length
  } catch (e) {
    console.error(e)
    assets.value = []
  } finally {
    loading.value = false
  }
}

function handleFilterUpdate(newFilters) {
  Object.assign(filters, newFilters)
  fetchAssets()
}

function handleViewAsset(asset) {
  router.push({
    name: 'RegistryAssetDetail',
    params: { ip: asset.ip_address },
  })
}

function handleSelectAsset(assetId, checked) {
  if (checked) {
    if (!selectedAssets.value.includes(assetId)) selectedAssets.value.push(assetId)
  } else {
    selectedAssets.value = selectedAssets.value.filter(id => id !== assetId)
  }
}

function handleSelectAll(checked) {
  selectedAssets.value = checked ? displayedAssets.value.map(a => a.id) : []
}

function handleSort(key) {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
}

onMounted(fetchAssets)
</script>
