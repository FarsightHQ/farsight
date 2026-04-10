<template>
  <div class="w-full overflow-x-auto rounded-md border border-theme-border-default">
    <table class="w-full min-w-[1100px] table-fixed divide-y divide-theme-border-default">
      <colgroup>
        <col class="w-12" />
        <col class="w-14" />
        <col class="w-[6.25rem]" />
        <col class="w-24" />
        <col class="w-24" />
        <col class="w-[22rem]" />
        <col />
        <col class="w-28" />
        <col class="w-[5.25rem]" />
      </colgroup>
      <thead class="bg-theme-content">
        <tr>
          <th
            class="px-2 py-2 text-center text-xs font-medium text-theme-text-muted tracking-wider normal-case"
          >
            enabled
          </th>
          <th
            class="px-2 py-2 text-center text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Id
          </th>
          <th
            class="px-2 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Protocol
          </th>
          <th
            class="px-2 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Start
          </th>
          <th
            class="px-2 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            End
          </th>
          <th
            class="px-2 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Label
          </th>
          <th
            class="px-2 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider min-w-0"
          >
            Recommendation
          </th>
          <th
            class="px-2 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Severity
          </th>
          <th
            class="px-2 py-2 text-right text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Actions
          </th>
        </tr>
      </thead>
      <tbody class="bg-theme-card divide-y divide-theme-border-default">
        <template v-if="loading">
          <tr v-for="i in 5" :key="`sk-${i}`">
            <td v-for="c in 9" :key="c" class="px-2 py-2">
              <div class="h-4 bg-theme-active/30 rounded animate-pulse w-full max-w-[8rem]" />
            </td>
          </tr>
        </template>
        <template v-else>
          <tr
            v-for="(row, index) in rows"
            :key="row._key"
            class="hover:bg-theme-hover transition-colors align-top"
          >
            <td class="px-2 py-2 text-center">
              <input
                v-model="row.enabled"
                type="checkbox"
                class="rounded border-theme-border-default"
                :aria-label="`Enabled for rule ${displayRuleId(row, index)}`"
              />
            </td>
            <td
              class="px-2 py-2 text-center text-sm tabular-nums text-theme-text-content"
              :title="row.id != null ? undefined : 'Saved rows use database id; new rows show list position until save'"
            >
              {{ displayRuleId(row, index) }}
            </td>
            <td class="px-2 py-2">
              <select
                v-model="row.protocol"
                class="input py-1 text-xs w-full min-w-[5.25rem]"
                :aria-label="`Protocol for row ${displayRuleId(row, index)}`"
              >
                <option value="tcp">tcp</option>
                <option value="udp">udp</option>
                <option value="both">both</option>
              </select>
            </td>
            <td class="px-2 py-2">
              <input
                v-model.number="row.port_start"
                type="number"
                min="1"
                max="65535"
                size="5"
                class="input py-1 text-xs w-full min-w-[5.5ch] max-w-full tabular-nums box-border"
                :aria-label="`Start port for rule ${displayRuleId(row, index)}`"
              />
            </td>
            <td class="px-2 py-2">
              <input
                v-model.number="row.port_end"
                type="number"
                min="1"
                max="65535"
                size="5"
                class="input py-1 text-xs w-full min-w-[5.5ch] max-w-full tabular-nums box-border"
                :aria-label="`End port for rule ${displayRuleId(row, index)}`"
              />
            </td>
            <td class="px-2 py-2 min-w-[22rem]">
              <input
                v-model="row.label"
                type="text"
                class="input py-1 text-xs w-full min-w-0"
                :aria-label="`Label for rule ${displayRuleId(row, index)}`"
              />
            </td>
            <td class="px-2 py-2 min-w-0 w-full">
              <input
                v-model="row.recommendation"
                type="text"
                class="input py-1 text-sm w-full min-w-0"
                :aria-label="`Recommendation for rule ${displayRuleId(row, index)}`"
              />
            </td>
            <td class="px-2 py-2 min-w-0">
              <select
                v-model="row.severity"
                class="input py-1 text-xs w-full max-w-full min-w-0"
                :aria-label="`Severity for rule ${displayRuleId(row, index)}`"
              >
                <option value="info">info</option>
                <option value="warning">warning</option>
                <option value="high">high</option>
              </select>
            </td>
            <td class="px-2 py-2 text-right whitespace-nowrap">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                class="!px-2"
                @click="$emit('remove', index)"
              >
                Remove
              </Button>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import Button from '@/components/ui/Button.vue'

/** @param {{ id?: number }} row @param {number} index */
function displayRuleId(row, index) {
  return row.id != null ? row.id : index + 1
}

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  rows: {
    type: Array,
    required: true,
  },
})

defineEmits(['remove'])
</script>
