<template>
  <header class="h-16 bg-white border-b border-gray-200 shadow-sm flex-shrink-0">
    <div class="h-full flex items-center justify-between px-6">
      <!-- Left: App Icon + Name -->
      <div class="flex items-center space-x-3">
        <router-link to="/" class="flex items-center space-x-2">
          <EyeIcon class="h-8 w-8 text-primary-600" />
          <h1 class="text-xl font-bold text-primary-600">Farsight</h1>
        </router-link>
      </div>

      <!-- Right: User Details + Logout -->
      <div class="flex items-center space-x-4">
        <!-- User Info -->
        <div class="flex items-center space-x-3">
          <div class="text-right">
            <p class="text-sm font-medium text-gray-900">User Name</p>
            <p class="text-xs text-gray-500">user@example.com</p>
          </div>
          <div class="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
            <span class="text-sm font-medium text-primary-700">U</span>
          </div>
        </div>
        
        <!-- Logout Button -->
        <button
          @click="handleLogout"
          class="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowRightOnRectangleIcon class="h-5 w-5" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { EyeIcon, ArrowRightOnRectangleIcon } from '@heroicons/vue/24/outline'

const handleLogout = () => {
  // TODO: Implement logout logic
  // Clear auth tokens, user session, etc.
  console.log('Logout clicked')
  // router.push('/login')
}
</script>

