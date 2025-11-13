<template>
  <header class="bg-white border-b border-gray-200 shadow-sm">
    <nav class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <router-link to="/" class="flex items-center space-x-2">
          <h1 class="text-xl font-bold text-primary-600">Farsight</h1>
        </router-link>

        <div class="flex items-center space-x-6">
          <router-link
            to="/requests"
            class="text-gray-700 hover:text-primary-600 font-medium transition-colors"
            active-class="text-primary-600"
          >
            Requests
          </router-link>
          <router-link
            to="/assets"
            class="text-gray-700 hover:text-primary-600 font-medium transition-colors"
            active-class="text-primary-600"
          >
            Assets
          </router-link>
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup>
// Header component with navigation
</script>

