<template>
  <div class="space-y-6">
    <!-- Stats -->
    <RulesStats v-if="stats && Object.keys(stats).length > 0" :stats="stats" />

    <!-- Filters -->
    <RulesFilter :filters="filters" @update:filters="handleFilterUpdate" />

    <!-- Search and Actions Bar -->
    <Card class="p-4">
      <div class="flex items-center space-x-4 mb-4">
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

      <!-- View Mode and Export Controls -->
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-600">View:</span>
          <div class="flex border border-gray-300 rounded-md overflow-hidden">
            <button
              :class="[
                'px-3 py-1 text-sm font-medium transition-colors',
                viewMode === 'table'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50',
              ]"
              @click="viewMode = 'table'"
            >
              Table
            </button>
            <button
              :class="[
                'px-3 py-1 text-sm font-medium transition-colors border-l border-gray-300',
                viewMode === 'cards'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50',
              ]"
              @click="viewMode = 'cards'"
            >
              Cards
            </button>
            <button
              :class="[
                'px-3 py-1 text-sm font-medium transition-colors border-l border-gray-300',
                viewMode === 'compact'
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50',
              ]"
              @click="viewMode = 'compact'"
            >
              Compact
            </button>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <div v-if="selectedRules.length > 0" class="text-sm text-gray-600 mr-2">
            {{ selectedRules.length }} selected
          </div>
          <div class="relative">
            <Button variant="outline" size="sm" @click="showExportMenu = !showExportMenu">
              <ArrowDownTrayIcon class="h-4 w-4 mr-1" />
              Export
            </Button>
            <div
              v-if="showExportMenu"
              class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200"
            >
              <button
                class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-t-md"
                @click="handleExportCSV"
              >
                Export to CSV
              </button>
              <button
                class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-b-md"
                @click="handleExportJSON"
              >
                Export to JSON
              </button>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- Rules Display (Table, Cards, or Compact) -->
    <Card v-if="viewMode === 'table'">
      <RulesTable
        :rules="paginatedRules"
        :loading="loading"
        :sort-key="sortKey"
        :sort-direction="sortDirection"
        :selected-rules="selectedRules"
        @sort="handleSort"
        @view-rule="$emit('view-rule', $event)"
        @select-rule="handleSelectRule"
        @select-all="handleSelectAll"
      />
    </Card>

    <div v-else-if="viewMode === 'cards'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <RuleCard
        v-for="rule in paginatedRules"
        :key="rule.id"
        :rule="rule"
        :selected="selectedRules.includes(rule.id)"
        @click="$emit('view-rule', rule)"
        @select="handleSelectRule(rule.id, $event)"
      />
    </div>

    <Card v-else-if="viewMode === 'compact'">
      <div class="divide-y divide-gray-200">
        <div
          v-for="rule in paginatedRules"
          :key="rule.id"
          class="p-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
          @click="$emit('view-rule', rule)"
        >
          <div class="flex items-center space-x-4 flex-1">
            <input
              type="checkbox"
              :checked="selectedRules.includes(rule.id)"
              class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              @click.stop
              @change="handleSelectRule(rule.id, $event.target.checked)"
            />
            <span class="text-sm font-medium text-gray-900">#{{ rule.id }}</span>
            <StatusBadge
              :status="rule.action === 'allow' ? 'success' : 'error'"
              :label="rule.action"
            />
            <span class="text-sm text-gray-600">
              {{ formatNetworks(rule.endpoints, 'source') || '—' }} →
              {{ formatNetworks(rule.endpoints, 'destination') || '—' }}
            </span>
          </div>
          <Button variant="ghost" size="sm" @click.stop="$emit('view-rule', rule)">
            View
          </Button>
        </div>
      </div>
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { MagnifyingGlassIcon, ArrowDownTrayIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import StatusBadge from './StatusBadge.vue'
import RulesStats from './RulesStats.vue'
import RulesFilter from './RulesFilter.vue'
import RulesTable from './RulesTable.vue'
import RuleCard from './RuleCard.vue'
import { rulesService } from '@/services/rules'
import { useToast } from '@/composables/useToast'
import { exportRulesToCSV, exportRulesToJSON } from '@/services/export'

const props = defineProps({
  requestId: {
    type: [String, Number],
    required: true,
  },
})

const emit = defineEmits(['view-rule'])

const { error: showError, success: showSuccess } = useToast()

const loading = ref(false)
const rules = ref([])
const stats = ref({})
const searchQuery = ref('')
const filters = ref({
  action: '',
  protocol: '',
  hasFacts: '',
  selfFlow: '',
  anyAny: '',
  ipRange: '',
  portRange: '',
})
const sortKey = ref('id')
const sortDirection = ref('asc')
const currentPage = ref(1)
const pageSize = ref(25)
const totalRules = ref(0)
const viewMode = ref('table')
const selectedRules = ref([])
const showExportMenu = ref(false)

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
}

const handleFilterUpdate = (newFilters) => {
  filters.value = { ...newFilters }
  currentPage.value = 1
}

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
  filters.value = {
    action: '',
    protocol: '',
    hasFacts: '',
    selfFlow: '',
    anyAny: '',
    ipRange: '',
    portRange: '',
  }
  selectedRules.value = []
  currentPage.value = 1
}

