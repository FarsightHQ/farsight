<template>
  <div class="h-full flex overflow-hidden bg-gray-50">
    <!-- Sidebar -->
    <AppSidebar />

    <!-- Main Area (Header + Content + Footer) -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Top Bar Header -->
      <AppHeader />

      <!-- Main Content Area (Scrollable) -->
      <main class="flex-1 overflow-y-auto bg-gray-50">
        <div class="p-6">
          <slot />
        </div>
      </main>

      <!-- Footer -->
      <AppFooter />
    </div>

    <!-- Toast Notifications -->
    <Toast />
  </div>
</template>

<script setup>
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
import AppFooter from './AppFooter.vue'
import Toast from '../ui/Toast.vue'
</script>


