<template>
  <div class="flex items-center gap-2 min-w-0 max-w-xs">
    <label class="sr-only" for="project-switcher">Project</label>
    <select
      id="project-switcher"
      v-model="selectedId"
      class="text-sm border border-theme-border-header rounded-lg px-2 py-1.5 bg-theme-header text-theme-text-header max-w-[14rem] truncate"
      @change="onChange"
    >
      <option value="" disabled>Select project…</option>
      <option v-for="p in projects" :key="p.id" :value="String(p.id)">
        {{ p.name }}
      </option>
    </select>
    <router-link
      to="/projects"
      class="text-xs text-theme-text-header/80 hover:underline whitespace-nowrap"
    >
      Manage
    </router-link>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectsService } from '../../services/projects'
import { getActiveProjectId, setActiveProjectId } from '../../utils/projectContext'

const projects = ref([])
const selectedId = ref(getActiveProjectId() || '')
const route = useRoute()
const router = useRouter()

async function load() {
  try {
    const res = await projectsService.list()
    const list = res.data?.projects || []
    projects.value = list
    const stored = getActiveProjectId()
    if (stored && list.some(p => String(p.id) === String(stored))) {
      selectedId.value = String(stored)
    } else if (list.length === 1) {
      selectedId.value = String(list[0].id)
      setActiveProjectId(list[0].id)
    } else if (list.length && !stored) {
      selectedId.value = ''
    }
  } catch (e) {
    console.error('Failed to load projects', e)
  }
}

function onChange() {
  setActiveProjectId(selectedId.value)
  if (route.meta.requiresProject) {
    router.replace({ path: route.path, query: route.query })
  }
}

onMounted(load)

watch(
  () => route.path,
  () => {
    const stored = getActiveProjectId()
    if (stored) selectedId.value = String(stored)
  }
)
</script>
