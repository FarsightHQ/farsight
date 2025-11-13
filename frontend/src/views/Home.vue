<template>
  <div class="max-w-4xl mx-auto">
    <div class="text-center mb-12">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">Welcome to Farsight</h1>
      <p class="text-xl text-gray-600 mb-8">
        Firewall Access Rule Analysis System
      </p>
      <div class="flex gap-4 justify-center">
        <Button variant="primary" size="lg" @click="$router.push('/requests/new')">
          Create New Request
        </Button>
        <Button variant="outline" size="lg" @click="$router.push('/requests')">
          View Requests
        </Button>
      </div>
    </div>

    <div class="grid md:grid-cols-3 gap-6">
      <Card>
        <h3 class="text-lg font-semibold mb-2">Upload & Process</h3>
        <p class="text-gray-600 text-sm">
          Upload CSV files containing firewall rules and process them through our analysis pipeline.
        </p>
      </Card>

      <Card>
        <h3 class="text-lg font-semibold mb-2">Analyze & Visualize</h3>
        <p class="text-gray-600 text-sm">
          Get comprehensive security analysis and interactive network topology visualizations.
        </p>
      </Card>

      <Card>
        <h3 class="text-lg font-semibold mb-2">Manage Assets</h3>
        <p class="text-gray-600 text-sm">
          Track and manage network assets with our integrated asset registry system.
        </p>
      </Card>
    </div>
  </div>
</template>

<script setup>
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
</script>

