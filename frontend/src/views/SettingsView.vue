<template>
  <PageFrame
    class="flex-1 min-h-0 flex flex-col"
    :breadcrumb-items="breadcrumbItems"
    title="Settings"
  >
    <div class="max-w-5xl space-y-8">
      <section class="border border-theme-border rounded-lg p-4 space-y-2">
        <h2 class="font-medium">Appearance</h2>
        <p class="text-sm text-theme-text-muted">
          Theme and display preferences will be available here.
        </p>
      </section>

      <section class="border border-theme-border rounded-lg p-4 space-y-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 class="font-medium">Global risky port policy</h2>
            <p class="text-sm text-theme-text-muted mt-1">
              Application-wide list used when analyzing FAR rules (rule detail and security
              analysis). Matches use protocol and port range overlap. Saving replaces the entire
              list.
            </p>
          </div>
          <div class="flex gap-2 shrink-0">
            <Button type="button" variant="secondary" :disabled="loading" @click="addRow">
              Add row
            </Button>
            <Button type="button" :disabled="loading || saving" @click="savePolicy">
              {{ saving ? 'Saving…' : 'Save' }}
            </Button>
          </div>
        </div>

        <p v-if="loadError" class="text-sm text-error-600">{{ loadError }}</p>

        <div v-if="loading" class="text-sm text-theme-text-muted">Loading policy…</div>

        <div v-else class="overflow-x-auto rounded-md border border-theme-border">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="border-b border-theme-border bg-theme-active/15 text-left">
                <th class="p-2 font-medium">Protocol</th>
                <th class="p-2 font-medium w-24">Start</th>
                <th class="p-2 font-medium w-24">End</th>
                <th class="p-2 font-medium min-w-[8rem]">Label</th>
                <th class="p-2 font-medium min-w-[10rem]">Recommendation</th>
                <th class="p-2 font-medium">Severity</th>
                <th class="p-2 font-medium w-20">On</th>
                <th class="p-2 font-medium w-16" />
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, index) in rows"
                :key="row._key"
                class="border-b border-theme-border last:border-0 align-top"
              >
                <td class="p-2">
                  <select
                    v-model="row.protocol"
                    class="input py-1.5 text-sm w-full min-w-[5.5rem]"
                    :aria-label="`Protocol for row ${index + 1}`"
                  >
                    <option value="tcp">tcp</option>
                    <option value="udp">udp</option>
                    <option value="both">both</option>
                  </select>
                </td>
                <td class="p-2">
                  <input
                    v-model.number="row.port_start"
                    type="number"
                    min="1"
                    max="65535"
                    class="input py-1.5 text-sm w-full"
                    :aria-label="`Start port for row ${index + 1}`"
                  />
                </td>
                <td class="p-2">
                  <input
                    v-model.number="row.port_end"
                    type="number"
                    min="1"
                    max="65535"
                    class="input py-1.5 text-sm w-full"
                    :aria-label="`End port for row ${index + 1}`"
                  />
                </td>
                <td class="p-2">
                  <input
                    v-model="row.label"
                    type="text"
                    class="input py-1.5 text-sm w-full"
                    :aria-label="`Label for row ${index + 1}`"
                  />
                </td>
                <td class="p-2">
                  <input
                    v-model="row.recommendation"
                    type="text"
                    class="input py-1.5 text-sm w-full"
                    placeholder="Optional"
                    :aria-label="`Recommendation for row ${index + 1}`"
                  />
                </td>
                <td class="p-2">
                  <select
                    v-model="row.severity"
                    class="input py-1.5 text-sm w-full min-w-[6rem]"
                    :aria-label="`Severity for row ${index + 1}`"
                  >
                    <option value="info">info</option>
                    <option value="warning">warning</option>
                    <option value="high">high</option>
                  </select>
                </td>
                <td class="p-2 text-center">
                  <input
                    v-model="row.enabled"
                    type="checkbox"
                    class="rounded border-theme-border"
                    :aria-label="`Enabled for row ${index + 1}`"
                  />
                </td>
                <td class="p-2">
                  <Button type="button" variant="ghost" class="!px-2" @click="removeRow(index)">
                    Remove
                  </Button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="!loading && rows.length === 0" class="text-sm text-theme-text-muted">
          No entries yet. Add rows for ports that should trigger recommendations or issues during
          analysis. Admins need the <code class="text-xs">admin</code> role in Keycloak to save
          changes.
        </p>
      </section>
    </div>
  </PageFrame>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import PageFrame from '@/components/layout/PageFrame.vue'
import Button from '@/components/ui/Button.vue'
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
      showToast('You need the admin role in Keycloak to update global policy.', 'error', 5000)
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
