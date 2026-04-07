<template>
  <Card
    class="p-4 hover:shadow-lg transition-shadow cursor-pointer"
    :class="{ 'ring-2 ring-primary-500': selected }"
    @click="$emit('click', rule)"
  >
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center space-x-2">
        <input
          type="checkbox"
          :checked="selected"
          class="rounded border-theme-border-default text-primary-600 focus:ring-primary-500"
          @click.stop
          @change="$emit('select', $event.target.checked)"
        />
        <h3 class="text-lg font-semibold text-theme-text-content">Rule #{{ rule.id }}</h3>
      </div>
      <StatusBadge :status="rule.action === 'allow' ? 'success' : 'error'" :label="rule.action" />
    </div>

    <div class="space-y-2 text-sm">
      <div class="flex items-center space-x-2">
        <span class="text-theme-text-muted">Source:</span>
        <span class="text-theme-text-content font-mono text-xs">
          {{ formatNetworks(rule.endpoints, 'source') || '—' }}
        </span>
      </div>
      <div class="flex items-center space-x-2">
        <span class="text-theme-text-muted">Dest:</span>
        <span class="text-theme-text-content font-mono text-xs">
          {{ formatNetworks(rule.endpoints, 'destination') || '—' }}
        </span>
      </div>
      <div class="flex items-center space-x-2">
        <span class="text-theme-text-muted">Services:</span>
        <span class="text-theme-text-content">{{ formatServices(rule.services) || '—' }}</span>
      </div>
    </div>

    <div class="mt-3 pt-3 border-t border-theme-border-default flex items-center justify-between">
      <RuleFactsIndicator :facts="rule.facts" />
      <span class="text-xs text-theme-text-muted">{{ formatDate(rule.created_at) }}</span>
    </div>
  </Card>
</template>

<script setup>
import Card from '@/components/ui/Card.vue'
import StatusBadge from '@/components/ui/StatusBadge.vue'
import RuleFactsIndicator from './RuleFactsIndicator.vue'

const props = defineProps({
  rule: {
    type: Object,
    required: true,
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['click', 'select'])

const formatNetworks = (endpoints, type) => {
  if (!endpoints || !Array.isArray(endpoints)) return ''
  const networks = endpoints
    .filter(ep => ep.endpoint_type === type || ep.type === type)
    .map(ep => ep.network_cidr || ep.cidr)
  if (networks.length === 0) return ''
  if (networks.length > 2) {
    return `${networks.slice(0, 2).join(', ')} +${networks.length - 2} more`
  }
  return networks.join(', ')
}

const formatServices = services => {
  if (!services || !Array.isArray(services)) return ''
  if (services.length === 0) return ''
  if (services.length > 2) {
    return `${services
      .slice(0, 2)
      .map(s => s.protocol?.toUpperCase())
      .join(', ')} +${services.length - 2} more`
  }
  return services.map(s => s.protocol?.toUpperCase()).join(', ')
}

const formatDate = dateString => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
</script>
