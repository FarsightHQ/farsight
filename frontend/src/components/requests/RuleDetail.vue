<template>
  <div v-if="rule" class="space-y-6">
    <!-- Rule Header -->
    <Card class="p-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">Rule #{{ rule.id }}</h2>
          <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600">
            <StatusBadge
              :status="rule.action === 'allow' ? 'success' : 'error'"
              :label="rule.action"
            />
            <span v-if="rule.direction">Direction: {{ rule.direction }}</span>
            <span>Created: {{ formatDate(rule.created_at) }}</span>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            :disabled="!hasNetworkData"
            :title="!hasNetworkData ? 'This rule has no network data to visualize' : 'Visualize network topology'"
            @click="handleVisualize"
          >
            Visualize
          </Button>
          <Button variant="outline" size="sm" @click="handleBack">
            Back to Rules
          </Button>
        </div>
      </div>
    </Card>

    <!-- 2-Column Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left Column: Network Endpoints and Services -->
      <div class="space-y-6">
    <!-- Endpoints Section -->
    <Card class="p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Network Endpoints</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Source Networks -->
        <div>
          <h4 class="text-sm font-medium text-gray-700 mb-3 flex items-center">
            <ArrowRightIcon class="h-5 w-5 mr-2 text-info-600" />
            Source Networks
          </h4>
          <div class="space-y-2">
            <div
              v-for="(endpoint, idx) in sourceEndpoints"
              :key="idx"
              class="p-3 bg-gray-50 rounded-lg border border-gray-200 flex items-center justify-between"
              :title="endpoint.network_cidr || endpoint.cidr"
            >
              <div class="flex flex-col">
                <code class="text-sm font-mono text-gray-900">
                  {{ formatCidrToRange(endpoint.network_cidr || endpoint.cidr) }}
                </code>
                <span 
                  v-if="endpoint.hostname"
                  class="text-xs text-gray-500 mt-1"
                >
                  {{ endpoint.hostname }}
                </span>
              </div>
              <button
                @click="copyToClipboard(endpoint.network_cidr || endpoint.cidr)"
                class="text-gray-400 hover:text-gray-600"
                title="Copy CIDR to clipboard"
              >
                <DocumentDuplicateIcon class="h-4 w-4" />
              </button>
            </div>
            <p v-if="sourceEndpoints.length === 0" class="text-sm text-gray-500">No source networks</p>
          </div>
        </div>

        <!-- Destination Networks -->
        <div>
          <h4 class="text-sm font-medium text-gray-700 mb-3 flex items-center">
            <ArrowLeftIcon class="h-5 w-5 mr-2 text-warning-600" />
            Destination Networks
          </h4>
          <div class="space-y-2">
            <div
              v-for="(endpoint, idx) in destinationEndpoints"
              :key="idx"
              class="p-3 bg-gray-50 rounded-lg border border-gray-200 flex items-center justify-between"
              :title="endpoint.network_cidr || endpoint.cidr"
            >
              <div class="flex flex-col">
                <code class="text-sm font-mono text-gray-900">
                  {{ formatCidrToRange(endpoint.network_cidr || endpoint.cidr) }}
                </code>
                <span 
                  v-if="endpoint.hostname"
                  class="text-xs text-gray-500 mt-1"
                >
                  {{ endpoint.hostname }}
                </span>
              </div>
              <button
                @click="copyToClipboard(endpoint.network_cidr || endpoint.cidr)"
                class="text-gray-400 hover:text-gray-600"
                title="Copy CIDR to clipboard"
              >
                <DocumentDuplicateIcon class="h-4 w-4" />
              </button>
            </div>
            <p v-if="destinationEndpoints.length === 0" class="text-sm text-gray-500">
              No destination networks
            </p>
          </div>
        </div>
      </div>
    </Card>

    <!-- Services Section -->
    <Card class="p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Services</h3>
      <div class="space-y-3">
        <div
          v-for="(service, idx) in rule.services"
          :key="idx"
          class="p-4 bg-gray-50 rounded-lg border border-gray-200"
        >
          <div class="flex items-center justify-between">
            <div>
              <span class="text-sm font-medium text-gray-700 uppercase">{{ service.protocol }}</span>
              <span class="text-sm text-gray-600 ml-2">{{ formatPortRanges(service.port_ranges || service.ports) }}</span>
            </div>
            <button
              @click="copyToClipboard(`${service.protocol}:${formatPortRanges(service.port_ranges || service.ports)}`)"
              class="text-gray-400 hover:text-gray-600"
              title="Copy to clipboard"
            >
              <DocumentDuplicateIcon class="h-4 w-4" />
            </button>
          </div>
        </div>
        <p v-if="!rule.services || rule.services.length === 0" class="text-sm text-gray-500">
          No services defined
        </p>
      </div>
    </Card>
      </div>

      <!-- Right Column: Related Info, Major Facts, Detailed Facts -->
      <div class="space-y-6">
    <!-- Related Information -->
    <Card class="p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Related Information</h3>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="font-medium text-gray-700">Request ID:</span>
          <span class="text-gray-600">{{ rule.request_id || requestId || 'N/A' }}</span>
        </div>
        <div v-if="rule.canonical_hash" class="flex justify-between">
          <span class="font-medium text-gray-700">Canonical Hash:</span>
          <code class="text-xs font-mono text-gray-600">{{ rule.canonical_hash }}</code>
        </div>
      </div>
    </Card>

        <!-- Major Facts Section -->
        <Card class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Major Facts</h3>
          <RuleFacts :facts="rule.facts" :show-only-major="true" />
        </Card>

        <!-- Detailed Facts Section -->
        <Card class="p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Detailed Facts</h3>
          <RuleFacts :facts="rule.facts" :show-only-detailed="true" />
        </Card>
      </div>
    </div>
  </div>

  <!-- Loading State -->
  <div v-else-if="loading" class="space-y-6">
    <div class="h-8 bg-gray-200 rounded animate-pulse w-1/3"></div>
    <div class="grid grid-cols-2 gap-4">
      <div v-for="i in 4" :key="i" class="h-24 bg-gray-200 rounded animate-pulse"></div>
    </div>
  </div>

  <!-- Error State -->
  <Card v-else class="p-6">
    <div class="text-center py-12">
      <p class="text-gray-600">Rule not found</p>
    </div>
  </Card>
