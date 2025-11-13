<template>
  <Modal v-model="modelValue" size="md" @update:modelValue="$emit('update:modelValue', $event)">
    <template #header>
      <h3 class="text-lg font-semibold text-gray-900">Delete Request</h3>
    </template>

    <div class="space-y-4">
      <div class="flex items-start space-x-3">
        <div class="flex-shrink-0">
          <ExclamationTriangleIcon class="h-6 w-6 text-error-500" />
        </div>
        <div class="flex-1">
          <p class="text-sm text-gray-600">
            Are you sure you want to delete this request? This action cannot be undone.
          </p>
        </div>
      </div>

      <div v-if="request" class="bg-gray-50 rounded-lg p-4 space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-700">Title:</span>
          <span class="text-sm text-gray-900">{{ request.title }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-700">ID:</span>
          <span class="text-sm text-gray-900">{{ request.id }}</span>
        </div>
        <div v-if="request.external_id" class="flex items-center justify-between">
          <span class="text-sm font-medium text-gray-700">External ID:</span>
          <span class="text-sm text-gray-900">{{ request.external_id }}</span>
        </div>
      </div>

      <div class="bg-error-50 border border-error-200 rounded-lg p-3">
        <p class="text-sm text-error-800">
          <strong>Warning:</strong> This will permanently delete:
        </p>
        <ul class="mt-2 text-sm text-error-700 list-disc list-inside space-y-1">
          <li>The request record</li>
          <li>All associated firewall rules</li>
          <li>The uploaded CSV file</li>
        </ul>
      </div>
    </div>

    <template #footer>
      <Button variant="outline" @click="$emit('cancel')" :disabled="deleting">
        Cancel
      </Button>
      <Button variant="primary" @click="$emit('confirm')" :disabled="deleting">
        <Spinner v-if="deleting" size="sm" class="mr-2" />
        {{ deleting ? 'Deleting...' : 'Delete Request' }}
      </Button>
    </template>
  </Modal>
</template>

<script setup>
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import Modal from '@/components/ui/Modal.vue'
import Button from '@/components/ui/Button.vue'
import Spinner from '@/components/ui/Spinner.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  request: {
    type: Object,
    default: null,
  },
  deleting: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:modelValue', 'confirm', 'cancel'])
</script>