const handleSelectRule = (ruleId, checked) => {
  if (checked) {
    if (!selectedRules.value.includes(ruleId)) {
      selectedRules.value.push(ruleId)
    }
  } else {
    selectedRules.value = selectedRules.value.filter((id) => id !== ruleId)
  }
}

const handleSelectAll = (checked) => {
  if (checked) {
    selectedRules.value = paginatedRules.value.map((rule) => rule.id)
  } else {
    selectedRules.value = []
  }
}

const handleExportCSV = () => {
  try {
    const rulesToExport = selectedRules.value.length > 0
      ? filteredRules.value.filter((rule) => selectedRules.value.includes(rule.id))
      : filteredRules.value
    
    if (rulesToExport.length === 0) {
      showError('No rules to export')
      return
    }
    
    exportRulesToCSV(rulesToExport, `rules-export-${new Date().toISOString().split('T')[0]}`)
    showExportMenu.value = false
    showSuccess(`Exported ${rulesToExport.length} rules to CSV`)
  } catch (err) {
    showError(err.message || 'Failed to export rules')
  }
}

const handleExportJSON = () => {
  try {
    const rulesToExport = selectedRules.value.length > 0
      ? filteredRules.value.filter((rule) => selectedRules.value.includes(rule.id))
      : filteredRules.value
    
    if (rulesToExport.length === 0) {
      showError('No rules to export')
      return
    }
    
    exportRulesToJSON(rulesToExport, `rules-export-${new Date().toISOString().split('T')[0]}`)
    showExportMenu.value = false
    showSuccess(`Exported ${rulesToExport.length} rules to JSON`)
  } catch (err) {
    showError(err.message || 'Failed to export rules')
  }
}

const formatNetworks = (endpoints, type) => {
  if (!endpoints || !Array.isArray(endpoints)) return ''
  const networks = endpoints
    .filter((ep) => ep.endpoint_type === type || ep.type === type)
    .map((ep) => ep.network_cidr || ep.cidr)
  return networks.length > 0 ? networks.join(', ') : ''
}

// Close export menu when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.relative')) {
    showExportMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const hasActiveFilters = computed(() => {
  return Object.values(filters.value).some((value) => value !== '') || searchQuery.value !== ''
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
  if (filters.value.action) {
    filtered = filtered.filter((rule) => rule.action === filters.value.action)
  }

  // Protocol filter
  if (filters.value.protocol) {
    filtered = filtered.filter((rule) =>
      rule.services?.some((svc) => svc.protocol?.toLowerCase() === filters.value.protocol)
    )
  }

  // Has Facts filter
  if (filters.value.hasFacts === 'yes') {
    filtered = filtered.filter((rule) => rule.facts && Object.keys(rule.facts).length > 0)
  } else if (filters.value.hasFacts === 'no') {
    filtered = filtered.filter((rule) => !rule.facts || Object.keys(rule.facts).length === 0)
  }

  // Self-Flow filter
  if (filters.value.selfFlow === 'yes') {
    filtered = filtered.filter((rule) => rule.facts?.is_self_flow === true)
  } else if (filters.value.selfFlow === 'no') {
    filtered = filtered.filter((rule) => !rule.facts?.is_self_flow)
  }

  // Any/Any filter
  if (filters.value.anyAny) {
    if (filters.value.anyAny === 'source') {
      filtered = filtered.filter((rule) => rule.facts?.src_is_any === true)
    } else if (filters.value.anyAny === 'destination') {
      filtered = filtered.filter((rule) => rule.facts?.dst_is_any === true)
    } else if (filters.value.anyAny === 'both') {
      filtered = filtered.filter(
        (rule) => rule.facts?.src_is_any === true && rule.facts?.dst_is_any === true
      )
    } else if (filters.value.anyAny === 'none') {
      filtered = filtered.filter(
        (rule) => !rule.facts?.src_is_any && !rule.facts?.dst_is_any
      )
    }
  }

  // IP Range filter (CIDR matching)
  if (filters.value.ipRange) {
    const ipRange = filters.value.ipRange.toLowerCase().trim()
    filtered = filtered.filter((rule) => {
      const endpoints = rule.endpoints || []
      return endpoints.some((ep) => {
        const cidr = (ep.network_cidr || ep.cidr || '').toLowerCase()
        // Simple CIDR matching - check if the filter CIDR contains or is contained by rule CIDR
        // For more precise matching, would need CIDR library
        return cidr.includes(ipRange) || ipRange.includes(cidr.split('/')[0])
      })
    })
  }

  // Port Range filter
  if (filters.value.portRange) {
    const portRange = filters.value.portRange.trim()
    filtered = filtered.filter((rule) => {
      const services = rule.services || []
      return services.some((svc) => {
        const ports = (svc.port_ranges || svc.ports || '').toString()
        // Check if port range matches (simple string matching)
        return ports.includes(portRange)
      })
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
      }
      if (data.summary) {
        stats.value = data.summary
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

