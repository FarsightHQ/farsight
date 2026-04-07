<template>
  <div class="space-y-4">
    <nav class="flex items-center space-x-2 text-sm text-theme-text-muted">
      <router-link :to="{ name: 'RegistryAssets' }" class="hover:text-primary-600"
        >Global assets</router-link
      >
      <ChevronRightIcon class="h-4 w-4" />
      <span class="text-theme-text-content font-medium">{{ ipAddress }}</span>
    </nav>

    <div v-if="loading" class="space-y-6">
      <Card class="p-6 animate-pulse">
        <div class="h-8 bg-theme-active/30 rounded w-1/3 mb-4"></div>
        <div class="h-4 bg-theme-active/30 rounded w-1/2"></div>
      </Card>
    </div>

    <Card v-else-if="err" class="p-6">
      <p class="text-error-600 mb-4">{{ err }}</p>
      <Button variant="outline" @click="$router.push({ name: 'RegistryAssets' })">
        Back to registry
      </Button>
    </Card>

    <div v-else-if="asset" class="space-y-4">
      <Card class="p-4">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h1 class="text-2xl font-bold text-theme-text-content">{{ asset.ip_address }}</h1>
            <div class="flex items-center space-x-4 mt-2 text-sm text-theme-text-muted">
              <StatusBadge
                :status="asset.is_active ? 'success' : 'error'"
                :label="asset.is_active ? 'Active' : 'Inactive'"
              />
              <span v-if="asset.hostname">Hostname: {{ asset.hostname }}</span>
              <span>Created: {{ formatDate(asset.created_at) }}</span>
            </div>
          </div>
          <Button variant="outline" @click="$router.push({ name: 'RegistryAssets' })">
            Back
          </Button>
        </div>
      </Card>

      <AssetDetailPanel :asset="asset" />

      <Card class="p-4">
        <h2 class="text-lg font-semibold text-theme-text-content mb-3">Linked projects</h2>
        <p v-if="projectsLoading" class="text-sm text-theme-text-muted">Loading…</p>
        <p v-else-if="projectsError" class="text-sm text-error-600">{{ projectsError }}</p>
        <ul v-else-if="linkedProjects.length" class="divide-y divide-theme-border-default">
          <li v-for="p in linkedProjects" :key="p.id" class="py-2 flex items-center justify-between">
            <span class="font-medium text-theme-text-content">{{ p.name }}</span>
            <router-link
              :to="{ name: 'ProjectAssets', params: { projectId: p.id } }"
              class="text-sm text-primary-600 hover:underline"
            >
              Project assets
            </router-link>
          </li>
        </ul>
        <p v-else class="text-sm text-theme-text-muted">
          This asset is not linked to any project you can access.
        </p>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronRightIcon } from '@heroicons/vue/24/outline'
import { registryAssetsService } from '@/services/registryAssets'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import StatusBadge from '@/components/requests/StatusBadge.vue'
import AssetDetailPanel from '@/components/assets/AssetDetailPanel.vue'

const route = useRoute()
const asset = ref(null)
const loading = ref(true)
const err = ref(null)
const linkedProjects = ref([])
const projectsLoading = ref(false)
const projectsError = ref(null)

const ipAddress = computed(() => {
  const raw = route.params.ip
  if (raw == null || raw === '') return ''
  const s = Array.isArray(raw) ? raw.join('/') : String(raw)
  try {
    return decodeURIComponent(s)
  } catch {
    return s
  }
})

function formatDate(s) {
  if (!s) return 'N/A'
  return new Date(s).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

async function load() {
  if (!ipAddress.value) {
    err.value = 'IP address is required'
    loading.value = false
    return
  }
  loading.value = true
  err.value = null
  asset.value = null
  try {
    const res = await registryAssetsService.getByIp(ipAddress.value)
    asset.value = res.data ?? res
  } catch (e) {
    err.value = e.response?.data?.detail || e.message || 'Failed to load asset'
  } finally {
    loading.value = false
  }

  projectsLoading.value = true
  projectsError.value = null
  linkedProjects.value = []
  try {
    const res = await registryAssetsService.linkedProjects(ipAddress.value)
    const payload = res.data ?? res
    linkedProjects.value = payload?.projects ?? []
  } catch (e) {
    projectsError.value = e.response?.data?.detail || e.message || 'Failed to load linked projects'
  } finally {
    projectsLoading.value = false
  }
}

onMounted(load)
watch(() => route.params.ip, load)
</script>
