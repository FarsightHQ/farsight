<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-theme-border-default">
      <thead class="bg-theme-content">
        <tr>
          <th class="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider w-12">
            <input
              type="checkbox"
              :checked="allSelected"
              :indeterminate="someSelected"
              class="rounded border-theme-border-default text-theme-active focus:ring-theme-active"
              @change="toggleSelectAll"
            />
          </th>
          <th
            class="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider cursor-pointer hover:bg-theme-active/50"
            @click="handleSort('id')"
          >
            <div class="flex items-center space-x-1">
              <span>ID</span>
              <ChevronUpIcon
                v-if="sortKey === 'id' && sortDirection === 'asc'"
                class="h-4 w-4 text-theme-active"
              />
              <ChevronDownIcon
                v-else-if="sortKey === 'id' && sortDirection === 'desc'"
                class="h-4 w-4 text-theme-active"
              />
              <ChevronUpIcon v-else class="h-4 w-4 text-theme-text-muted" />
            </div>
          </th>
          <th 
            v-if="showRequestColumn"
            class="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Request
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
            Source Networks
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
            Dest Networks
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
            Services
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider">
            Assessment
          </th>
          <th class="px-6 py-3 text-right text-xs font-medium text-theme-text-muted uppercase tracking-wider">
            Actions
          </th>
        </tr>
      </thead>
      <tbody class="bg-theme-card divide-y divide-theme-border-default">
        <!-- Loading Skeleton -->
        <tr v-if="loading" v-for="i in 5" :key="i">
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-4"></div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-16"></div>
          </td>
          <td v-if="showRequestColumn" class="px-6 py-4">
            <div class="h-4 bg-gray-200 rounded animate-pulse w-32"></div>
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
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <div class="h-8 bg-gray-200 rounded animate-pulse w-16"></div>
          </td>
        </tr>

        <!-- Rules Rows -->
        <tr
          v-else
          v-for="rule in rules"
          :key="rule.id"
          class="hover:bg-theme-active/30 transition-colors"
          :class="{
            'bg-theme-active': selectedRules.includes(rule.id),
            'bg-red-50': rule.health_status === 'critical' && !selectedRules.includes(rule.id),
            'bg-yellow-50': rule.health_status === 'warning' && !selectedRules.includes(rule.id)
          }"
        >
          <td class="px-6 py-4 whitespace-nowrap" @click.stop>
            <input
              type="checkbox"
              :checked="selectedRules.includes(rule.id)"
              class="rounded border-theme-border-default text-theme-active focus:ring-theme-active"
              @change="toggleRule(rule.id)"
            />
          </td>
          <td 
            class="px-6 py-4 whitespace-nowrap text-sm font-medium text-theme-text-content cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            {{ rule.id }}
          </td>
          <td 
            v-if="showRequestColumn"
            class="px-6 py-4 text-sm text-theme-text-content"
            @click.stop
          >
            <router-link
              v-if="rule.request"
              :to="`/requests/${rule.request.id}`"
              class="text-theme-active hover:text-theme-active/80 hover:underline"
            >
              {{ rule.request.title || `Request ${rule.request.id}` }}
            </router-link>
            <span v-else class="text-theme-text-muted">—</span>
          </td>
          <td 
            class="px-6 py-4 text-sm text-theme-text-content cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div 
              class="max-w-xs truncate" 
              :title="getOriginalCidr(rule.endpoints, 'source')"
            >
              {{ getFormattedNetworks(rule.id, 'source') || '—' }}
            </div>
          </td>
          <td 
            class="px-6 py-4 text-sm text-theme-text-content cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div 
              class="max-w-xs truncate" 
              :title="getOriginalCidr(rule.endpoints, 'destination')"
            >
              {{ getFormattedNetworks(rule.id, 'destination') || '—' }}
            </div>
          </td>
          <td 
            class="px-6 py-4 text-sm text-theme-text-content cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div class="max-w-xs truncate" :title="formatServices(rule.services)">
              {{ formatServices(rule.services) || '—' }}
            </div>
          </td>
          <td 
            class="px-6 py-4 text-sm cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div class="flex items-center space-x-2">
              <span 
                v-if="rule.health_status"
                :class="getAssessmentBadgeClass(rule.health_status)"
                class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
              >
                {{ getAssessmentBadgeText(rule.health_status) }}
              </span>
              <span 
                v-if="rule.problem_count && rule.problem_count > 0"
                class="text-theme-text-content"
              >
                {{ rule.problem_count }} {{ rule.problem_count === 1 ? 'problem' : 'problems' }}
              </span>
              <span v-if="!rule.health_status" class="text-theme-text-muted">—</span>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <div class="flex items-center justify-end space-x-2">
              <Button 
                variant="ghost" 
                size="sm" 
                :disabled="!hasNetworkData(rule)"
                :title="!hasNetworkData(rule) ? 'This rule has no network data to visualize' : 'Visualize network topology'"
                @click.stop="handleVisualize(rule)"
              >
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
          <td :colspan="showRequestColumn ? 8 : 7" class="px-6 py-12 text-center">
            <p class="text-theme-text-muted">No rules found</p>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline'
