<template>
  <PageFrame
    class="flex-1 min-h-0 flex flex-col"
    :breadcrumb-items="breadcrumbItems"
    title="Create project"
      subtitle="Add a workspace for FAR requests and project-scoped assets."
    >
      <template #actions>
        <router-link :to="backToList">
          <Button type="button" variant="outline">Cancel</Button>
        </router-link>
      </template>

      <div class="max-w-xl">
      <Card class="p-6">
      <form class="space-y-4" @submit.prevent="onCreate">
        <div>
          <label class="block text-sm font-medium text-theme-text-content mb-1">Name</label>
          <input
            v-model="newName"
            type="text"
            required
            class="w-full border border-theme-border rounded-lg px-3 py-2 text-sm"
            placeholder="My workspace"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-theme-text-content mb-1"
            >Description (optional)</label
          >
          <textarea
            v-model="newDesc"
            rows="3"
            class="w-full border border-theme-border rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div class="flex flex-wrap items-center gap-3 pt-2">
          <Button type="submit" variant="primary" :disabled="creating">
            {{ creating ? 'Creating…' : 'Create project' }}
          </Button>
        </div>
        <p v-if="createError" class="text-sm text-error-600">{{ createError }}</p>
      </form>
    </Card>

      <div v-if="redirect" class="text-sm mt-6">
        <router-link :to="redirect" class="text-primary-600 hover:underline">
          Continue to requested page
        </router-link>
      </div>
      </div>
    </PageFrame>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectsService } from '@/services/projects'
import { setActiveProjectId } from '@/utils/projectContext'
import PageFrame from '@/components/layout/PageFrame.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const { breadcrumbItems } = usePageBreadcrumbs()

const newName = ref('')
const newDesc = ref('')
const creating = ref(false)
const createError = ref('')
const route = useRoute()
const router = useRouter()

const redirect = computed(() => {
  const r = route.query.redirect
  return typeof r === 'string' && r.startsWith('/') ? r : ''
})

const backToList = computed(() => {
  if (redirect.value) {
    return { name: 'Projects', query: { redirect: redirect.value } }
  }
  return { name: 'Projects' }
})

async function onCreate() {
  createError.value = ''
  creating.value = true
  try {
    const res = await projectsService.create({
      name: newName.value.trim(),
      description: newDesc.value.trim() || undefined,
    })
    const p = res.data
    if (p?.id) {
      setActiveProjectId(p.id)
      if (redirect.value) {
        router.push(redirect.value)
      } else {
        router.push({ name: 'ProjectOverview', params: { projectId: p.id } })
      }
    }
  } catch (e) {
    createError.value = e.message || 'Create failed'
  } finally {
    creating.value = false
  }
}
</script>
