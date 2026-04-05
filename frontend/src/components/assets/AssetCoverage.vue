<template>
  <Card class="p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Rule Coverage</h3>

    <div v-if="loading" class="space-y-4">
      <div class="h-20 bg-gray-200 rounded animate-pulse"></div>
    </div>

    <div v-else-if="error" class="text-center py-8">
      <p class="text-sm text-error-600">{{ error }}</p>
    </div>

    <div v-else class="space-y-4">
      <!-- Coverage Statistics -->
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-sm text-gray-600">Rules as Source</div>
          <div class="text-2xl font-bold text-gray-900 mt-1">{{ sourceRulesCount }}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
          <div class="text-sm text-gray-600">Rules as Destination</div>
          <div class="text-2xl font-bold text-gray-900 mt-1">{{ destinationRulesCount }}</div>
        </div>
      </div>

      <!-- Source Rules -->
      <div v-if="sourceRules.length > 0">
        <h4 class="text-sm font-medium text-gray-700 mb-2">Source Rules</h4>
        <div class="space-y-2">
          <div
            v-for="rule in sourceRules"
            :key="rule.id"
            class="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="text-sm font-medium text-gray-900">Rule #{{ rule.id }}</span>
                <span class="ml-2 text-xs text-gray-500">{{ rule.action }}</span>
              </div>
              <Button variant="ghost" size="sm">View</Button>
            </div>
          </div>
        </div>
      </div>

      <!-- Destination Rules -->
      <div v-if="destinationRules.length > 0">
        <h4 class="text-sm font-medium text-gray-700 mb-2 mt-4">Destination Rules</h4>
        <div class="space-y-2">
          <div
            v-for="rule in destinationRules"
            :key="rule.id"
            class="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 cursor-pointer"
            @click="$emit('view-rule', rule)"
          >
            <div class="flex items-center justify-between">
              <div>
                <span class="text-sm font-medium text-gray-900">Rule #{{ rule.id }}</span>
                <span class="ml-2 text-xs text-gray-500">{{ rule.action }}</span>
              </div>
              <Button variant="ghost" size="sm">View</Button>
            </div>
          </div>
        </div>
      </div>

      <!-- No Coverage -->
      <div
        v-if="sourceRules.length === 0 && destinationRules.length === 0"
        class="text-center py-8"
      >
        <p class="text-sm text-gray-500">This asset is not referenced in any firewall rules</p>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'

const props = defineProps({
  sourceRules: {
    type: Array,
    default: () => [],
  },
  destinationRules: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['view-rule'])

const sourceRulesCount = computed(() => props.sourceRules.length)
const destinationRulesCount = computed(() => props.destinationRules.length)
</script>
