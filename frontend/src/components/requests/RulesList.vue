<template>
  <div class="space-y-6">

    <!-- Search -->
    <Card class="p-4">
      <div class="flex items-center space-x-4">
        <div class="flex-1 relative">
          <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none z-10" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by ID, CIDR, or port..."
            class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
            @input="handleSearch"
          />
        </div>
        <div v-if="searchQuery" class="flex items-center space-x-2">
          <span class="text-sm text-gray-600">{{ filteredRules.length }} results</span>
          <Button variant="ghost" size="sm" @click="clearSearch">Clear</Button>
        </div>
      </div>
    </Card>

    <!-- Rules Table -->
    <Card>
      <div v-if="selectedRules.length > 0" class="p-4 border-b border-gray-200 bg-gray-50">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-700">
            {{ selectedRules.length }} rule{{ selectedRules.length !== 1 ? 's' : '' }} selected
          </span>
          <Button 
            variant="primary" 
            @click="handleVisualizeSelected"
            :disabled="selectedRules.length === 0"
          >
            Visualize Selected
          </Button>
        </div>
      </div>
      <RulesTable
        :rules="paginatedRules"
        :loading="loading"
        :sort-key="sortKey"
        :sort-direction="sortDirection"
        :selected-rules="selectedRules"
        @sort="handleSort"
        @view-rule="$emit('view-rule', $event)"
        @visualize-rule="handleVisualizeRule"
        @select-rule="handleSelectRule"
        @select-all="handleSelectAll"
        @deselect-all="handleDeselectAll"
      />
    </Card>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-sm text-gray-700">Page size:</span>
        <select
          v-model="pageSize"
          class="rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
          @change="handlePageSizeChange"
        >
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>

      <div class="flex items-center space-x-2">
        <Button variant="outline" size="sm" :disabled="currentPage === 1" @click="currentPage--">
          Previous
        </Button>
        <span class="text-sm text-gray-700">
          Page {{ currentPage }} of {{ totalPages }} ({{ totalRules }} total)
        </span>
        <Button
          variant="outline"
          size="sm"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          Next
        </Button>
      </div>
    </div>

    <!-- Empty State -->
    <Card v-if="!loading && filteredRules.length === 0">
      <div class="text-center py-12">
        <p class="text-gray-600 mb-2">
          {{ searchQuery || hasActiveFilters ? 'No rules match your filters' : 'No rules found' }}
        </p>
        <Button v-if="searchQuery || hasActiveFilters" variant="outline" @click="clearAll">
          Clear Filters
        </Button>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import RulesTable from './RulesTable.vue'
import { rulesService } from '@/services/rules'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  requestId: {
    type: [String, Number],
    required: true,
  },
  filters: {
    type: Object,
    default: () => ({
      action: '',
      protocol: '',
      hasFacts: '',
      selfFlow: '',
      anyAny: '',
    }),
  },
})

const emit = defineEmits(['view-rule', 'stats-updated', 'rules-loaded', 'visualize-rule', 'visualize-multiple-rules'])

const { error: showError } = useToast()

const loading = ref(false)
const rules = ref([])
const stats = ref({})
const searchQuery = ref('')
const selectedRules = ref([])
const localFilters = ref({
  action: props.filters.action || '',
  protocol: props.filters.protocol || '',
  direction: props.filters.direction || '',
  hasFacts: props.filters.hasFacts || '',
  selfFlow: props.filters.selfFlow || '',
  anyAny: props.filters.anyAny || '',
  publicIP: props.filters.publicIP || '',
  hasIssues: props.filters.hasIssues || '',
})
const sortKey = ref('id')
const sortDirection = ref('asc')
const currentPage = ref(1)
const pageSize = ref(25)
const totalRules = ref(0)

// Debounce search
let searchTimeout = null
const handleSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1 // Reset to first page on search
  }, 300)
}

const clearSearch = () => {
  searchQuery.value = ''
  currentPage.value = 1
  selectedRules.value = [] // Clear selection when search changes
}

// Watch props.filters for external updates
watch(
  () => props.filters,
  (newFilters) => {
    localFilters.value = {
      action: newFilters.action || '',
      protocol: newFilters.protocol || '',
      direction: newFilters.direction || '',
      hasFacts: newFilters.hasFacts || '',
      selfFlow: newFilters.selfFlow || '',
      anyAny: newFilters.anyAny || '',
      publicIP: newFilters.publicIP || '',
      hasIssues: newFilters.hasIssues || '',
    }
    currentPage.value = 1
    selectedRules.value = [] // Clear selection when filters change
  },
  { deep: true }
)

const handleSort = (key) => {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
}

const handlePageSizeChange = () => {
  currentPage.value = 1
}

