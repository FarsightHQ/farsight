<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold">FAR Requests</h1>
      <Button variant="primary" @click="$router.push('/requests/new')">
        New Request
      </Button>
    </div>

    <Card>
      <p class="text-gray-600">Request list will be implemented in Phase 2</p>
    </Card>
  </div>
</template>

<script setup>
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
</script>

