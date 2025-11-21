<template>
  <div class="h-full flex flex-col overflow-hidden bg-gray-50">
    <!-- Top Bar Header (Full Width) -->
    <AppHeader />

    <!-- Main Area (Sidebar + Content + Footer) -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar -->
      <AppSidebar />

      <!-- Content Area (Scrollable) -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Main Content Area (Scrollable) -->
        <main class="flex-1 overflow-y-auto bg-gray-50">
          <div class="p-6">
            <slot />
          </div>
        </main>

        <!-- Footer -->
        <AppFooter />
      </div>
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


