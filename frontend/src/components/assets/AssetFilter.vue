<template>
  <Card class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-medium text-gray-900">Filters</h3>
      <Button v-if="hasActiveFilters" variant="ghost" size="sm" @click="clearFilters">
        Clear All
      </Button>
    </div>

    <!-- Stack filters vertically for sidebar -->
    <div class="space-y-4">
      <!-- IP Address Search -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">IP Address</label>
        <input
          v-model="localFilters.ip_address"
          type="text"
          placeholder="e.g., 192.168.1.1"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @input="updateFilters"
        />
      </div>

      <!-- IP Range Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">IP Range (CIDR)</label>
        <input
          v-model="localFilters.ip_range"
          type="text"
          placeholder="e.g., 192.168.1.0/24"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @input="updateFilters"
        />
      </div>

      <!-- Segment Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Segment</label>
        <input
          v-model="localFilters.segment"
          type="text"
          placeholder="Segment name"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @input="updateFilters"
        />
      </div>

      <!-- OS Name Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">OS Name</label>
        <input
          v-model="localFilters.os_name"
          type="text"
          placeholder="e.g., Linux, Windows"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @input="updateFilters"
        />
      </div>

      <!-- VLAN Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">VLAN</label>
        <input
          v-model="localFilters.vlan"
          type="text"
          placeholder="VLAN ID"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @input="updateFilters"
        />
      </div>

      <!-- Environment Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Environment</label>
        <select
          v-model="localFilters.environment"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @change="updateFilters"
        >
          <option value="">All</option>
          <option value="dev">Dev</option>
          <option value="stage">Stage</option>
          <option value="prod">Prod</option>
          <option value="test">Test</option>
        </select>
      </div>

      <!-- Hostname Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Hostname</label>
        <input
          v-model="localFilters.hostname"
          type="text"
          placeholder="Hostname"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @input="updateFilters"
        />
      </div>

      <!-- Active/Inactive Toggle -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Status</label>
        <select
          v-model="localFilters.is_active"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @change="updateFilters"
        >
          <option :value="true">Active</option>
          <option :value="false">Inactive</option>
          <option value="">All</option>
        </select>
      </div>

      <!-- Active Filters Count -->
      <div v-if="hasActiveFilters" class="pt-2 border-t border-gray-200">
        <div class="text-xs text-gray-600">
          <span class="font-medium">{{ activeFilterCount }}</span> filter(s) active
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:filters'])

const localFilters = ref({
  ip_address: props.filters.ip_address || '',
  ip_range: props.filters.ip_range || '',
  segment: props.filters.segment || '',
  vlan: props.filters.vlan || '',
  os_name: props.filters.os_name || '',
  environment: props.filters.environment || '',
  hostname: props.filters.hostname || '',
  is_active: props.filters.is_active !== undefined ? props.filters.is_active : true,
})

watch(
  () => props.filters,
  (newFilters) => {
    localFilters.value = {
      ip_address: newFilters.ip_address || '',
      ip_range: newFilters.ip_range || '',
      segment: newFilters.segment || '',
      vlan: newFilters.vlan || '',
      os_name: newFilters.os_name || '',
      environment: newFilters.environment || '',
      hostname: newFilters.hostname || '',
      is_active: newFilters.is_active !== undefined ? newFilters.is_active : true,
    }
  },
  { deep: true }
)

const updateFilters = () => {
  const filters = { ...localFilters.value }
  // Convert is_active to proper type
  if (filters.is_active === '') {
    filters.is_active = undefined
  } else if (filters.is_active === 'true' || filters.is_active === true) {
    filters.is_active = true
  } else if (filters.is_active === 'false' || filters.is_active === false) {
    filters.is_active = false
  }
  emit('update:filters', filters)
}

const clearFilters = () => {
  localFilters.value = {
    ip_address: '',
    ip_range: '',
    segment: '',
    vlan: '',
    os_name: '',
    environment: '',
    hostname: '',
    is_active: true,
  }
  updateFilters()
}

const hasActiveFilters = computed(() => {
  return (
    localFilters.value.ip_address !== '' ||
    localFilters.value.ip_range !== '' ||
    localFilters.value.segment !== '' ||
    localFilters.value.vlan !== '' ||
    localFilters.value.os_name !== '' ||
    localFilters.value.environment !== '' ||
    localFilters.value.hostname !== '' ||
    localFilters.value.is_active !== true
  )
})

const activeFilterCount = computed(() => {
  let count = 0
  if (localFilters.value.ip_address !== '') count++
  if (localFilters.value.ip_range !== '') count++
  if (localFilters.value.segment !== '') count++
  if (localFilters.value.vlan !== '') count++
  if (localFilters.value.os_name !== '') count++
  if (localFilters.value.environment !== '') count++
  if (localFilters.value.hostname !== '') count++
  if (localFilters.value.is_active !== true) count++
  return count
})
</script>

