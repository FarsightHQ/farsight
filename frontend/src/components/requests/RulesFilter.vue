<template>
  <Card class="p-4">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-medium text-gray-900">Filters</h3>
      <Button v-if="hasActiveFilters" variant="ghost" size="sm" @click="clearFilters">
        Clear All
      </Button>
    </div>

    <div class="space-y-4">
      <!-- Basic Filters Section -->
      <div>
        <button
          class="flex items-center justify-between w-full mb-2 text-xs font-medium text-gray-700 hover:text-gray-900"
          @click="sections.basic = !sections.basic"
        >
          <span>Basic Filters</span>
          <ChevronDownIcon
            :class="['h-4 w-4 text-gray-500 transition-transform', sections.basic && 'rotate-180']"
          />
        </button>
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-96"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 max-h-96"
          leave-to-class="opacity-0 max-h-0"
        >
          <div v-if="sections.basic" class="space-y-3 pl-2">
            <!-- Action Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-2">Action</label>
              <select
                v-model="localFilters.action"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                @change="updateFilters"
              >
                <option value="">All</option>
                <option
                  v-for="(count, action) in filterMetadata.actionCounts"
                  :key="action"
                  :value="action"
                  :disabled="count === 0"
                >
                  {{ action.charAt(0).toUpperCase() + action.slice(1) }} ({{ count }})
                </option>
              </select>
            </div>

            <!-- Protocol Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-2">Protocol</label>
              <select
                v-model="localFilters.protocol"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                :class="{ 'opacity-50': filterMetadata.protocols.length === 0 }"
                :disabled="filterMetadata.protocols.length === 0"
                @change="updateFilters"
              >
                <option value="">All</option>
                <option
                  v-for="protocol in filterMetadata.protocols"
                  :key="protocol.value"
                  :value="protocol.value"
                  :disabled="protocol.count === 0"
                >
                  {{ protocol.label }} ({{ protocol.count }})
                </option>
              </select>
            </div>

            <!-- Direction Filter -->
            <div v-if="filterMetadata.directions.length > 0">
              <label class="block text-xs font-medium text-gray-700 mb-2">Direction</label>
              <select
                v-model="localFilters.direction"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                @change="updateFilters"
              >
                <option value="">All</option>
                <option
                  v-for="direction in filterMetadata.directions"
                  :key="direction.value"
                  :value="direction.value"
                  :disabled="direction.count === 0"
                >
                  {{ direction.label }} ({{ direction.count }})
                </option>
              </select>
            </div>

            <!-- Request Filter (for global view) -->
            <div v-if="showRequestFilter">
              <label class="block text-xs font-medium text-gray-700 mb-2">Request</label>
              <select
                v-model="localFilters.requestId"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                @change="updateFilters"
              >
                <option :value="null">All Requests</option>
                <option v-for="request in availableRequests" :key="request.id" :value="request.id">
                  {{ request.title || `Request ${request.id}` }}
                  <span v-if="request.external_id"> ({{ request.external_id }})</span>
                </option>
              </select>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Security Filters Section -->
      <div>
        <button
          class="flex items-center justify-between w-full mb-2 text-xs font-medium text-gray-700 hover:text-gray-900"
          @click="sections.security = !sections.security"
        >
          <span>Security Filters</span>
          <ChevronDownIcon
            :class="[
              'h-4 w-4 text-gray-500 transition-transform',
              sections.security && 'rotate-180',
            ]"
          />
        </button>
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-96"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 max-h-96"
          leave-to-class="opacity-0 max-h-0"
        >
          <div v-if="sections.security" class="space-y-3 pl-2">
            <!-- Self-Flow Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-2">Self-Flow</label>
              <select
                v-model="localFilters.selfFlow"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                @change="updateFilters"
              >
                <option value="">All</option>
                <option
                  v-for="(count, value) in filterMetadata.selfFlowCounts"
                  :key="value"
                  :value="value"
                  :disabled="count === 0"
                >
                  {{ value === 'yes' ? 'Yes' : 'No' }} ({{ count }})
                </option>
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
                <option
                  v-for="(count, value) in filterMetadata.anyAnyCounts"
                  :key="value"
                  :value="value"
                  :disabled="count === 0"
                >
                  {{
                    value === 'source'
                      ? 'Source Any'
                      : value === 'destination'
                        ? 'Dest Any'
                        : value === 'both'
                          ? 'Both'
                          : 'None'
                  }}
                  ({{ count }})
                </option>
              </select>
            </div>

            <!-- Public IP Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-2">Public IP</label>
              <select
                v-model="localFilters.publicIP"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                @change="updateFilters"
              >
                <option value="">All</option>
                <option
                  v-for="(count, value) in filterMetadata.publicIPCounts"
                  :key="value"
                  :value="value"
                  :disabled="count === 0"
                >
                  {{
                    value === 'src'
                      ? 'Source Public'
                      : value === 'dst'
                        ? 'Dest Public'
                        : value === 'either'
                          ? 'Either Public'
                          : 'None'
                  }}
                  ({{ count }})
                </option>
              </select>
            </div>

            <!-- Has Issues Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-2">Has Issues</label>
              <select
                v-model="localFilters.hasIssues"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                @change="updateFilters"
              >
                <option value="">All</option>
                <option
                  v-for="(count, value) in filterMetadata.hasIssuesCounts"
                  :key="value"
                  :value="value"
                  :disabled="count === 0"
                >
                  {{ value === 'yes' ? 'Has Issues' : 'Clean Rules' }} ({{ count }})
                </option>
              </select>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Facts Filters Section -->
      <div>
        <button
          class="flex items-center justify-between w-full mb-2 text-xs font-medium text-gray-700 hover:text-gray-900"
          @click="sections.facts = !sections.facts"
        >
          <span>Facts Filters</span>
          <ChevronDownIcon
            :class="['h-4 w-4 text-gray-500 transition-transform', sections.facts && 'rotate-180']"
          />
        </button>
        <Transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="opacity-0 max-h-0"
          enter-to-class="opacity-100 max-h-96"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 max-h-96"
          leave-to-class="opacity-0 max-h-0"
        >
          <div v-if="sections.facts" class="space-y-3 pl-2">
            <!-- Has Facts Filter -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-2">Has Facts</label>
              <select
                v-model="localFilters.hasFacts"
                class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
                @change="updateFilters"
              >
                <option value="">All</option>
                <option
                  v-for="(count, value) in filterMetadata.hasFactsCounts"
                  :key="value"
                  :value="value"
                  :disabled="count === 0"
                >
                  {{ value === 'yes' ? 'Yes' : 'No' }} ({{ count }})
                </option>
              </select>
            </div>
          </div>
        </Transition>
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
import { ref, computed, watch, onMounted } from 'vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import { useRuleFilters } from '@/composables/useRuleFilters'
import { requestsService } from '@/services/requests'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({}),
  },
  rules: {
    type: Array,
    default: () => [],
  },
  showRequestFilter: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:filters'])

