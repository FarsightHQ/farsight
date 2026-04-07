<template>
  <aside
    :class="[
      'bg-theme-sidebar border-r border-theme-border-sidebar flex-shrink-0 flex flex-col h-full transition-all duration-300 ease-in-out relative',
      isCollapsed ? 'w-16' : 'w-64',
    ]"
  >
    <button
      :class="[
        'absolute top-1/2 -translate-y-1/2 z-10 p-2 bg-theme-sidebar border border-theme-border-sidebar rounded-full shadow-sm hover:shadow-md hover:bg-theme-sidebar-hover transition-all duration-300 ease-in-out',
        isCollapsed ? 'right-2' : '-right-3',
      ]"
      aria-label="Toggle sidebar"
      :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      @click="toggleSidebar"
    >
      <ChevronLeftIcon v-if="!isCollapsed" class="h-4 w-4 text-theme-text-sidebar" />
      <ChevronRightIcon v-else class="h-4 w-4 text-theme-text-sidebar" />
    </button>

    <div :class="['border-b border-theme-border-sidebar shrink-0', isCollapsed ? 'px-2 py-2' : 'px-3 py-3']">
      <ProjectSwitcher :collapsed="isCollapsed" />
    </div>

    <nav class="flex-1 overflow-y-auto py-3">
      <div v-if="hasProjectContext" :class="[isCollapsed ? 'px-2' : 'px-3']">
        <button
          type="button"
          :class="[
            'flex w-full items-center text-xs font-semibold uppercase tracking-wide text-theme-text-sidebar/70 mb-1',
            isCollapsed ? 'justify-center' : 'justify-between',
          ]"
          :title="isCollapsed ? 'In this project' : ''"
          @click="inProjectOpen = !inProjectOpen"
        >
          <span v-if="!isCollapsed">In this project</span>
          <Squares2X2Icon v-if="isCollapsed" class="h-5 w-5 text-theme-text-sidebar/80" />
          <ChevronDownIcon
            v-else
            :class="['h-4 w-4 transition-transform', inProjectOpen ? 'rotate-180' : '']"
          />
        </button>
        <ul
          v-show="inProjectOpen || isCollapsed"
          :class="['space-y-1', isCollapsed ? '' : 'pl-3']"
        >
          <li>
            <router-link
              :to="{ name: 'ProjectOverview', params: { projectId } }"
              :class="navClass(true)"
              active-class="bg-theme-nav-selected text-theme-text-sidebar"
              :title="isCollapsed ? 'Details' : ''"
            >
              <DocumentIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
              <span v-if="!isCollapsed" class="truncate">Details</span>
            </router-link>
          </li>
          <li>
            <router-link
              :to="{ name: 'Requests', params: { projectId } }"
              :class="navClass(true)"
              active-class="bg-theme-nav-selected text-theme-text-sidebar"
              :title="isCollapsed ? 'Requests' : ''"
            >
              <DocumentTextIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
              <span v-if="!isCollapsed" class="truncate">Requests</span>
            </router-link>
          </li>
          <li>
            <router-link
              :to="{ name: 'AllRules', params: { projectId } }"
              :class="navClass(true)"
              active-class="bg-theme-nav-selected text-theme-text-sidebar"
              :title="isCollapsed ? 'All rules' : ''"
            >
              <ShieldCheckIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
              <span v-if="!isCollapsed" class="truncate">All rules</span>
            </router-link>
          </li>
          <li>
            <router-link
              :to="{ name: 'ProjectAssets', params: { projectId } }"
              :class="navClass(true)"
              active-class="bg-theme-nav-selected text-theme-text-sidebar"
              :title="isCollapsed ? 'Project assets' : ''"
            >
              <ServerIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
              <span v-if="!isCollapsed" class="truncate">Project assets</span>
            </router-link>
          </li>
        </ul>
      </div>

      <hr
        v-if="hasProjectContext && !isCollapsed"
        class="border-theme-border-sidebar mx-3 my-3"
      />

      <ul :class="['space-y-1', isCollapsed ? 'px-2' : 'px-3']">
        <li>
          <router-link
            :to="{ name: 'RegistryAssets' }"
            :class="navClass(false)"
            active-class="bg-theme-nav-selected text-theme-text-sidebar"
            :title="isCollapsed ? 'Assets (global)' : ''"
          >
            <CircleStackIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
            <span v-if="!isCollapsed" class="truncate">Assets</span>
          </router-link>
        </li>
        <li>
          <router-link
            :to="{ name: 'Settings' }"
            :class="navClass(false)"
            active-class="bg-theme-nav-selected text-theme-text-sidebar"
            :title="isCollapsed ? 'Settings' : ''"
          >
            <Cog6ToothIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
            <span v-if="!isCollapsed" class="truncate">Settings</span>
          </router-link>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  DocumentTextIcon,
  ShieldCheckIcon,
  ServerIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  Cog6ToothIcon,
  CircleStackIcon,
  DocumentIcon,
  Squares2X2Icon,
} from '@heroicons/vue/24/outline'
import { useSidebar } from '@/composables/useSidebar'
import { getActiveProjectId } from '@/utils/projectContext'
import ProjectSwitcher from './ProjectSwitcher.vue'

const route = useRoute()
const { isCollapsed, toggleSidebar } = useSidebar()
const inProjectOpen = ref(true)

const projectId = computed(() => {
  const p = route.params.projectId
  if (p != null && p !== '') return p
  const stored = getActiveProjectId()
  return stored || null
})

const hasProjectContext = computed(() => Boolean(projectId.value))

function navClass(sub) {
  return [
    'flex items-center text-sm font-medium rounded-lg transition-colors',
    isCollapsed.value ? 'justify-center px-2 py-2' : 'px-3 py-2',
    sub ? 'text-theme-text-sidebar/90' : 'text-theme-text-sidebar',
    'hover:bg-theme-sidebar-hover',
  ]
}

watch(
  () => route.params.projectId,
  () => {
    inProjectOpen.value = true
  }
)
</script>
