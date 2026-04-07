<template>
  <PageFrame :breadcrumb-items="breadcrumbItems" title="Settings">
    <div class="max-w-2xl space-y-8">
    <section class="border border-theme-border rounded-lg p-4 space-y-2">
      <h2 class="font-medium">Appearance</h2>
      <p class="text-sm text-theme-text-muted">
        Theme and display preferences will be available here.
      </p>
    </section>

    <section class="border border-theme-border rounded-lg p-4 space-y-2">
      <h2 class="font-medium">Global policy</h2>
      <p class="text-sm text-theme-text-muted">
        Organization-wide risky ports, allowed/denied IP ranges, and similar rules are planned for
        a later release. FAR analysis will be able to reference these defaults per project.
      </p>
    </section>
    </div>
  </PageFrame>
</template>

<script setup>
import PageFrame from '@/components/layout/PageFrame.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const { breadcrumbItems } = usePageBreadcrumbs()
</script>
