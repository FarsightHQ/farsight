<template>
  <aside class="w-64 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col h-full">
    <!-- Navigation Menu -->
    <nav class="flex-1 overflow-y-auto py-4">
      <ul class="space-y-1 px-3">
        <li>
          <router-link
            to="/"
            class="flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors"
            active-class="bg-primary-50 text-primary-700"
            exact-active-class="bg-primary-50 text-primary-700"
          >
            <HomeIcon class="h-5 w-5 mr-3" />
            <span>Home</span>
          </router-link>
        </li>
        <li>
          <router-link
            to="/requests"
            class="flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors text-gray-700 hover:bg-gray-100"
            active-class="bg-primary-50 text-primary-700"
          >
            <DocumentTextIcon class="h-5 w-5 mr-3" />
            <span>Requests</span>
          </router-link>
        </li>
        <li>
          <router-link
            to="/rules"
            class="flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors text-gray-700 hover:bg-gray-100"
            active-class="bg-primary-50 text-primary-700"
          >
            <ShieldCheckIcon class="h-5 w-5 mr-3" />
            <span>All Rules</span>
          </router-link>
        </li>
        <li>
          <router-link
            to="/assets"
            class="flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors text-gray-700 hover:bg-gray-100"
            active-class="bg-primary-50 text-primary-700"
          >
            <ServerIcon class="h-5 w-5 mr-3" />
            <span>Assets</span>
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
} from '@heroicons/vue/24/outline'
</script>

