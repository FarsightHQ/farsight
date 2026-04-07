<template>
  <header class="h-16 bg-theme-header border-b border-theme-border-header shadow-sm flex-shrink-0">
    <div class="h-full flex items-center justify-between px-6">
      <!-- Left: App Icon + Name -->
      <div class="flex items-center space-x-3">
        <router-link to="/" class="flex items-center space-x-2">
          <EyeIcon class="h-8 w-8 text-theme-text-header" />
          <h1 class="text-xl font-bold text-theme-text-header">Farsight</h1>
        </router-link>
      </div>

      <!-- Center: project -->
      <div class="flex-1 flex justify-center px-4 min-w-0">
        <ProjectSwitcher v-if="authenticated" />
      </div>

      <!-- Right: User Details + Logout -->
      <div class="flex items-center space-x-4">
        <!-- User Info (shown when authenticated) -->
        <div v-if="authenticated && user" class="flex items-center space-x-3">
          <div class="text-right">
            <p class="text-sm font-medium text-theme-text-header">
              {{ user.name || user.username || 'User' }}
            </p>
            <p v-if="user.email" class="text-xs text-theme-text-header/70">
              {{ user.email }}
            </p>
          </div>
          <div
            class="h-10 w-10 rounded-full bg-theme-text-header/20 flex items-center justify-center"
          >
            <span class="text-sm font-medium text-theme-text-header">
              {{ getUserInitials(user) }}
            </span>
          </div>
        </div>

        <!-- Logout Button (shown when authenticated) -->
        <button
          v-if="authenticated"
          class="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-theme-text-header hover:text-theme-text-header/80 hover:bg-theme-text-header/10 rounded-lg transition-colors"
          @click="handleLogout"
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
import { useAuth } from '../../composables/useAuth'
import ProjectSwitcher from './ProjectSwitcher.vue'

const { authenticated, user, logout } = useAuth()

const handleLogout = () => {
  logout()
}

const getUserInitials = user => {
  if (user.name) {
    const names = user.name.split(' ')
    if (names.length >= 2) {
      return (names[0][0] + names[names.length - 1][0]).toUpperCase()
    }
    return names[0][0].toUpperCase()
  }
  if (user.username) {
    return user.username[0].toUpperCase()
  }
  if (user.email) {
    return user.email[0].toUpperCase()
  }
  return 'U'
}
</script>