const clearAll = () => {
  searchQuery.value = ''
  localFilters.value = {
    action: '',
    protocol: '',
    direction: '',
    hasFacts: '',
    selfFlow: '',
    anyAny: '',
    publicIP: '',
    hasIssues: '',
  }
  currentPage.value = 1
}

const handleVisualizeRule = (rule) => {
  emit('visualize-rule', rule)
}

const handleSelectRule = (ruleId) => {
  const index = selectedRules.value.indexOf(ruleId)
  if (index > -1) {
    selectedRules.value.splice(index, 1)
  } else {
    selectedRules.value.push(ruleId)
  }
}

const handleSelectAll = (ruleIds) => {
  selectedRules.value = [...ruleIds]
}

const handleDeselectAll = () => {
  selectedRules.value = []
}

const mergeGraphData = (responses) => {
  const allSources = []
  const allDestinations = []
  const allConnections = []
  const sourceMap = new Map() // key: network_cidr
  const destMap = new Map() // key: network_cidr
  
  responses.forEach((response, index) => {
    const data = response.data?.data || response.data || response
    const graph = data.graph || data
    
    if (!graph.sources || !graph.destinations) return
    
    // Merge sources (deduplicate by network_cidr)
    graph.sources.forEach(src => {
      if (!sourceMap.has(src.network_cidr)) {
        sourceMap.set(src.network_cidr, {
          ...src,
          id: `src_merged_${sourceMap.size}`
        })
        allSources.push(sourceMap.get(src.network_cidr))
      }
    })
    
    // Merge destinations (deduplicate by network_cidr, merge ports)
    graph.destinations.forEach(dest => {
      if (!destMap.has(dest.network_cidr)) {
        destMap.set(dest.network_cidr, {
          ...dest,
          id: `dst_merged_${destMap.size}`,
          ports: [...(dest.ports || [])]
        })
        allDestinations.push(destMap.get(dest.network_cidr))
      } else {
        // Merge ports if destination already exists
        const existing = destMap.get(dest.network_cidr)
        if (dest.ports) {
          existing.ports.push(...dest.ports)
        }
      }
    })
    
    // Map connections to merged source/dest IDs
    graph.connections?.forEach(conn => {
      const source = graph.sources.find(s => s.id === conn.source_id)
      const dest = graph.destinations.find(d => d.id === conn.destination_id)
      
      if (source && dest) {
        const mergedSource = sourceMap.get(source.network_cidr)
        const mergedDest = destMap.get(dest.network_cidr)
        
        if (mergedSource && mergedDest) {
          allConnections.push({
            source_id: mergedSource.id,
            destination_id: mergedDest.id,
            port_count: conn.port_count,
            services: conn.services
          })
        }
      }
    })
  })
  
  return {
    sources: allSources,
    destinations: allDestinations,
    connections: allConnections,
    metadata: {
      rule_count: selectedRules.value.length,
      source_count: allSources.length,
      destination_count: allDestinations.length,
      connection_count: allConnections.length
    }
  }
}

const handleVisualizeSelected = async () => {
  if (selectedRules.value.length === 0) return
  
  try {
    // Fetch graph data for each selected rule
    const graphPromises = selectedRules.value.map(ruleId => 
      requestsService.getRuleGraph(ruleId)
    )
    
    const responses = await Promise.all(graphPromises)
    
    // Merge graph data from all selected rules
    const mergedGraph = mergeGraphData(responses)
    
    // Emit event with merged graph data
    emit('visualize-multiple-rules', {
      ruleIds: selectedRules.value,
      graphData: mergedGraph
    })
  } catch (err) {
    showError(err.message || 'Failed to load graph data')
  }
}

const hasActiveFilters = computed(() => {
  return Object.values(localFilters.value).some((value) => value !== '') || searchQuery.value !== ''
})

