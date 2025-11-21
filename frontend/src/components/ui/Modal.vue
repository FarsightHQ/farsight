<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
        :class="{ 'p-4': size !== 'full', 'p-2': size === 'full' }"
        @click.self="$emit('update:modelValue', false)"
      >
        <div
          :class="[
            sizeClasses,
            'bg-theme-card rounded-lg shadow-xl',
            size === 'full' ? 'flex flex-col h-[calc(100vh-2rem)]' : 'max-h-[90vh] overflow-y-auto'
          ]"
          @click.stop
        >
          <div v-if="title || $slots.header" :class="{ 'flex-shrink-0': size === 'full' }" class="flex items-center justify-between p-6 border-b border-theme-border-card">
            <h3 v-if="title" class="text-lg font-semibold text-theme-text-content">{{ title }}</h3>
            <slot name="header" />
            <button
              @click="$emit('update:modelValue', false)"
              class="text-theme-text-muted hover:text-theme-text-content"
            >
              <XMarkIcon class="h-6 w-6" />
            </button>
          </div>
          <div :class="{ 'flex-1 overflow-auto': size === 'full', 'p-6': size !== 'full' }">
            <slot />
          </div>
          <div v-if="$slots.footer" :class="{ 'flex-shrink-0': size === 'full' }" class="flex items-center justify-end gap-3 p-6 border-t border-theme-border-card">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'xl', 'full'].includes(value),
  },
})

const emit = defineEmits(['update:modelValue'])

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'w-full max-w-md',
    md: 'w-full max-w-lg',
    lg: 'w-full max-w-2xl',
    xl: 'w-full max-w-4xl',
    full: 'w-[calc(100vw-2rem)] max-w-[calc(100vw-2rem)]',
  }
  return sizes[props.size]
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-theme-card,
.modal-leave-active .bg-theme-card {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-theme-card,
.modal-leave-to .bg-theme-card {
  transform: scale(0.95);
}
</style>

