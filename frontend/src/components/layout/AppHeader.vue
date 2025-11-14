<template>
  <header class="h-16 bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
    <div class="h-full flex items-center justify-between px-6">
      <!-- Left: Page Title or Breadcrumb -->
      <div class="flex items-center">
        <h2 class="text-lg font-semibold text-gray-900">{{ pageTitle }}</h2>
      </div>

      <!-- Right: Navigation and User Menu -->
      <div class="flex items-center space-x-4">
        <!-- Additional navigation items can go here -->
        <div class="flex items-center space-x-2">
          <!-- User menu placeholder -->
          <div class="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
            <span class="text-sm font-medium text-primary-700">U</span>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const pageTitle = computed(() => {
  const titles = {
    '/': 'Dashboard',
    '/requests': 'FAR Requests',
    '/requests/new': 'Create Request',
    '/assets': 'Asset Registry',
    '/assets/upload': 'Upload Assets',
  }
  
  // Handle asset detail pages
  if (route.path.startsWith('/assets/') && route.path !== '/assets' && route.path !== '/assets/upload') {
    return `Asset: ${route.params.ip_address}`
  }
  
  return titles[route.path] || 'Farsight'
})
</script>

