<template>
  <Card class="hover:shadow-md transition-shadow cursor-pointer" @click="$emit('click')">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="flex items-center space-x-3 mb-3">
          <h3 class="text-lg font-semibold text-gray-900">{{ request.title }}</h3>
          <StatusBadge :status="request.status" />
        </div>

        <div class="space-y-2 text-sm text-gray-600">
          <div v-if="request.external_id" class="flex items-center space-x-2">
            <span class="font-medium">External ID:</span>
            <span>{{ request.external_id }}</span>
          </div>
          <div class="flex items-center space-x-2">
            <span class="font-medium">Created:</span>
            <span>{{ formatDate(request.created_at) }}</span>
          </div>
          <div class="flex items-center space-x-2">
            <span class="font-medium">File:</span>
            <span class="truncate">{{ request.source_filename }}</span>
          </div>
        </div>
      </div>

      <div class="flex items-center space-x-2 ml-4" @click.stop>
        <Button variant="ghost" size="sm" @click="$emit('view', request)"> View </Button>
        <Button variant="ghost" size="sm" @click="$emit('delete', request)"> Delete </Button>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'

const props = defineProps({
  request: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['click', 'view', 'delete'])

const formatDate = dateString => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>
