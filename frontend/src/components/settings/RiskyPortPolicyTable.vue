<template>
  <div class="w-full overflow-x-auto rounded-md border border-theme-border-default">
    <table class="min-w-full divide-y divide-theme-border-default">
      <thead class="bg-theme-content">
        <tr>
          <th
            class="px-4 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Protocol
          </th>
          <th
            class="px-4 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider w-24"
          >
            Start
          </th>
          <th
            class="px-4 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider w-24"
          >
            End
          </th>
          <th
            class="px-4 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider min-w-[8rem]"
          >
            Label
          </th>
          <th
            class="px-4 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider min-w-[14rem]"
          >
            Recommendation
          </th>
          <th
            class="px-4 py-2 text-left text-xs font-medium text-theme-text-muted uppercase tracking-wider"
          >
            Severity
          </th>
          <th
            class="px-4 py-2 text-center text-xs font-medium text-theme-text-muted uppercase tracking-wider w-16"
          >
            On
          </th>
          <th
            class="px-4 py-2 text-right text-xs font-medium text-theme-text-muted uppercase tracking-wider w-24"
          >
            Actions
          </th>
        </tr>
      </thead>
      <tbody class="bg-theme-card divide-y divide-theme-border-default">
        <template v-if="loading">
          <tr v-for="i in 5" :key="`sk-${i}`">
            <td v-for="c in 8" :key="c" class="px-4 py-2">
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
            <td class="px-4 py-2">
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
            <td class="px-4 py-2">
              <input
                v-model.number="row.port_start"
                type="number"
                min="1"
                max="65535"
                class="input py-1.5 text-sm w-full"
                :aria-label="`Start port for row ${index + 1}`"
              />
            </td>
            <td class="px-4 py-2">
              <input
                v-model.number="row.port_end"
                type="number"
                min="1"
                max="65535"
                class="input py-1.5 text-sm w-full"
                :aria-label="`End port for row ${index + 1}`"
              />
            </td>
            <td class="px-4 py-2">
              <input
                v-model="row.label"
                type="text"
                class="input py-1.5 text-sm w-full"
                :aria-label="`Label for row ${index + 1}`"
              />
            </td>
            <td class="px-4 py-2">
              <input
                v-model="row.recommendation"
                type="text"
                class="input py-1.5 text-sm w-full"
                :aria-label="`Recommendation for row ${index + 1}`"
              />
            </td>
            <td class="px-4 py-2">
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
            <td class="px-4 py-2 text-center">
              <input
                v-model="row.enabled"
                type="checkbox"
                class="rounded border-theme-border-default"
                :aria-label="`Enabled for row ${index + 1}`"
              />
            </td>
            <td class="px-4 py-2 text-right whitespace-nowrap">
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
