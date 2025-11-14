<template>
  <Card class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-medium text-gray-900">Filters</h3>
      <Button v-if="hasActiveFilters" variant="ghost" size="sm" @click="clearFilters">
        Clear All
      </Button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <!-- Action Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Action</label>
        <select
          v-model="localFilters.action"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @change="updateFilters"
        >
          <option value="">All</option>
          <option value="allow">Allow</option>
          <option value="deny">Deny</option>
        </select>
      </div>

      <!-- Protocol Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Protocol</label>
        <select
          v-model="localFilters.protocol"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @change="updateFilters"
        >
          <option value="">All</option>
          <option value="tcp">TCP</option>
          <option value="udp">UDP</option>
          <option value="icmp">ICMP</option>
          <option value="any">Any</option>
        </select>
      </div>

      <!-- Has Facts Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Has Facts</label>
        <select
          v-model="localFilters.hasFacts"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @change="updateFilters"
        >
          <option value="">All</option>
          <option value="yes">Yes</option>
          <option value="no">No</option>
        </select>
      </div>

      <!-- Self-Flow Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Self-Flow</label>
        <select
          v-model="localFilters.selfFlow"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @change="updateFilters"
        >
          <option value="">All</option>
          <option value="yes">Yes</option>
          <option value="no">No</option>
        </select>
      </div>

      <!-- Any/Any Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Any/Any</label>
        <select
          v-model="localFilters.anyAny"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @change="updateFilters"
        >
          <option value="">All</option>
          <option value="source">Source Any</option>
          <option value="destination">Dest Any</option>
          <option value="both">Both</option>
          <option value="none">None</option>
        </select>
      </div>

      <!-- IP Range Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">IP Range (CIDR)</label>
        <input
          v-model="localFilters.ipRange"
          type="text"
          placeholder="e.g., 192.168.1.0/24"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @input="updateFilters"
        />
      </div>

      <!-- Port Range Filter -->
      <div>
        <label class="block text-xs font-medium text-gray-700 mb-2">Port Range</label>
        <input
          v-model="localFilters.portRange"
          type="text"
          placeholder="e.g., 80-443 or 8080"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @input="updateFilters"
        />
      </div>

      <!-- Active Filters Count -->
      <div class="flex items-end">
        <div v-if="hasActiveFilters" class="text-xs text-gray-600">
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
  action: props.filters.action || '',
  protocol: props.filters.protocol || '',
  hasFacts: props.filters.hasFacts || '',
  selfFlow: props.filters.selfFlow || '',
  anyAny: props.filters.anyAny || '',
  ipRange: props.filters.ipRange || '',
  portRange: props.filters.portRange || '',
})

watch(
  () => props.filters,
  (newFilters) => {
    localFilters.value = {
      action: newFilters.action || '',
      protocol: newFilters.protocol || '',
      hasFacts: newFilters.hasFacts || '',
      selfFlow: newFilters.selfFlow || '',
      anyAny: newFilters.anyAny || '',
      ipRange: newFilters.ipRange || '',
      portRange: newFilters.portRange || '',
    }
  },
  { deep: true }
)

const updateFilters = () => {
  emit('update:filters', { ...localFilters.value })
}

const clearFilters = () => {
  localFilters.value = {
    action: '',
    protocol: '',
    hasFacts: '',
    selfFlow: '',
    anyAny: '',
    ipRange: '',
    portRange: '',
  }
  updateFilters()
}

const hasActiveFilters = computed(() => {
  return Object.values(localFilters.value).some((value) => value !== '')
})

const activeFilterCount = computed(() => {
  return Object.values(localFilters.value).filter((value) => value !== '').length
})
</script>