import Button from '@/components/ui/Button.vue'
import { formatCidrToRange } from '@/utils/ipUtils'
import { formatPortRanges } from '@/utils/portUtils'
import { useAssetCache } from '@/composables/useAssetCache'

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
  showRequestColumn: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['sort', 'view-rule', 'select-rule', 'select-all', 'deselect-all'])

// Asset cache for fetching hostnames
const { fetchAssetsForEndpoints, getAssetForCidr, cacheVersion } = useAssetCache()

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

// Check if rule has network data for visualization
const hasNetworkData = (rule) => {
  if (!rule) return false
  
  // Check if rule has endpoints array with source or destination entries
  const hasEndpoints = rule.endpoints && Array.isArray(rule.endpoints) && rule.endpoints.length > 0
  
  // Check if rule has services array
  const hasServices = rule.services && Array.isArray(rule.services) && rule.services.length > 0
  
  // Rule needs at least endpoints to visualize
  return hasEndpoints
}

// Handle visualize button click with validation
const handleVisualize = (rule) => {
  if (!hasNetworkData(rule)) {
    console.warn('[RulesTable] Rule has no network data for visualization:', rule.id)
    // Still emit the event - let the modal handle showing appropriate message
  }
  emit('visualize-rule', rule)
}

// Helper function to format networks (used by computed properties)
const formatNetworks = (endpoints, type) => {
  if (!endpoints || !Array.isArray(endpoints)) return ''
  const networks = endpoints
    .filter((ep) => ep.endpoint_type === type || ep.type === type)
    .map((ep) => {
      const cidr = ep.network_cidr || ep.cidr
      const ipRange = formatCidrToRange(cidr)
      
      // Try to get hostname from asset cache
      // Access cacheVersion to make this reactive
      const _ = cacheVersion.value
      const asset = getAssetForCidr(cidr)
      const hostname = asset?.hostname
      
      // Display format: "192.168.1.0 - 192.168.1.255 (hostname)" or just IP range if no hostname
      return hostname ? `${ipRange} (${hostname})` : ipRange
    })
  return networks.length > 0 ? networks.join(', ') : ''
}

// Create computed properties for each rule's formatted networks
// These will reactively update when cacheVersion changes
const formattedNetworksByRule = computed(() => {
  // Access cacheVersion to track changes
  const _ = cacheVersion.value
  
  const result = new Map()
  props.rules.forEach((rule) => {
    if (rule.endpoints) {
      result.set(rule.id, {
        source: formatNetworks(rule.endpoints, 'source'),
        destination: formatNetworks(rule.endpoints, 'destination'),
      })
    }
  })
  return result
})

// Helper to get formatted networks for a rule
const getFormattedNetworks = (ruleId, type) => {
  const networks = formattedNetworksByRule.value.get(ruleId)
  return networks ? networks[type] : ''
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

// Assessment helper functions
const getAssessmentBadgeClass = (healthStatus) => {
  const classes = {
    'critical': 'bg-red-100 text-red-800',
    'warning': 'bg-yellow-100 text-yellow-800',
    'clean': 'bg-green-100 text-green-800'
  }
  return classes[healthStatus] || 'bg-theme-active text-theme-text-content'
}

const getAssessmentBadgeText = (healthStatus) => {
  const texts = {
    'critical': 'Critical',
    'warning': 'Warning',
    'clean': 'Clean'
  }
  return texts[healthStatus] || healthStatus
}

// Fetch asset info for all unique IPs when rules change
watch(
  () => props.rules,
  async (newRules) => {
    if (!newRules || newRules.length === 0) return
    
    // Collect all endpoints from all rules
    const allEndpoints = []
    newRules.forEach((rule) => {
      if (rule.endpoints && Array.isArray(rule.endpoints)) {
        allEndpoints.push(...rule.endpoints)
      }
    })
    
    // Fetch asset info for all unique IPs
    await fetchAssetsForEndpoints(allEndpoints)
  },
  { immediate: true }
)

// Also fetch on mount
onMounted(async () => {
  if (props.rules && props.rules.length > 0) {
    const allEndpoints = []
    props.rules.forEach((rule) => {
      if (rule.endpoints && Array.isArray(rule.endpoints)) {
        allEndpoints.push(...rule.endpoints)
      }
    })
    await fetchAssetsForEndpoints(allEndpoints)
  }
})
</script>

