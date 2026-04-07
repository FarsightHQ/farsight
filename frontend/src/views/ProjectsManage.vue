<template>
  <div class="space-y-6">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-theme-text-content">All projects</h1>
        <p class="text-sm text-theme-text-muted mt-1">
          Workspaces you can access. Open one to work on requests, rules, and assets.
        </p>
      </div>
      <router-link :to="createLink">
        <Button variant="primary">New project</Button>
      </router-link>
    </div>

    <div v-if="redirect" class="text-sm">
      <router-link :to="redirect" class="text-primary-600 hover:underline">
        Continue to requested page
      </router-link>
    </div>

    <Card>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-theme-border-default">
          <thead class="bg-theme-content">
            <tr>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
              >
                Name
              </th>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
              >
                Slug
              </th>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
              >
                Description
              </th>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
              >
                Access
              </th>
              <th
                class="px-4 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
              >
                Created
              </th>
              <th
                class="px-4 py-3 text-right text-xs font-medium text-theme-text-muted uppercase tracking-wider"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody v-if="loading" class="bg-theme-card divide-y divide-theme-border-default">
            <tr v-for="i in 5" :key="i">
              <td v-for="j in 6" :key="j" class="px-4 py-3">
                <div class="h-4 bg-theme-active/30 rounded animate-pulse"></div>
              </td>
            </tr>
          </tbody>
          <tbody v-else-if="!projects.length" class="bg-theme-card">
            <tr>
              <td colspan="6" class="px-4 py-12 text-center text-sm text-theme-text-muted">
                No projects yet.
                <router-link :to="createLink" class="text-primary-600 hover:underline ml-1">
                  Create one
                </router-link>
              </td>
            </tr>
          </tbody>
          <tbody v-else class="bg-theme-card divide-y divide-theme-border-default">
            <tr
              v-for="p in projects"
              :key="p.id"
              class="hover:bg-theme-hover transition-colors"
            >
              <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-theme-text-content">
                {{ p.name }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-theme-text-muted font-mono">
                {{ p.slug }}
              </td>
              <td
                class="px-4 py-3 text-sm text-theme-text-content max-w-xs truncate"
                :title="p.description || ''"
              >
                {{ p.description || '—' }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm">
                <Badge v-if="p.legacy_unrestricted" variant="warning">Legacy open</Badge>
                <span v-else class="text-theme-text-muted">Member</span>
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-sm text-theme-text-muted">
                {{ formatDate(p.created_at) }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap text-right text-sm">
                <Button variant="outline" size="sm" @click="openProject(p.id)"> Open </Button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectsService } from '@/services/projects'
import { setActiveProjectId } from '@/utils/projectContext'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'

const projects = ref([])
const loading = ref(true)
const route = useRoute()
const router = useRouter()

const redirect = computed(() => {
  const r = route.query.redirect
  return typeof r === 'string' && r.startsWith('/') ? r : ''
})

const createLink = computed(() => {
  if (redirect.value) {
    return { name: 'ProjectCreate', query: { redirect: redirect.value } }
  }
  return { name: 'ProjectCreate' }
})

function formatDate(s) {
  if (!s) return '—'
  try {
    return new Date(s).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return '—'
  }
}

async function load() {
  loading.value = true
  try {
    const res = await projectsService.list()
    projects.value = res.data?.projects || []
  } catch {
    projects.value = []
  } finally {
    loading.value = false
  }
}

function openProject(id) {
  setActiveProjectId(id)
  if (redirect.value) {
    router.push(redirect.value)
  } else {
    router.push({ name: 'ProjectOverview', params: { projectId: id } })
  }
}

onMounted(load)
</script>
