<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
        :class="{ 'p-4': size !== 'full', 'p-2': size === 'full' }"
        role="presentation"
        @click.self="$emit('update:modelValue', false)"
      >
        <div
          ref="dialogRef"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="title ? titleId : undefined"
          :class="[
            sizeClasses,
            'bg-theme-card rounded-lg shadow-xl outline-none',
            size === 'full' ? 'flex flex-col h-[calc(100vh-2rem)]' : 'max-h-[90vh] overflow-y-auto',
          ]"
          tabindex="-1"
          @click.stop
        >
          <div
            v-if="title || $slots.header"
            :class="{ 'flex-shrink-0': size === 'full' }"
            class="flex items-center justify-between p-6 border-b border-theme-border-card"
          >
            <h3 v-if="title" :id="titleId" class="text-lg font-semibold text-theme-text-content">
              {{ title }}
            </h3>
            <slot name="header" />
            <button
              type="button"
              class="text-theme-text-muted hover:text-theme-text-content"
              aria-label="Close dialog"
              @click="$emit('update:modelValue', false)"
            >
              <XMarkIcon class="h-6 w-6" aria-hidden="true" />
            </button>
          </div>
          <div :class="{ 'flex-1 overflow-auto': size === 'full', 'p-6': size !== 'full' }">
            <slot />
          </div>
          <div
            v-if="$slots.footer"
            :class="{ 'flex-shrink-0': size === 'full' }"
            class="flex items-center justify-end gap-3 p-6 border-t border-theme-border-card"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, watch, onBeforeUnmount, useId, ref, nextTick } from 'vue'
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
    validator: value => ['sm', 'md', 'lg', 'xl', 'full'].includes(value),
  },
})

const emit = defineEmits(['update:modelValue'])

const titleId = useId()
const dialogRef = ref(null)

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

let escapeHandler = null

function removeEscapeListener() {
  if (escapeHandler) {
    document.removeEventListener('keydown', escapeHandler)
    escapeHandler = null
  }
}

watch(
  () => props.modelValue,
  async open => {
    removeEscapeListener()
    if (open) {
      escapeHandler = e => {
        if (e.key === 'Escape') {
          emit('update:modelValue', false)
        }
      }
      document.addEventListener('keydown', escapeHandler)
      await nextTick()
      dialogRef.value?.focus?.()
    }
  }
)

onBeforeUnmount(removeEscapeListener)
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
