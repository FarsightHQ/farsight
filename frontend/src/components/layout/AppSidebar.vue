<template>
  <aside
    :class="[
      'bg-theme-sidebar border-r border-theme-border-sidebar flex-shrink-0 flex flex-col h-full transition-all duration-300 ease-in-out relative',
      isCollapsed ? 'w-16' : 'w-64'
    ]"
  >
    <!-- Floating Collapse Button on Border -->
    <button
      @click="toggleSidebar"
      :class="[
        'absolute top-1/2 -translate-y-1/2 z-10 p-2 bg-theme-sidebar border border-theme-border-sidebar rounded-full shadow-sm hover:shadow-md hover:bg-theme-active/50 transition-all duration-300 ease-in-out',
        isCollapsed ? 'right-2' : '-right-3'
      ]"
      aria-label="Toggle sidebar"
      :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
    >
      <ChevronLeftIcon v-if="!isCollapsed" class="h-4 w-4 text-theme-text-sidebar" />
      <ChevronRightIcon v-else class="h-4 w-4 text-theme-text-sidebar" />
    </button>

    <!-- Navigation Menu -->
    <nav class="flex-1 overflow-y-auto py-4">
      <ul :class="['space-y-1', isCollapsed ? 'px-2' : 'px-3']">
        <li>
          <router-link
            to="/"
            :class="[
              'flex items-center text-sm font-medium rounded-lg transition-colors',
              isCollapsed ? 'justify-center px-2 py-2' : 'px-3 py-2',
              'text-theme-text-sidebar hover:bg-theme-active/50'
            ]"
            active-class="bg-theme-nav-selected text-theme-text-sidebar"
            exact-active-class="bg-theme-nav-selected text-theme-text-sidebar"
            :title="isCollapsed ? 'Home' : ''"
          >
            <HomeIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
            <span
              :class="[
                'transition-all duration-300 ease-in-out whitespace-nowrap',
                isCollapsed ? 'opacity-0 max-w-0 overflow-hidden' : 'opacity-100 max-w-xs'
              ]"
            >
              Home
            </span>
          </router-link>
        </li>
        <li>
          <router-link
            to="/requests"
            :class="[
              'flex items-center text-sm font-medium rounded-lg transition-colors',
              isCollapsed ? 'justify-center px-2 py-2' : 'px-3 py-2',
              'text-theme-text-sidebar hover:bg-theme-active/50'
            ]"
            active-class="bg-theme-nav-selected text-theme-text-sidebar"
            :title="isCollapsed ? 'Requests' : ''"
          >
            <DocumentTextIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
            <span
              :class="[
                'transition-all duration-300 ease-in-out whitespace-nowrap',
                isCollapsed ? 'opacity-0 max-w-0 overflow-hidden' : 'opacity-100 max-w-xs'
              ]"
            >
              Requests
            </span>
          </router-link>
        </li>
        <li>
          <router-link
            to="/rules"
            :class="[
              'flex items-center text-sm font-medium rounded-lg transition-colors',
              isCollapsed ? 'justify-center px-2 py-2' : 'px-3 py-2',
              'text-theme-text-sidebar hover:bg-theme-active/50'
            ]"
            active-class="bg-theme-nav-selected text-theme-text-sidebar"
            :title="isCollapsed ? 'All Rules' : ''"
          >
            <ShieldCheckIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
            <span
              :class="[
                'transition-all duration-300 ease-in-out whitespace-nowrap',
                isCollapsed ? 'opacity-0 max-w-0 overflow-hidden' : 'opacity-100 max-w-xs'
              ]"
            >
              All Rules
            </span>
          </router-link>
        </li>
        <li>
          <router-link
            to="/assets"
            :class="[
              'flex items-center text-sm font-medium rounded-lg transition-colors',
              isCollapsed ? 'justify-center px-2 py-2' : 'px-3 py-2',
              'text-theme-text-sidebar hover:bg-theme-active/50'
            ]"
            active-class="bg-theme-nav-selected text-theme-text-sidebar"
            :title="isCollapsed ? 'Assets' : ''"
          >
            <ServerIcon :class="['h-5 w-5', isCollapsed ? '' : 'mr-3']" />
            <span
              :class="[
                'transition-all duration-300 ease-in-out whitespace-nowrap',
                isCollapsed ? 'opacity-0 max-w-0 overflow-hidden' : 'opacity-100 max-w-xs'
              ]"
            >
              Assets
            </span>
          </router-link>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script setup>
import {
  HomeIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  ServerIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/vue/24/outline'
import { useSidebar } from '@/composables/useSidebar'

const { isCollapsed, toggleSidebar } = useSidebar()
</script>

