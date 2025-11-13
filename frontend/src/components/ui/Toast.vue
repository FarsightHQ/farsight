<template>
  <TransitionGroup
    name="toast"
    tag="div"
    class="fixed top-4 right-4 z-50 space-y-2"
  >
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="toastClasses(toast.type)"
      class="flex items-center gap-3 rounded-lg px-4 py-3 shadow-lg min-w-[300px] max-w-md"
    >
      <component :is="iconComponent(toast.type)" class="h-5 w-5 flex-shrink-0" />
      <p class="flex-1 text-sm font-medium">{{ toast.message }}</p>
      <button
        @click="removeToast(toast.id)"
        class="flex-shrink-0 text-gray-400 hover:text-gray-600"
      >
        <XMarkIcon class="h-5 w-5" />
      </button>
    </div>
  </TransitionGroup>
</template>

<script setup>
import { computed } from 'vue'
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { useToast } from '@/composables/useToast'

const { toasts, removeToast } = useToast()

const toastClasses = (type) => {
  const classes = {
    success: 'bg-success-50 text-success-800 border border-success-200',
    error: 'bg-error-50 text-error-800 border border-error-200',
    warning: 'bg-warning-50 text-warning-800 border border-warning-200',
    info: 'bg-primary-50 text-primary-800 border border-primary-200',
  }
  return classes[type] || classes.info
}

const iconComponent = (type) => {
  const icons = {
    success: CheckCircleIcon,
    error: XCircleIcon,
    warning: ExclamationTriangleIcon,
    info: InformationCircleIcon,
  }
  return icons[type] || InformationCircleIcon
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>

