<template>
  <div class="w-full">
    <label
      v-if="label"
      :for="inputId"
      class="block text-sm font-medium text-theme-text-content mb-1"
    >
      {{ label }}
      <span v-if="required" class="text-error-500">*</span>
    </label>
    <input
      :id="inputId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      class="input"
      :class="{ 'border-error-300 focus:border-error-500 focus:ring-error-500': error }"
      @input="onInput"
      @blur="onBlur"
    />
    <p v-if="error" class="mt-1 text-sm text-error-600">{{ error }}</p>
    <p v-if="hint && !error" class="mt-1 text-sm text-theme-text-muted">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { useId } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: 'text',
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  required: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  hint: {
    type: String,
    default: '',
  },
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  blur: [event: FocusEvent]
}>()

const inputId = useId()

function onInput(e: Event) {
  const v = (e.target as HTMLInputElement).value
  emit('update:modelValue', v)
}

function onBlur(e: FocusEvent) {
  emit('blur', e)
}
</script>
