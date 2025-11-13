<template>
  <footer class="h-12 bg-white border-t border-gray-200 flex-shrink-0">
    <div class="h-full flex items-center justify-between px-6">
      <div class="flex items-center space-x-4 text-xs text-gray-500">
        <span>&copy; {{ currentYear }} Farsight. All rights reserved.</span>
      </div>
      <div class="flex items-center space-x-4 text-xs text-gray-400">
        <span>Version 2.0.0</span>
        <a href="#" class="hover:text-gray-600 transition-colors">Documentation</a>
        <a href="#" class="hover:text-gray-600 transition-colors">Support</a>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>

