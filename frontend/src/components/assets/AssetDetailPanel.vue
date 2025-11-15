<template>
  <div class="space-y-3">
    <!-- Network Information -->
    <Card class="p-4">
      <h3 class="text-sm font-semibold text-gray-900 mb-3">Network Information</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label class="text-xs font-medium text-gray-700">Segment</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.segment || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Subnet</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.subnet || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Gateway</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.gateway || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">VLAN</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.vlan || '—' }}</p>
        </div>
      </div>
    </Card>

    <!-- System Information -->
    <Card class="p-4">
      <h3 class="text-sm font-semibold text-gray-900 mb-3">System Information</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label class="text-xs font-medium text-gray-700">OS Name</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.os_name || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">OS Version</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.os_version || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">App Version</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.app_version || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">DB Version</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.db_version || '—' }}</p>
        </div>
      </div>
    </Card>

    <!-- Hardware Resources -->
    <Card class="p-4">
      <h3 class="text-sm font-semibold text-gray-900 mb-3">Hardware Resources</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <label class="text-xs font-medium text-gray-700">vCPU</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.vcpu || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Memory</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.memory || '—' }}</p>
        </div>
      </div>
    </Card>

    <!-- Metadata -->
    <Card class="p-4">
      <h3 class="text-sm font-semibold text-gray-900 mb-3">Metadata</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label class="text-xs font-medium text-gray-700">Hostname</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.hostname || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">VM Display Name</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.vm_display_name || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Environment</label>
          <p class="mt-0.5">
            <Badge v-if="asset.environment && String(asset.environment).trim()" :label="String(asset.environment).trim()" variant="info" />
            <span v-else class="text-xs text-gray-400">—</span>
          </p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Location</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.location || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Availability</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.availability || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">ITM ID</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.itm_id || '—' }}</p>
        </div>
      </div>
    </Card>

    <!-- Compliance & Security -->
    <Card class="p-4">
      <h3 class="text-sm font-semibold text-gray-900 mb-3">Compliance & Security</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label class="text-xs font-medium text-gray-700">Tool Update</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.tool_update || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">DMZ/MZ</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.dmz_mz || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Confidentiality</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.confidentiality || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Integrity</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.integrity || '—' }}</p>
        </div>
      </div>
    </Card>

    <!-- Timestamps -->
    <Card class="p-4">
      <h3 class="text-sm font-semibold text-gray-900 mb-3">Timestamps</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label class="text-xs font-medium text-gray-700">Created At</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ formatDate(asset.created_at) }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Updated At</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ formatDate(asset.updated_at) }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Version</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.version || '—' }}</p>
        </div>
        <div>
          <label class="text-xs font-medium text-gray-700">Data Source</label>
          <p class="mt-0.5 text-sm text-gray-900">{{ asset.data_source || '—' }}</p>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup>
import Card from '@/components/ui/Card.vue'
import Badge from '@/components/ui/Badge.vue'

const props = defineProps({
  asset: {
    type: Object,
    required: true,
  },
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
</script>

