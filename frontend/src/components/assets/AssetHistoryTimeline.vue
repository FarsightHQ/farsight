<template>
  <Card class="p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Change History</h3>
    
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="h-16 bg-gray-200 rounded animate-pulse"></div>
    </div>

    <div v-else-if="error" class="text-center py-8">
      <p class="text-sm text-error-600">{{ error }}</p>
    </div>

    <div v-else-if="history && history.length > 0" class="space-y-4">
      <div
        v-for="(record, idx) in history"
        :key="idx"
        class="relative pl-8 pb-6 border-l-2 border-gray-200 last:border-l-0 last:pb-0"
      >
        <div class="absolute -left-2 top-0 w-4 h-4 bg-primary-600 rounded-full border-2 border-white"></div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-2">
              <Badge
                :label="record.change_type"
                :variant="getChangeTypeVariant(record.change_type)"
              />
              <span class="text-xs text-gray-500">Version {{ record.version }}</span>
            </div>
            <span class="text-xs text-gray-500">{{ formatDate(record.created_at) }}</span>
          </div>
          <p v-if="record.change_description" class="text-sm text-gray-700 mb-2">
            {{ record.change_description }}
          </p>
          <div class="text-xs text-gray-500">
            Changed by: {{ record.created_by || 'System' }}
          </div>
          <div v-if="record.changed_fields && record.changed_fields.length > 0" class="mt-2">
            <span class="text-xs font-medium text-gray-700">Changed fields:</span>
            <div class="flex flex-wrap gap-1 mt-1">
              <Badge
                v-for="field in record.changed_fields"
                :key="field"
                :label="field"
                variant="outline"
                class="text-xs"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-8">
      <p class="text-sm text-gray-500">No history records found</p>
    </div>
  </Card>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'
import { assetsService } from '@/services/assets'

const props = defineProps({
  ipAddress: {
    type: String,
    required: true,
  },
  limit: {
    type: Number,
    default: 50,
  },
})

const history = ref([])
const loading = ref(true)
const error = ref(null)

const fetchHistory = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await assetsService.getAssetHistory(props.ipAddress, props.limit)
    history.value = response.data?.history || response.history || []
  } catch (err) {
    error.value = err.message || 'Failed to load history'
    console.error('Error fetching history:', err)
  } finally {
    loading.value = false
  }
}

const getChangeTypeVariant = (changeType) => {
  const type = changeType?.toLowerCase() || ''
  if (type.includes('create')) return 'success'
  if (type.includes('update')) return 'info'
  if (type.includes('delete') || type.includes('deactivate')) return 'error'
  return 'outline'
}

const formatDate = (dateString) => {
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

onMounted(() => {
  fetchHistory()
})
</script>

