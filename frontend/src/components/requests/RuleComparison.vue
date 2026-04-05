<template>
  <Card class="p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-900">Rule Comparison</h3>
      <Button variant="outline" size="sm" @click="$emit('close')">Close</Button>
    </div>

    <div v-if="selectedRules.length < 2" class="text-center py-8">
      <p class="text-gray-600 mb-4">Select at least 2 rules to compare</p>
      <Button variant="primary" @click="$emit('select-rules')">Select Rules</Button>
    </div>

    <div v-else class="space-y-6">
      <!-- Comparison Table -->
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Property
              </th>
              <th
                v-for="rule in selectedRules"
                :key="rule.id"
                class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase"
              >
                Rule #{{ rule.id }}
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr>
              <td class="px-4 py-3 text-sm font-medium text-gray-700">Action</td>
              <td
                v-for="rule in selectedRules"
                :key="rule.id"
                class="px-4 py-3 text-sm"
                :class="getDifferenceClass('action', rule)"
              >
                {{ rule.action }}
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3 text-sm font-medium text-gray-700">Direction</td>
              <td
                v-for="rule in selectedRules"
                :key="rule.id"
                class="px-4 py-3 text-sm"
                :class="getDifferenceClass('direction', rule)"
              >
                {{ rule.direction || '—' }}
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3 text-sm font-medium text-gray-700">Source Networks</td>
              <td
                v-for="rule in selectedRules"
                :key="rule.id"
                class="px-4 py-3 text-sm"
                :class="getDifferenceClass('sources', rule)"
              >
                {{ formatNetworks(rule.endpoints, 'source') || '—' }}
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3 text-sm font-medium text-gray-700">Destination Networks</td>
              <td
                v-for="rule in selectedRules"
                :key="rule.id"
                class="px-4 py-3 text-sm"
                :class="getDifferenceClass('destinations', rule)"
              >
                {{ formatNetworks(rule.endpoints, 'destination') || '—' }}
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3 text-sm font-medium text-gray-700">Services</td>
              <td
                v-for="rule in selectedRules"
                :key="rule.id"
                class="px-4 py-3 text-sm"
                :class="getDifferenceClass('services', rule)"
              >
                {{ formatServices(rule.services) || '—' }}
              </td>
            </tr>
            <tr>
              <td class="px-4 py-3 text-sm font-medium text-gray-700">Has Facts</td>
              <td v-for="rule in selectedRules" :key="rule.id" class="px-4 py-3 text-sm">
                {{ rule.facts ? 'Yes' : 'No' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Export Comparison -->
      <div class="flex justify-end">
        <Button variant="outline" @click="handleExport"> Export Comparison </Button>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import { exportToJSON } from '@/services/export'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  selectedRules: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['close', 'select-rules'])

const { success, error: showError } = useToast()

const formatNetworks = (endpoints, type) => {
  if (!endpoints || !Array.isArray(endpoints)) return ''
  const networks = endpoints
    .filter(ep => ep.endpoint_type === type || ep.type === type)
    .map(ep => ep.network_cidr || ep.cidr)
  return networks.length > 0 ? networks.join(', ') : ''
}

const formatServices = services => {
  if (!services || !Array.isArray(services)) return ''
  return services
    .map(svc => {
      const protocol = (svc.protocol || '').toUpperCase()
      const ports = svc.port_ranges || svc.ports || ''
      return ports ? `${protocol}: ${ports}` : protocol
    })
    .join(', ')
}

const getDifferenceClass = (property, rule) => {
  if (props.selectedRules.length < 2) return ''

  const firstValue = getPropertyValue(props.selectedRules[0], property)
  const currentValue = getPropertyValue(rule, property)

  if (firstValue !== currentValue) {
    return 'bg-yellow-50 text-yellow-900'
  }
  return ''
}

const getPropertyValue = (rule, property) => {
  switch (property) {
    case 'action':
      return rule.action
    case 'direction':
      return rule.direction || ''
    case 'sources':
      return formatNetworks(rule.endpoints, 'source')
    case 'destinations':
      return formatNetworks(rule.endpoints, 'destination')
    case 'services':
      return formatServices(rule.services)
    default:
      return ''
  }
}

const handleExport = () => {
  try {
    const comparisonData = {
      compared_at: new Date().toISOString(),
      rules: props.selectedRules.map(rule => ({
        id: rule.id,
        action: rule.action,
        direction: rule.direction,
        sources: formatNetworks(rule.endpoints, 'source'),
        destinations: formatNetworks(rule.endpoints, 'destination'),
        services: formatServices(rule.services),
        facts: rule.facts,
      })),
    }

    exportToJSON(comparisonData, `rule-comparison-${new Date().toISOString().split('T')[0]}`, true)
    success('Comparison exported successfully')
  } catch (err) {
    showError(err.message || 'Failed to export comparison')
  }
}
</script>
