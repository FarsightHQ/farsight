<template>
  <div class="relative min-w-0" data-project-switcher>
    <button
      type="button"
      :class="[
        'w-full flex items-center gap-2 rounded-lg border border-theme-border-sidebar px-2 py-2 text-left text-sm',
        'bg-theme-sidebar hover:bg-theme-sidebar-hover text-theme-text-sidebar',
        collapsed ? 'justify-center px-1' : '',
      ]"
      :title="collapsed ? currentLabel : 'Switch project'"
      aria-haspopup="listbox"
      :aria-expanded="open"
      @click="open = !open"
    >
      <FolderIcon class="h-5 w-5 shrink-0 text-theme-text-sidebar" />
      <span
        v-if="!collapsed"
        class="truncate flex-1 min-w-0 font-medium"
      >
        {{ currentLabel }}
      </span>
      <ChevronDownIcon
        v-if="!collapsed"
        class="h-4 w-4 shrink-0 text-theme-text-sidebar/80"
      />
    </button>

    <div
      v-if="open"
      class="absolute left-0 right-0 z-50 mt-1 max-h-64 overflow-y-auto rounded-lg border border-theme-border-sidebar bg-theme-sidebar py-1 shadow-lg"
      role="listbox"
    >
      <button
        v-for="p in projects"
        :key="p.id"
        type="button"
        role="option"
        :class="[
          'w-full text-left px-3 py-2 text-sm truncate hover:bg-theme-sidebar-hover',
          String(p.id) === String(activeId) ? 'bg-theme-nav-selected/30' : '',
        ]"
        @click="selectProject(p.id)"
      >
        {{ p.name }}
      </button>
      <div class="border-t border-theme-border-sidebar mt-1 pt-1 px-2 space-y-1">
        <router-link
          :to="allProjectsLink"
          class="block px-2 py-1.5 text-xs text-theme-text-sidebar/90 hover:underline"
          @click="open = false"
        >
          All projects…
        </router-link>
        <router-link
          :to="createProjectLink"
          class="block px-2 py-1.5 text-xs text-theme-text-sidebar/90 hover:underline"
          @click="open = false"
        >
          Create project…
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FolderIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'
import { projectsService } from '@/services/projects'
import { getActiveProjectId, setActiveProjectId } from '@/utils/projectContext'

defineProps({
  collapsed: {
    type: Boolean,
    default: false,
  },
})

const projects = ref([])
const open = ref(false)
const route = useRoute()
const router = useRouter()

const activeId = computed(() => {
  const fromRoute = route.params.projectId
  if (fromRoute != null && fromRoute !== '') return String(fromRoute)
  return getActiveProjectId() || ''
})

function redirectPreservingQuery() {
  const r = route.query.redirect
  return typeof r === 'string' && r.startsWith('/') ? { redirect: r } : {}
}

const allProjectsLink = computed(() => ({
  name: 'Projects',
  query: redirectPreservingQuery(),
}))

const createProjectLink = computed(() => ({
  name: 'ProjectCreate',
  query: redirectPreservingQuery(),
}))

const currentLabel = computed(() => {
  if (!activeId.value) return 'Select project…'
  const p = projects.value.find(x => String(x.id) === String(activeId.value))
  return p?.name || `Project ${activeId.value}`
})

function onDocClick(e) {
  if (!open.value) return
  const root = e.target.closest?.('[data-project-switcher]')
  if (!root) open.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  load()
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
})

async function load() {
  try {
    const res = await projectsService.list()
    const list = res.data?.projects ?? []
    projects.value = list
    const stored = getActiveProjectId()
    if (stored && list.some(p => String(p.id) === String(stored))) {
      /* keep */
    } else if (list.length === 1) {
      setActiveProjectId(list[0].id)
    }
  } catch (e) {
    console.error('Failed to load projects', e)
  }
}

function selectProject(id) {
  setActiveProjectId(id)
  open.value = false
  const needs = route.matched.some(m => m.meta.requiresProject)
  if (needs && route.params.projectId != null && route.params.projectId !== '') {
    router.push({
      name: route.name,
      params: { ...route.params, projectId: String(id) },
      query: route.query,
      hash: route.hash,
    })
  }
}

watch(
  () => route.params.projectId,
  pid => {
    if (pid != null && pid !== '') setActiveProjectId(pid)
  }
)
</script>
