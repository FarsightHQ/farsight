<template>
  <footer class="bg-white border-t border-gray-200 mt-auto">
    <div class="container mx-auto px-4 py-6">
      <div class="flex items-center justify-between text-sm text-gray-600">
        <p>&copy; {{ currentYear }} Farsight. All rights reserved.</p>
        <p class="text-gray-400">Version 2.0.0</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>

