<template>
  <div class="flex flex-col flex-1 min-h-0 min-w-0">
    <PageFrame
      class="flex-1 min-h-0 flex flex-col"
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
        <Button variant="outline" @click="$router.push({ name: 'RegistryAssets' })">
          Back to registry
        </Button>
      </template>

      <CardSkeleton v-if="loading" />

      <ErrorCallout v-else-if="err" variant="card" :message="err">
        <Button variant="outline" @click="$router.push({ name: 'RegistryAssets' })">
          Back to registry
        </Button>
      </ErrorCallout>

      <div v-else-if="asset" class="space-y-4">
        <AssetDetailPanel :asset="asset" />

        <Card class="p-4">
          <h2 class="text-lg font-semibold text-theme-text-content mb-3">Linked projects</h2>
          <p v-if="projectsLoading" class="text-sm text-theme-text-muted">Loading…</p>
          <p v-else-if="projectsError" class="text-sm text-error-600">{{ projectsError }}</p>
          <ul v-else-if="linkedProjects.length" class="divide-y divide-theme-border-default">
            <li
              v-for="p in linkedProjects"
              :key="p.id"
              class="py-2 flex items-center justify-between"
            >
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
    </PageFrame>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { registryAssetsService } from '@/services/registryAssets'
import PageFrame from '@/components/layout/PageFrame.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import CardSkeleton from '@/components/ui/CardSkeleton.vue'
import ErrorCallout from '@/components/ui/ErrorCallout.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import AssetDetailPanel from '@/components/assets/AssetDetailPanel.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

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

const { breadcrumbItems } = usePageBreadcrumbs({
  registryIp: ipAddress,
})

const pageTitle = computed(() => asset.value?.ip_address || ipAddress.value || 'Asset')

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
