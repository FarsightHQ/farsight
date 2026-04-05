<template>
  <footer class="h-12 bg-theme-footer border-t border-theme-border-footer flex-shrink-0">
    <div class="h-full flex items-center justify-between px-6">
      <div class="flex items-center space-x-4 text-xs text-theme-text-footer">
        <span>&copy; {{ currentYear }} Farsight. All rights reserved.</span>
      </div>
      <div class="flex items-center space-x-4 text-xs text-theme-text-footer/70">
        <span>Version 2.0.0</span>
        <a href="#" class="hover:text-theme-text-footer transition-colors">Documentation</a>
        <a href="#" class="hover:text-theme-text-footer transition-colors">Support</a>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>