// Use composable to extract filter metadata
const rulesRef = computed(() => props.rules || [])
const { filterMetadata } = useRuleFilters(rulesRef)

// Collapsible sections state
const sections = ref({
  basic: true,
  security: true,
  facts: true,
})

const localFilters = ref({
  action: props.filters.action || '',
  protocol: props.filters.protocol || '',
  direction: props.filters.direction || '',
  hasFacts: props.filters.hasFacts || '',
  selfFlow: props.filters.selfFlow || '',
  anyAny: props.filters.anyAny || '',
  publicIP: props.filters.publicIP || '',
  hasIssues: props.filters.hasIssues || '',
  requestId: props.filters.requestId || null,
})

// Available requests for dropdown (only fetch if showRequestFilter is true)
const availableRequests = ref([])
const loadingRequests = ref(false)

const fetchRequests = async () => {
  if (!props.showRequestFilter) return

  loadingRequests.value = true
  try {
    const response = await requestsService.list(0, 1000) // Fetch all requests
    const responseData = response.data || response
    availableRequests.value = Array.isArray(responseData) ? responseData : responseData.data || []
  } catch (err) {
    console.error('Failed to fetch requests:', err)
    availableRequests.value = []
  } finally {
    loadingRequests.value = false
  }
}

onMounted(() => {
  if (props.showRequestFilter) {
    fetchRequests()
  }
})

watch(
  () => props.showRequestFilter,
  newVal => {
    if (newVal && availableRequests.value.length === 0) {
      fetchRequests()
    }
  }
)

watch(
  () => props.filters,
  newFilters => {
    localFilters.value = {
      action: newFilters.action || '',
      protocol: newFilters.protocol || '',
      direction: newFilters.direction || '',
      hasFacts: newFilters.hasFacts || '',
      selfFlow: newFilters.selfFlow || '',
      anyAny: newFilters.anyAny || '',
      publicIP: newFilters.publicIP || '',
      hasIssues: newFilters.hasIssues || '',
      requestId: newFilters.requestId || null,
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
    direction: '',
    hasFacts: '',
    selfFlow: '',
    anyAny: '',
    publicIP: '',
    hasIssues: '',
    requestId: null,
  }
  updateFilters()
}

const hasActiveFilters = computed(() => {
  return Object.values(localFilters.value).some(value => value !== '' && value !== null)
})

const activeFilterCount = computed(() => {
  return Object.values(localFilters.value).filter(value => value !== '' && value !== null).length
})
</script>
