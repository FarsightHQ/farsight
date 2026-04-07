<template>
  <div class="max-w-2xl mx-auto p-6 space-y-6">
    <h1 class="text-2xl font-semibold">Projects</h1>
    <p class="text-sm text-theme-text-muted">
      Select a workspace for FAR requests and assets. The default migrated project is open to all
      signed-in users until you turn off legacy access in the database.
    </p>

    <form class="space-y-3 border border-theme-border rounded-lg p-4" @submit.prevent="onCreate">
      <h2 class="font-medium">Create project</h2>
      <div>
        <label class="block text-sm mb-1">Name</label>
        <input
          v-model="newName"
          type="text"
          required
          class="w-full border rounded px-3 py-2 text-sm"
          placeholder="My workspace"
        />
      </div>
      <div>
        <label class="block text-sm mb-1">Description (optional)</label>
        <input
          v-model="newDesc"
          type="text"
          class="w-full border rounded px-3 py-2 text-sm"
        />
      </div>
      <button
        type="submit"
        class="px-4 py-2 text-sm font-medium rounded-lg bg-theme-nav-selected text-white"
        :disabled="creating"
      >
        {{ creating ? 'Creating…' : 'Create' }}
      </button>
      <p v-if="createError" class="text-sm text-red-600">{{ createError }}</p>
    </form>

    <div>
      <h2 class="font-medium mb-2">Your projects</h2>
      <ul v-if="projects.length" class="space-y-2">
        <li
          v-for="p in projects"
          :key="p.id"
          class="flex items-center justify-between border border-theme-border rounded-lg px-3 py-2"
        >
          <div>
            <div class="font-medium">{{ p.name }}</div>
            <div class="text-xs text-theme-text-muted">slug: {{ p.slug }}</div>
          </div>
          <button
            type="button"
            class="text-sm px-3 py-1 rounded bg-theme-sidebar-hover"
            @click="select(p.id)"
          >
            Use
          </button>
        </li>
      </ul>
      <p v-else class="text-sm text-theme-text-muted">No projects yet.</p>
    </div>

    <div v-if="redirect" class="text-sm">
      <router-link :to="redirect" class="text-blue-600 underline">Continue to requested page</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectsService } from '../services/projects'
import { setActiveProjectId } from '../utils/projectContext'

const projects = ref([])
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

async function load() {
  const res = await projectsService.list()
  projects.value = res.data?.projects || []
}

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
      newName.value = ''
      newDesc.value = ''
      await load()
      if (redirect.value) {
        router.push(redirect.value)
      }
    }
  } catch (e) {
    createError.value = e.message || 'Create failed'
  } finally {
    creating.value = false
  }
}

function select(id) {
  setActiveProjectId(id)
  if (redirect.value) {
    router.push(redirect.value)
  } else {
    router.push('/')
  }
}

onMounted(load)
</script>
