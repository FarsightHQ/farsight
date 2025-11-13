<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :class="[
              'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
              column.sortable ? 'cursor-pointer hover:bg-gray-100' : '',
            ]"
            @click="column.sortable && handleSort(column.key)"
          >
            <div class="flex items-center space-x-1">
              <span>{{ column.label }}</span>
              <span v-if="column.sortable" class="flex flex-col">
                <svg
                  :class="[
                    'h-3 w-3',
                    sortKey === column.key && sortDirection === 'asc'
                      ? 'text-primary-600'
                      : 'text-gray-400',
                  ]"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                    clip-rule="evenodd"
                  />
                </svg>
                <svg
                  :class="[
                    'h-3 w-3 -mt-1',
                    sortKey === column.key && sortDirection === 'desc'
                      ? 'text-primary-600'
                      : 'text-gray-400',
                  ]"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                    clip-rule="evenodd"
                  />
                </svg>
              </span>
            </div>
          </th>
          <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
            Actions
          </th>
        </tr>
      </thead>
      <tbody v-if="loading" class="bg-white divide-y divide-gray-200">
        <tr v-for="i in 5" :key="i">
          <td v-for="column in columns" :key="column.key" class="px-6 py-4 whitespace-nowrap">
            <div class="h-4 bg-gray-200 rounded animate-pulse"></div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-16 ml-auto"></div>
          </td>
        </tr>
      </tbody>
      <tbody v-else-if="requests.length === 0" class="bg-white">
        <tr>
          <td :colspan="columns.length + 1" class="px-6 py-12 text-center text-gray-500">
            No requests found
          </td>
        </tr>
      </tbody>
      <tbody v-else class="bg-white divide-y divide-gray-200">
        <tr
          v-for="request in requests"
          :key="request.id"
          class="hover:bg-gray-50 transition-colors"
        >
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
            {{ request.id }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            {{ request.title }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <StatusBadge :status="request.status" />
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            {{ request.external_id || '—' }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            {{ formatDate(request.created_at) }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <div class="flex items-center justify-end space-x-2">
              <Button variant="ghost" size="sm" @click="$emit('view', request)">
                View
              </Button>
              <Button variant="ghost" size="sm" @click="$emit('delete', request)">
                Delete
              </Button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Button from '@/components/ui/Button.vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  requests: {
    type: Array,
    default: () => [],
  },
  columns: {
    type: Array,
    default: () => [
      { key: 'id', label: 'ID', sortable: true },
      { key: 'title', label: 'Title', sortable: true },
      { key: 'status', label: 'Status', sortable: true },
      { key: 'external_id', label: 'External ID', sortable: false },
      { key: 'created_at', label: 'Created', sortable: true },
    ],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  sortKey: {
    type: String,
    default: 'created_at',
  },
  sortDirection: {
    type: String,
    default: 'desc',
    validator: (value) => ['asc', 'desc'].includes(value),
  },
})

const emit = defineEmits(['sort', 'view', 'delete'])

const handleSort = (key) => {
  emit('sort', key)
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
</script>