// Filter rules based on search and filters
const filteredRules = computed(() => {
  let filtered = [...rules.value]

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter((rule) => {
      const idMatch = String(rule.id).includes(query)
      const sourceMatch = rule.endpoints
        ?.some((ep) => (ep.network_cidr || ep.cidr || '').toLowerCase().includes(query))
      const destMatch = rule.endpoints
        ?.some((ep) => (ep.network_cidr || ep.cidr || '').toLowerCase().includes(query))
      const portMatch = rule.services?.some((svc) =>
        (svc.port_ranges || svc.ports || '').includes(query)
      )
      return idMatch || sourceMatch || destMatch || portMatch
    })
  }

  // Action filter
  if (localFilters.value.action) {
    filtered = filtered.filter((rule) => rule.action === localFilters.value.action)
  }

  // Protocol filter
  if (localFilters.value.protocol) {
    filtered = filtered.filter((rule) =>
      rule.services?.some((svc) => svc.protocol?.toLowerCase() === localFilters.value.protocol)
    )
  }

  // Has Facts filter
  if (localFilters.value.hasFacts === 'yes') {
    filtered = filtered.filter((rule) => rule.facts && Object.keys(rule.facts).length > 0)
  } else if (localFilters.value.hasFacts === 'no') {
    filtered = filtered.filter((rule) => !rule.facts || Object.keys(rule.facts).length === 0)
  }

  // Self-Flow filter
  if (localFilters.value.selfFlow === 'yes') {
    filtered = filtered.filter((rule) => rule.facts?.is_self_flow === true)
  } else if (localFilters.value.selfFlow === 'no') {
    filtered = filtered.filter((rule) => !rule.facts?.is_self_flow)
  }

  // Any/Any filter
  if (localFilters.value.anyAny) {
    if (localFilters.value.anyAny === 'source') {
      filtered = filtered.filter((rule) => rule.facts?.src_is_any === true)
    } else if (localFilters.value.anyAny === 'destination') {
      filtered = filtered.filter((rule) => rule.facts?.dst_is_any === true)
    } else if (localFilters.value.anyAny === 'both') {
      filtered = filtered.filter(
        (rule) => rule.facts?.src_is_any === true && rule.facts?.dst_is_any === true
      )
    } else if (localFilters.value.anyAny === 'none') {
      filtered = filtered.filter(
        (rule) => !rule.facts?.src_is_any && !rule.facts?.dst_is_any
      )
    }
  }

  // Public IP filter
  if (localFilters.value.publicIP) {
    if (localFilters.value.publicIP === 'src') {
      filtered = filtered.filter((rule) => rule.facts?.src_has_public === true)
    } else if (localFilters.value.publicIP === 'dst') {
      filtered = filtered.filter((rule) => rule.facts?.dst_has_public === true)
    } else if (localFilters.value.publicIP === 'either') {
      filtered = filtered.filter(
        (rule) => rule.facts?.src_has_public === true || rule.facts?.dst_has_public === true
      )
    } else if (localFilters.value.publicIP === 'none') {
      filtered = filtered.filter(
        (rule) => !rule.facts?.src_has_public && !rule.facts?.dst_has_public
      )
    }
  }

  // Direction filter
  if (localFilters.value.direction) {
    filtered = filtered.filter((rule) => {
      const ruleDirection = (rule.direction || 'bidirectional').toLowerCase()
      return ruleDirection === localFilters.value.direction.toLowerCase()
    })
  }

  // Has Issues filter (combines self-flow, any/any, public IPs)
  if (localFilters.value.hasIssues === 'yes') {
    filtered = filtered.filter((rule) => {
      const facts = rule.facts || {}
      return (
        facts.is_self_flow ||
        facts.src_is_any ||
        facts.dst_is_any ||
        facts.src_has_public ||
        facts.dst_has_public
      )
    })
  } else if (localFilters.value.hasIssues === 'no') {
    filtered = filtered.filter((rule) => {
      const facts = rule.facts || {}
      return (
        !facts.is_self_flow &&
        !facts.src_is_any &&
        !facts.dst_is_any &&
        !facts.src_has_public &&
        !facts.dst_has_public
      )
    })
  }

  // Sort
  filtered.sort((a, b) => {
    let aVal = a[sortKey.value]
    let bVal = b[sortKey.value]

    if (sortKey.value === 'created_at') {
      aVal = new Date(aVal).getTime()
      bVal = new Date(bVal).getTime()
    }

    if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1
    return 0
  })

  return filtered
})

// Pagination
const totalPages = computed(() => {
  return Math.ceil(filteredRules.value.length / pageSize.value)
})

const paginatedRules = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRules.value.slice(start, end)
})

// Fetch rules
const fetchRules = async () => {
  loading.value = true
  try {
    const response = await rulesService.getRules(props.requestId, {
      skip: 0,
      limit: 1000, // Fetch all for client-side filtering
      include_summary: true,
    })

    // Handle standardized response format
    const responseData = response.data || response
    const data = responseData.data || responseData
    
    if (data) {
      if (data.rules) {
        rules.value = data.rules
        emit('rules-loaded', data.rules)
      }
      if (data.summary) {
        stats.value = data.summary
        emit('stats-updated', data.summary)
      }
      if (data.pagination) {
        totalRules.value = data.pagination.total || rules.value.length
      }
    }
  } catch (err) {
    showError(err.message || 'Failed to load rules')
    rules.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => props.requestId,
  () => {
    if (props.requestId) {
      fetchRules()
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (props.requestId) {
    fetchRules()
  }
})
</script>

