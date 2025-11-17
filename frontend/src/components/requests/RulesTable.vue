<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
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
            Action
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
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Facts
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
            <div class="h-6 bg-gray-200 rounded animate-pulse w-20"></div>
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
          <td class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-20"></div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
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
          class="hover:bg-gray-50 cursor-pointer transition-colors"
          @click="$emit('view-rule', rule)"
        >
          <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
            {{ rule.id }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <StatusBadge
              :status="rule.action === 'allow' ? 'success' : 'error'"
              :label="rule.action"
            />
          </td>
          <td class="px-6 py-4 text-sm text-gray-600">
            <div 
              class="max-w-xs truncate" 
              :title="getOriginalCidr(rule.endpoints, 'source')"
            >
              {{ formatNetworks(rule.endpoints, 'source') || '—' }}
            </div>
          </td>
          <td class="px-6 py-4 text-sm text-gray-600">
            <div 
              class="max-w-xs truncate" 
              :title="getOriginalCidr(rule.endpoints, 'destination')"
            >
              {{ formatNetworks(rule.endpoints, 'destination') || '—' }}
            </div>
          </td>
          <td class="px-6 py-4 text-sm text-gray-600">
            <div class="max-w-xs truncate" :title="formatServices(rule.services)">
              {{ formatServices(rule.services) || '—' }}
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center space-x-1">
              <RuleFactsIndicator :facts="rule.facts" />
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            {{ formatDate(rule.created_at) }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <Button variant="ghost" size="sm" @click.stop="$emit('view-rule', rule)">
              View
            </Button>
          </td>
        </tr>

        <!-- Empty State -->
        <tr v-if="!loading && rules.length === 0">
          <td colspan="8" class="px-6 py-12 text-center">
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
import StatusBadge from './StatusBadge.vue'
import RuleFactsIndicator from './RuleFactsIndicator.vue'
import { formatCidrToRange } from '@/utils/ipUtils'
import { formatPortRanges } from '@/utils/portUtils'

const props = defineProps({
  rules: {
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

const emit = defineEmits(['sort', 'view-rule'])

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

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
</script>

