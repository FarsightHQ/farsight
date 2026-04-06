<template>
  <div class="zone-heatmap h-full w-full min-h-0 overflow-auto bg-gray-100 p-3 sm:p-4">
    <table
      v-if="rowLabels.length > 0"
      class="border-collapse text-xs sm:text-sm mx-auto"
      role="grid"
      :aria-label="ariaLabel"
    >
      <thead>
        <tr>
          <th
            class="sticky left-0 z-20 bg-gray-100 p-1 sm:p-2 text-left font-medium text-gray-600 border border-gray-200 min-w-[4.5rem]"
            scope="col"
          >
            {{ rowAxisLabel }} \\ {{ colAxisLabel }}
          </th>
          <th
            v-for="(c, j) in colLabels"
            :key="'c-' + j"
            scope="col"
            class="p-1 sm:p-2 text-left font-medium text-gray-800 border border-gray-200 bg-white max-w-[8rem] align-bottom"
          >
            <span class="block truncate sm:whitespace-normal break-words leading-tight" :title="c">{{
              c
            }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(r, i) in rowLabels" :key="'r-' + i">
          <th
            scope="row"
            class="sticky left-0 z-10 bg-gray-50 p-1 sm:p-2 text-left font-medium text-gray-800 border border-gray-200 max-w-[10rem]"
          >
            <span class="block truncate sm:whitespace-normal break-words leading-tight" :title="r">{{
              r
            }}</span>
          </th>
          <td
            v-for="(c, j) in colLabels"
            :key="'cell-' + i + '-' + j"
            class="border border-gray-200 p-0 text-center align-middle min-w-[2.5rem]"
          >
            <button
              type="button"
              class="w-full min-h-[2rem] px-1 py-1.5 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500 transition-colors"
              :class="selectedI === i && selectedJ === j ? 'ring-2 ring-inset ring-blue-600' : ''"
              :style="{ backgroundColor: cellColor(matrix[i][j]) }"
              :aria-label="cellAriaLabel(i, j)"
              :aria-pressed="selectedI === i && selectedJ === j"
              @click="onCellClick(i, j)"
            >
              <span class="font-mono text-[11px] sm:text-xs text-gray-900 tabular-nums">
                {{ cellText(matrix[i][j]) }}
              </span>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="text-sm text-gray-500 text-center py-8">No zone pairs in the current graph.</p>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  rowLabels: { type: Array, default: () => [] },
  colLabels: { type: Array, default: () => [] },
  matrix: { type: Array, default: () => [] },
  cellDetail: { type: Array, default: () => [] },
  maxValue: { type: Number, default: 0 },
  metric: { type: String, default: 'rules' },
  groupBy: { type: String, default: 'segment' },
  /** Increment from parent to clear visual selection (e.g. panel Clear). */
  clearStamp: { type: Number, default: 0 },
})

const emit = defineEmits(['cell-select'])

const selectedI = ref(null)
const selectedJ = ref(null)

const rowAxisLabel = computed(() =>
  props.groupBy === 'location' ? 'From (location)' : props.groupBy === 'vlan' ? 'From (VLAN)' : 'From (segment)'
)
const colAxisLabel = computed(() =>
  props.groupBy === 'location' ? 'To (location)' : props.groupBy === 'vlan' ? 'To (VLAN)' : 'To (segment)'
)

const ariaLabel = computed(
  () => `Zone adjacency heat map by ${props.groupBy}, ${props.metric} metric`
)

watch(
  () => [props.matrix, props.rowLabels, props.colLabels],
  () => {
    selectedI.value = null
    selectedJ.value = null
  },
  { deep: true }
)

watch(
  () => props.clearStamp,
  () => {
    selectedI.value = null
    selectedJ.value = null
  }
)

function cellText(v) {
  if (v == null) return '·'
  if (props.metric === 'binary') return v >= 1 ? '1' : '·'
  return String(v)
}

function cellColor(v) {
  if (v == null) return '#e5e7eb'
  if (props.metric === 'binary') return v >= 1 ? '#93c5fd' : '#e5e7eb'
  const max = props.maxValue > 0 ? props.maxValue : 1
  const t = Math.min(1, Number(v) / max)
  const r = Math.round(240 - t * 120)
  const g = Math.round(249 - t * 80)
  const b = Math.round(255 - t * 40)
  return `rgb(${r},${g},${b})`
}

function cellAriaLabel(i, j) {
  const r = props.rowLabels[i]
  const c = props.colLabels[j]
  const v = props.matrix[i]?.[j]
  const detail = props.cellDetail[i]?.[j]
  const extra = detail?.linkCount != null ? `, ${detail.linkCount} edge(s)` : ''
  return `${r} to ${c}, value ${v == null ? 'empty' : v}${extra}`
}

function onCellClick(i, j) {
  const detail = props.cellDetail[i]?.[j]
  if (!detail) {
    if (selectedI.value === i && selectedJ.value === j) {
      selectedI.value = null
      selectedJ.value = null
      emit('cell-select', null)
    }
    return
  }
  if (selectedI.value === i && selectedJ.value === j) {
    selectedI.value = null
    selectedJ.value = null
    emit('cell-select', null)
    return
  }
  selectedI.value = i
  selectedJ.value = j
  emit('cell-select', { rowIndex: i, colIndex: j, detail })
}
</script>
