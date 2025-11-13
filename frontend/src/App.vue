<template>
  <div id="app" class="h-screen overflow-hidden bg-gray-50">
    <AppLayout>
      <router-view />
    </AppLayout>
  </div>
</template>

<script setup>
import AppLayout from './components/layout/AppLayout.vue'
</script>

