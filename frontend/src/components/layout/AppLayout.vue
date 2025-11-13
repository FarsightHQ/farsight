<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    <main class="container mx-auto px-4 py-8">
      <slot />
    </main>
    <AppFooter />
    <Toast />
  </div>
</template>

<script setup>
import AppHeader from './AppHeader.vue'
import AppFooter from './AppFooter.vue'
import Toast from '../ui/Toast.vue'
</script>

