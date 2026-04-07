<template>
  <div class="relative min-w-0" data-project-switcher>
    <button
      ref="triggerRef"
      type="button"
      :class="[
        'w-full flex items-center gap-2 rounded-lg px-2 py-2 text-left text-sm',
        'bg-theme-sidebar hover:bg-theme-sidebar-hover text-theme-text-sidebar',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40 focus-visible:ring-offset-2 focus-visible:ring-offset-theme-sidebar',
        collapsed ? 'justify-center px-1' : '',
      ]"
      :title="collapsed ? currentLabel : 'Switch project'"
      aria-haspopup="listbox"
      :aria-expanded="open"
      @click="open = !open"
    >
      <FolderIcon class="h-5 w-5 shrink-0 text-theme-text-sidebar" />
      <span v-if="!collapsed" class="truncate flex-1 min-w-0 font-medium">
        {{ currentLabel }}
      </span>
      <ChevronRightIcon
        v-if="!collapsed"
        class="h-4 w-4 shrink-0 text-theme-text-sidebar/80"
        aria-hidden="true"
      />
    </button>

    <div
      v-if="open"
      class="absolute left-full top-0 z-50 ml-2 min-w-[14rem] max-w-[min(20rem,calc(100vw-4rem))] max-h-64 overflow-y-auto rounded-lg border border-theme-border-default bg-theme-card py-1 shadow-xl"
      role="listbox"
    >
      <button
        v-for="p in projects"
        :key="p.id"
        type="button"
        role="option"
        :aria-selected="String(p.id) === String(activeId)"
        :class="[
          'w-full text-left px-3 py-2 text-sm text-theme-text-content truncate rounded-md mx-1',
          'hover:bg-theme-content focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-inset',
          String(p.id) === String(activeId)
            ? 'bg-primary-50 font-medium text-theme-text-content'
            : '',
        ]"
        @click="selectProject(p.id)"
      >
        {{ p.name }}
      </button>
      <div
        class="mt-1 border-t border-theme-border-default pt-2 px-2 pb-1 space-y-0.5"
        role="presentation"
      >
        <p class="px-2 pt-0.5 text-xs font-semibold uppercase tracking-wide text-theme-text-muted">
          More
        </p>
        <router-link
          :to="allProjectsLink"
          class="block rounded-md px-3 py-2 text-sm text-theme-text-content hover:bg-theme-content focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-inset"
          @click="open = false"
        >
          All projects…
        </router-link>
        <router-link
          :to="createProjectLink"
          class="block rounded-md px-3 py-2 text-sm text-theme-text-content hover:bg-theme-content focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-inset"
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
import { FolderIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'
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
const triggerRef = ref(null)
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

function onKeydown(e) {
  if (e.key !== 'Escape' || !open.value) return
  open.value = false
  triggerRef.value?.focus()
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKeydown, true)
  load()
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKeydown, true)
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
