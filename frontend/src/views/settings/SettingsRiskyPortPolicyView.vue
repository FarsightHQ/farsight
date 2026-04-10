<template>
  <PageFrame
    class="flex-1 min-h-0 flex flex-col"
    :breadcrumb-items="breadcrumbItems"
    title="Risky port policy"
    subtitle="Application-wide list used when analyzing FAR rules. The seeded baseline reflects common industry guidance; adjust it for your organization. Matches use protocol and port range overlap. Saving replaces the entire list."
  >
    <template #actions>
      <Button type="button" variant="secondary" :disabled="loading" @click="addRow">
        Add row
      </Button>
      <Button type="button" :disabled="loading || saving" @click="savePolicy">
        {{ saving ? 'Saving…' : 'Save' }}
      </Button>
    </template>

    <div class="w-full min-w-0 space-y-4">
      <p v-if="loadError" class="text-sm text-error-600">{{ loadError }}</p>

      <RiskyPortPolicyTable :loading="loading" :rows="rows" @remove="removeRow" />

      <p v-if="!loading && rows.length === 0" class="text-sm text-theme-text-muted">
        No entries yet. Add rows for ports that should trigger recommendations or issues during
        analysis. Saving requires a platform admin role (<code class="text-xs">admin</code> or
        <code class="text-xs">farsight-admin</code>) in Keycloak.
      </p>
    </div>
  </PageFrame>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import PageFrame from '@/components/layout/PageFrame.vue'
import Button from '@/components/ui/Button.vue'
import RiskyPortPolicyTable from '@/components/settings/RiskyPortPolicyTable.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'
import { useToast } from '@/composables/useToast'
import { riskyPortPolicyService } from '@/services/riskyPortPolicy'

const { breadcrumbItems } = usePageBreadcrumbs()
const { showToast } = useToast()

const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
/** @type {import('vue').Ref<Array<Record<string, unknown> & { _key: string }>>} */
const rows = ref([])

let keySeq = 0
function nextKey() {
  keySeq += 1
  return `row-${keySeq}`
}

function emptyRow() {
  return {
    _key: nextKey(),
    protocol: 'tcp',
    port_start: 22,
    port_end: 22,
    label: '',
    recommendation: '',
    severity: 'warning',
    enabled: true,
  }
}

function addRow() {
  rows.value.push(emptyRow())
}

function removeRow(index) {
  rows.value.splice(index, 1)
}

async function loadPolicy() {
  loading.value = true
  loadError.value = ''
  try {
    const list = await riskyPortPolicyService.list()
    rows.value = list.map(e => ({
      _key: nextKey(),
      protocol: e.protocol,
      port_start: e.port_start,
      port_end: e.port_end,
      label: e.label,
      recommendation: e.recommendation ?? '',
      severity: e.severity,
      enabled: e.enabled,
    }))
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || 'Could not load risky port policy.'
    loadError.value = typeof msg === 'string' ? msg : 'Could not load risky port policy.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

function validateRows() {
  for (let i = 0; i < rows.value.length; i += 1) {
    const r = rows.value[i]
    const label = String(r.label || '').trim()
    if (!label) {
      showToast(`Row ${i + 1}: label is required`, 'error')
      return null
    }
    const ps = Number(r.port_start)
    const pe = Number(r.port_end)
    if (!Number.isInteger(ps) || ps < 1 || ps > 65535) {
      showToast(`Row ${i + 1}: invalid start port`, 'error')
      return null
    }
    if (!Number.isInteger(pe) || pe < 1 || pe > 65535) {
      showToast(`Row ${i + 1}: invalid end port`, 'error')
      return null
    }
    if (pe < ps) {
      showToast(`Row ${i + 1}: end port must be >= start port`, 'error')
      return null
    }
  }
  return true
}

async function savePolicy() {
  if (validateRows() === null) return
  saving.value = true
  try {
    const entries = rows.value.map((r, index) => ({
      protocol: r.protocol,
      port_start: Number(r.port_start),
      port_end: Number(r.port_end),
      label: String(r.label).trim(),
      recommendation: String(r.recommendation || '').trim() || null,
      severity: r.severity,
      enabled: Boolean(r.enabled),
      sort_order: index,
    }))
    const saved = await riskyPortPolicyService.replace(entries)
    rows.value = saved.map(e => ({
      _key: nextKey(),
      protocol: e.protocol,
      port_start: e.port_start,
      port_end: e.port_end,
      label: e.label,
      recommendation: e.recommendation ?? '',
      severity: e.severity,
      enabled: e.enabled,
    }))
    showToast('Risky port policy saved', 'success')
  } catch (e) {
    const status = e?.response?.status
    const detail = e?.response?.data?.detail
    if (status === 403) {
      showToast(
        'You need a platform admin role in Keycloak (admin or farsight-admin) to update global policy.',
        'error',
        6000
      )
    } else if (typeof detail === 'string') {
      showToast(detail, 'error', 5000)
    } else {
      showToast('Failed to save policy', 'error')
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadPolicy()
})
</script>
