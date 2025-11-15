<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            <input
              type="checkbox"
              :checked="allSelected"
              :indeterminate="someSelected"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              @change="handleSelectAllChange"
            />
          </th>
          <th
            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
            @click="handleSort('ip_address')"
          >
            <div class="flex items-center space-x-1">
              <span>IP Address</span>
              <ChevronUpIcon
                v-if="sortKey === 'ip_address' && sortDirection === 'asc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronDownIcon
                v-else-if="sortKey === 'ip_address' && sortDirection === 'desc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronUpIcon v-else class="h-4 w-4 text-gray-300" />
            </div>
          </th>
          <th
            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
            @click="handleSort('segment')"
          >
            <div class="flex items-center space-x-1">
              <span>Segment</span>
              <ChevronUpIcon
                v-if="sortKey === 'segment' && sortDirection === 'asc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronDownIcon
                v-else-if="sortKey === 'segment' && sortDirection === 'desc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronUpIcon v-else class="h-4 w-4 text-gray-300" />
            </div>
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            VLAN
          </th>
          <th
            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
            @click="handleSort('os_name')"
          >
            <div class="flex items-center space-x-1">
              <span>OS</span>
              <ChevronUpIcon
                v-if="sortKey === 'os_name' && sortDirection === 'asc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronDownIcon
                v-else-if="sortKey === 'os_name' && sortDirection === 'desc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronUpIcon v-else class="h-4 w-4 text-gray-300" />
            </div>
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Hostname
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Environment
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Status
          </th>
          <th
            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
            @click="handleSort('created_at')"
          >
            <div class="flex items-center space-x-1">
              <span>Created</span>
              <ChevronUpIcon
                v-if="sortKey === 'created_at' && sortDirection === 'asc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronDownIcon
                v-else-if="sortKey === 'created_at' && sortDirection === 'desc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronUpIcon v-else class="h-4 w-4 text-gray-300" />
            </div>
          </th>
          <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
            Actions
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <!-- Loading Skeleton -->
        <tr v-if="loading" v-for="i in 5" :key="i">
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-16"></div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-32"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-24"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-20"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-24"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-32"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-20"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-16"></div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-24"></div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <div class="h-8 bg-gray-200 rounded animate-pulse w-16"></div>
          </td>
        </tr>

        <!-- Assets Rows -->
        <tr
          v-else
          v-for="asset in assets"
          :key="asset.id"
          class="hover:bg-gray-50 cursor-pointer transition-colors"
          @click="$emit('view-asset', asset)"
        >
          <td class="px-6 py-4 whitespace-nowrap" @click.stop>
            <input
              type="checkbox"
              :checked="isSelected(asset.id)"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              @change="handleSelectAsset(asset.id, $event.target.checked)"
            />
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
            {{ asset.ip_address }}
          </td>
          <td class="px-6 py-4 text-sm text-gray-600">
            {{ asset.segment || '—' }}
          </td>
          <td class="px-6 py-4 text-sm text-gray-600">
            {{ asset.vlan || '—' }}
          </td>
          <td class="px-6 py-4 text-sm text-gray-600">
            {{ asset.os_name || '—' }}
          </td>
          <td class="px-6 py-4 text-sm text-gray-600">
            <div class="max-w-xs truncate" :title="asset.hostname">
              {{ asset.hostname || '—' }}
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <Badge v-if="asset.environment && String(asset.environment).trim()" :label="String(asset.environment).trim()" variant="info" />
            <span v-else class="text-gray-400">—</span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <StatusBadge
              :status="asset.is_active ? 'success' : 'error'"
              :label="asset.is_active ? 'Active' : 'Inactive'"
            />
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            {{ formatDate(asset.created_at) }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <Button variant="ghost" size="sm" @click.stop="$emit('view-asset', asset)">
              View
            </Button>
          </td>
        </tr>

        <!-- Empty State -->
        <tr v-if="!loading && assets.length === 0">
          <td colspan="10" class="px-6 py-12 text-center text-sm text-gray-500">
            No assets found
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import StatusBadge from '@/components/requests/StatusBadge.vue'

const props = defineProps({
  assets: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  selectedAssets: {
    type: Array,
    default: () => [],
  },
  sortKey: {
    type: String,
    default: '',
  },
  sortDirection: {
    type: String,
    default: 'asc',
  },
})

const emit = defineEmits(['view-asset', 'select-asset', 'select-all', 'sort'])

const allSelected = computed(() => {
  return props.assets.length > 0 && props.assets.every((asset) => props.selectedAssets.includes(asset.id))
})

const someSelected = computed(() => {
  return (
    props.selectedAssets.length > 0 &&
    props.selectedAssets.length < props.assets.length
  )
})

const isSelected = (assetId) => {
  return props.selectedAssets.includes(assetId)
}

const handleSelectAsset = (assetId, checked) => {
  emit('select-asset', assetId, checked)
}

const handleSelectAllChange = (event) => {
  emit('select-all', event.target.checked)
}

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
  })
}
</script>

