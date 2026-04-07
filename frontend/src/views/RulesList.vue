<template>
  <div class="space-y-6">
    <!-- Breadcrumb Navigation -->
    <nav class="flex items-center space-x-2 text-sm text-gray-600">
      <router-link
        :to="projectPath('/requests', route.params.projectId)"
        class="hover:text-primary-600"
      >
        Requests
      </router-link>
      <ChevronRightIcon class="h-4 w-4" />
      <router-link
        :to="projectPath(`/requests/${requestId}`, route.params.projectId)"
        class="hover:text-primary-600"
      >
        Request {{ requestId }}
      </router-link>
      <ChevronRightIcon class="h-4 w-4" />
      <span class="text-gray-900 font-medium">Rules</span>
    </nav>

    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900">Firewall Rules</h1>
        <p class="text-gray-600 mt-1">
          Manage and explore firewall rules for request {{ requestId }}
        </p>
      </div>
      <div class="flex items-center space-x-2">
        <Button variant="outline" @click="$router.push(projectPath(`/requests/${requestId}`))">
          Back to Request
        </Button>
      </div>
    </div>

    <!-- Rules List Component -->
    <RulesList :request-id="requestId" @view-rule="handleViewRule" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectPath } from '@/utils/projectRoutes'
import { ChevronRightIcon } from '@heroicons/vue/24/outline'
import Button from '@/components/ui/Button.vue'
import RulesList from '@/components/requests/RulesList.vue'

const route = useRoute()
const router = useRouter()

const requestId = computed(() => route.params.id)

const handleViewRule = rule => {
  router.push(projectPath(`/rules/${rule.id}`, route.params.projectId))
}
</script>
