<template>
  <div v-if="facts" class="flex items-center space-x-1">
    <!-- Self-Flow Indicator -->
    <span
      v-if="facts.is_self_flow"
      class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-error-100 text-error-800"
      title="Self-flow detected"
    >
      <ArrowPathIcon class="h-3 w-3 mr-1" />
      Self
    </span>

    <!-- Any/Any Indicators -->
    <span
      v-if="facts.src_is_any"
      class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-warning-100 text-warning-800"
      title="Source is any (0.0.0.0/0)"
    >
      Any Src
    </span>
    <span
      v-if="facts.dst_is_any"
      class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-warning-100 text-warning-800"
      title="Destination is any (0.0.0.0/0)"
    >
      Any Dst
    </span>

    <!-- Public IP Indicators -->
    <span
      v-if="facts.src_has_public"
      class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-info-100 text-info-800"
      title="Contains public source IPs"
    >
      Public
    </span>

    <!-- Clean Indicator -->
    <span
      v-if="!hasIssues"
      class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-success-100 text-success-800"
      title="No issues detected"
    >
      <CheckCircleIcon class="h-3 w-3 mr-1" />
      Clean
    </span>

    <!-- No Facts -->
    <span v-else-if="!facts" class="text-xs text-gray-400" title="No facts computed"> — </span>
  </div>
  <span v-else class="text-xs text-gray-400">—</span>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowPathIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  facts: {
    type: Object,
    default: null,
  },
})

const hasIssues = computed(() => {
  if (!props.facts) return false
  return (
    props.facts.is_self_flow ||
    props.facts.src_is_any ||
    props.facts.dst_is_any ||
    props.facts.src_has_public ||
    props.facts.dst_has_public
  )
})
</script>
