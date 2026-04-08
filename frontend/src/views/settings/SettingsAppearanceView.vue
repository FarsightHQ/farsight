<template>
  <PageFrame
    class="flex-1 min-h-0 flex flex-col"
    :breadcrumb-items="breadcrumbItems"
    title="Appearance"
    subtitle="Theme and display preferences."
  >
    <p class="text-sm text-theme-text-muted max-w-2xl">
      Appearance settings are not available yet. Check back in a later release.
    </p>
  </PageFrame>
</template>

<script setup>
import PageFrame from '@/components/layout/PageFrame.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const { breadcrumbItems } = usePageBreadcrumbs()
</script>