</template>

<script setup>
import { computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ArrowRightIcon,
  ArrowLeftIcon,
  DocumentDuplicateIcon,
} from '@heroicons/vue/24/outline'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import StatusBadge from './StatusBadge.vue'
import RuleFacts from './RuleFacts.vue'
import { useToast } from '@/composables/useToast'
import { formatCidrToRange } from '@/utils/ipUtils'
import { formatPortRanges } from '@/utils/portUtils'
import { useAssetCache } from '@/composables/useAssetCache'

const props = defineProps({
  rule: {
    type: Object,
    default: null,
  },
  requestId: {
    type: [String, Number],
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['back', 'visualize'])

const router = useRouter()
const route = useRoute()
const { success } = useToast()

// Asset cache for fetching hostnames
const { fetchAssetsForEndpoints, getAssetForCidr, cacheVersion } = useAssetCache()

// Base endpoint filters (not reactive to cache)
const sourceEndpointsBase = computed(() => {
  if (!props.rule?.endpoints) return []
  return props.rule.endpoints.filter(
    (ep) => ep.endpoint_type === 'source' || ep.type === 'source'
  )
})

const destinationEndpointsBase = computed(() => {
  if (!props.rule?.endpoints) return []
  return props.rule.endpoints.filter(
    (ep) => ep.endpoint_type === 'destination' || ep.type === 'destination'
  )
})

// Computed properties with asset information that reactively update when cache changes
const sourceEndpoints = computed(() => {
  // Access cacheVersion to track changes
  const _ = cacheVersion.value
  
  return sourceEndpointsBase.value.map((ep) => {
    const cidr = ep.network_cidr || ep.cidr
    const asset = getAssetForCidr(cidr)
    return {
      ...ep,
      asset: asset || null,
      hostname: asset?.hostname || null,
      segment: asset?.segment || null,
      vlan: asset?.vlan || null,
      os_name: asset?.os_name || null,
    }
  })
})

const destinationEndpoints = computed(() => {
  // Access cacheVersion to track changes
  const _ = cacheVersion.value
  
  return destinationEndpointsBase.value.map((ep) => {
    const cidr = ep.network_cidr || ep.cidr
    const asset = getAssetForCidr(cidr)
    return {
      ...ep,
      asset: asset || null,
      hostname: asset?.hostname || null,
      segment: asset?.segment || null,
      vlan: asset?.vlan || null,
      os_name: asset?.os_name || null,
    }
  })
})

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    success('Copied to clipboard')
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

// Check if rule has network data for visualization
const hasNetworkData = computed(() => {
  if (!props.rule) return false
  
  // Check if rule has endpoints array with source or destination entries
  const hasEndpoints = props.rule.endpoints && Array.isArray(props.rule.endpoints) && props.rule.endpoints.length > 0
  
  // Rule needs at least endpoints to visualize
  return hasEndpoints
})

// Handle visualize button click
const handleVisualize = () => {
  if (!hasNetworkData.value) {
    console.warn('[RuleDetail] Rule has no network data for visualization:', props.rule?.id)
    // Still emit the event - let the modal handle showing appropriate message
  }
  emit('visualize', props.rule)
}

// Handle back button click - context-aware navigation
const handleBack = () => {
  // If in a route context (not inline), use router navigation
  if (route?.params?.ruleId || route?.params?.id) {
    const requestId = route.params.requestId || props.requestId
    if (requestId) {
      // From nested route: go back to request detail page
      router.push(`/requests/${requestId}`)
    } else {
      // From standalone route: go back to all rules
      router.push('/rules')
    }
  } else {
    // Fallback for inline usage (shouldn't happen after this change)
    emit('back')
  }
}

// Fetch asset info when rule changes
watch(
  () => props.rule,
  async (newRule) => {
    if (!newRule || !newRule.endpoints) return
    
    await fetchAssetsForEndpoints(newRule.endpoints)
  },
  { immediate: true }
)

// Also fetch on mount
onMounted(async () => {
  if (props.rule && props.rule.endpoints) {
    await fetchAssetsForEndpoints(props.rule.endpoints)
  }
})
</script>

