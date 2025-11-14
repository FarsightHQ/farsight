<template>
  <Card class="p-4 hover:shadow-md transition-shadow cursor-pointer" @click="$emit('view-asset', asset)">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="flex items-center space-x-2 mb-2">
          <h3 class="text-lg font-semibold text-gray-900">{{ asset.ip_address }}</h3>
          <StatusBadge
            :status="asset.is_active ? 'success' : 'error'"
            :label="asset.is_active ? 'Active' : 'Inactive'"
          />
        </div>
        <div class="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span class="text-gray-500">Segment:</span>
            <span class="ml-2 text-gray-900">{{ asset.segment || '—' }}</span>
          </div>
          <div>
            <span class="text-gray-500">OS:</span>
            <span class="ml-2 text-gray-900">{{ asset.os_name || '—' }}</span>
          </div>
          <div>
            <span class="text-gray-500">VLAN:</span>
            <span class="ml-2 text-gray-900">{{ asset.vlan || '—' }}</span>
          </div>
          <div>
            <span class="text-gray-500">Environment:</span>
            <Badge v-if="asset.environment" :label="asset.environment" variant="info" class="ml-2" />
            <span v-else class="ml-2 text-gray-400">—</span>
          </div>
          <div v-if="asset.hostname" class="col-span-2">
            <span class="text-gray-500">Hostname:</span>
            <span class="ml-2 text-gray-900">{{ asset.hostname }}</span>
          </div>
        </div>
      </div>
      <div class="ml-4" @click.stop>
        <input
          type="checkbox"
          :checked="isSelected"
          class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          @change="$emit('select-asset', asset.id, $event.target.checked)"
        />
      </div>
    </div>
    <div class="mt-4 flex items-center justify-between">
      <span class="text-xs text-gray-500">
        Created {{ formatDate(asset.created_at) }}
      </span>
      <Button variant="ghost" size="sm" @click.stop="$emit('view-asset', asset)">
        View Details
      </Button>
    </div>
  </Card>
</template>

<script setup>
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import StatusBadge from '@/components/requests/StatusBadge.vue'

const props = defineProps({
  asset: {
    type: Object,
    required: true,
  },
  isSelected: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['view-asset', 'select-asset'])

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}
</script>

