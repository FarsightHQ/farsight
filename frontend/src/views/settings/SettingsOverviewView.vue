<template>
  <PageFrame
    class="flex-1 min-h-0 flex flex-col"
    :breadcrumb-items="breadcrumbItems"
    title="Settings"
    subtitle="Application preferences and global policy."
  >
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 max-w-4xl">
      <router-link
        :to="{ name: 'SettingsAppearance' }"
        class="block rounded-lg border border-theme-border-default bg-theme-card p-5 shadow-sm hover:bg-theme-hover transition-colors"
      >
        <h2 class="font-medium text-theme-text-content">Appearance</h2>
        <p class="mt-2 text-sm text-theme-text-muted">Theme and display options (coming soon).</p>
      </router-link>
      <router-link
        :to="{ name: 'SettingsRiskyPortPolicy' }"
        class="block rounded-lg border border-theme-border-default bg-theme-card p-5 shadow-sm hover:bg-theme-hover transition-colors"
      >
        <h2 class="font-medium text-theme-text-content">Risky port policy</h2>
        <p class="mt-2 text-sm text-theme-text-muted">
          Global port list used in FAR rule and security analysis.
        </p>
      </router-link>
    </div>
  </PageFrame>
</template>

<script setup>
import PageFrame from '@/components/layout/PageFrame.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const { breadcrumbItems } = usePageBreadcrumbs()
</script>
