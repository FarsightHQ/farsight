<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
            <input
              type="checkbox"
              :checked="allSelected"
              :indeterminate="someSelected"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              @change="toggleSelectAll"
            />
          </th>
          <th
            class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
            @click="handleSort('id')"
          >
            <div class="flex items-center space-x-1">
              <span>ID</span>
              <ChevronUpIcon
                v-if="sortKey === 'id' && sortDirection === 'asc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronDownIcon
                v-else-if="sortKey === 'id' && sortDirection === 'desc'"
                class="h-4 w-4 text-primary-600"
              />
              <ChevronUpIcon v-else class="h-4 w-4 text-gray-300" />
            </div>
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Source Networks
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Dest Networks
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Services
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
            <div class="h-4 bg-gray-200 rounded animate-pulse w-4"></div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-16"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-32"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-32"></div>
          </td>
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-24"></div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <div class="h-8 bg-gray-200 rounded animate-pulse w-16"></div>
          </td>
        </tr>

        <!-- Rules Rows -->
        <tr
          v-else
          v-for="rule in rules"
          :key="rule.id"
          class="hover:bg-gray-50 transition-colors"
          :class="{ 'bg-primary-50': selectedRules.includes(rule.id) }"
        >
          <td class="px-6 py-4 whitespace-nowrap" @click.stop>
            <input
              type="checkbox"
              :checked="selectedRules.includes(rule.id)"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              @change="toggleRule(rule.id)"
            />
          </td>
          <td 
            class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            {{ rule.id }}
          </td>
          <td 
            class="px-6 py-4 text-sm text-gray-600 cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div 
              class="max-w-xs truncate" 
              :title="getOriginalCidr(rule.endpoints, 'source')"
            >
              {{ formatNetworks(rule.endpoints, 'source') || '—' }}
            </div>
          </td>
          <td 
            class="px-6 py-4 text-sm text-gray-600 cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div 
              class="max-w-xs truncate" 
              :title="getOriginalCidr(rule.endpoints, 'destination')"
            >
              {{ formatNetworks(rule.endpoints, 'destination') || '—' }}
            </div>
          </td>
          <td 
            class="px-6 py-4 text-sm text-gray-600 cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div class="max-w-xs truncate" :title="formatServices(rule.services)">
              {{ formatServices(rule.services) || '—' }}
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <div class="flex items-center justify-end space-x-2">
              <Button variant="ghost" size="sm" @click.stop="$emit('visualize-rule', rule)">
                Visualize
              </Button>
              <Button variant="ghost" size="sm" @click.stop="$emit('view-rule', rule)">
                View
              </Button>
            </div>
          </td>
        </tr>

        <!-- Empty State -->
        <tr v-if="!loading && rules.length === 0">
          <td colspan="6" class="px-6 py-12 text-center">
            <p class="text-gray-500">No rules found</p>
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
import { formatCidrToRange } from '@/utils/ipUtils'
import { formatPortRanges } from '@/utils/portUtils'

const props = defineProps({
  rules: {
    type: Array,
    default: () => [],
  },
  selectedRules: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  sortKey: {
    type: String,
    default: null,
  },
  sortDirection: {
    type: String,
    default: 'asc',
    validator: (value) => ['asc', 'desc'].includes(value),
  },
})

const emit = defineEmits(['sort', 'view-rule', 'select-rule', 'select-all', 'deselect-all'])

const allSelected = computed(() => {
  return props.rules.length > 0 && props.rules.every(rule => props.selectedRules.includes(rule.id))
})

const someSelected = computed(() => {
  return props.selectedRules.length > 0 && !allSelected.value
})

const toggleSelectAll = () => {
  if (allSelected.value) {
    emit('deselect-all')
  } else {
    emit('select-all', props.rules.map(r => r.id))
  }
}

const toggleRule = (ruleId) => {
  emit('select-rule', ruleId)
}

const handleSort = (key) => {
  emit('sort', key)
}

const formatNetworks = (endpoints, type) => {
  if (!endpoints || !Array.isArray(endpoints)) return ''
  const networks = endpoints
    .filter((ep) => ep.endpoint_type === type || ep.type === type)
    .map((ep) => {
      const cidr = ep.network_cidr || ep.cidr
      return formatCidrToRange(cidr)
    })
  return networks.length > 0 ? networks.join(', ') : ''
}

// Helper to get original CIDR for tooltip
const getOriginalCidr = (endpoints, type) => {
  if (!endpoints || !Array.isArray(endpoints)) return ''
  const networks = endpoints
    .filter((ep) => ep.endpoint_type === type || ep.type === type)
    .map((ep) => ep.network_cidr || ep.cidr)
  return networks.length > 0 ? networks.join(', ') : ''
}

const formatServices = (services) => {
  if (!services || !Array.isArray(services)) return ''
  return services
    .map((svc) => {
      const protocol = (svc.protocol || '').toUpperCase()
      const ports = svc.port_ranges || svc.ports || ''
      const formattedPorts = formatPortRanges(ports)
      return formattedPorts ? `${protocol}: ${formattedPorts}` : protocol
    })
    .join(', ')
}
</script>

