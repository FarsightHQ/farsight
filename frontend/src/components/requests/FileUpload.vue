<template>
  <div class="w-full">
    <label v-if="label" class="block text-sm font-medium text-gray-700 mb-2">
      {{ label }}
      <span v-if="required" class="text-error-500">*</span>
    </label>

    <!-- Drag & Drop Area -->
    <div
      :class="[
        'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
        isDragging
          ? 'border-primary-500 bg-primary-50'
          : 'border-gray-300 bg-gray-50 hover:border-gray-400',
        error ? 'border-error-300 bg-error-50' : '',
      ]"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".csv,text/csv,application/csv"
        class="hidden"
        @change="handleFileSelect"
      />

      <div v-if="!selectedFile" class="space-y-2">
        <svg
          class="mx-auto h-12 w-12 text-gray-400"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <div class="text-sm text-gray-600">
          <span class="font-medium text-primary-600">Click to upload</span> or drag and drop
        </div>
        <p class="text-xs text-gray-500">CSV files only (Max 50MB)</p>
      </div>

      <!-- File Preview -->
      <div v-else class="space-y-2">
        <div class="flex items-center justify-center space-x-2">
          <svg
            class="h-8 w-8 text-success-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div class="text-left">
            <p class="text-sm font-medium text-gray-900">{{ selectedFile.name }}</p>
            <p class="text-xs text-gray-500">{{ formatFileSize(selectedFile.size) }}</p>
          </div>
          <button
            type="button"
            class="ml-2 text-gray-400 hover:text-error-500"
            @click.stop="clearFile"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Progress Bar -->
    <div v-if="uploadProgress > 0 && uploadProgress < 100" class="mt-2">
      <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
        <span>Uploading...</span>
        <span>{{ uploadProgress }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-primary-600 h-2 rounded-full transition-all duration-300"
          :style="{ width: `${uploadProgress}%` }"
        ></div>
      </div>
    </div>

    <!-- Error Message -->
    <p v-if="error" class="mt-2 text-sm text-error-600">{{ error }}</p>
    <p v-if="hint && !error" class="mt-2 text-sm text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: File,
    default: null,
  },
  label: {
    type: String,
    default: '',
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
  uploadProgress: {
    type: Number,
    default: 0,
  },
  maxSize: {
    type: Number,
    default: 50 * 1024 * 1024, // 50MB default
  },
})

const emit = defineEmits(['update:modelValue', 'error'])

const fileInput = ref(null)
const isDragging = ref(false)
const selectedFile = computed(() => props.modelValue)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const validateFile = file => {
  // Check if file is provided
  if (!file) {
    emit('error', 'No file selected')
    return false
  }

  // Check file type by extension
  if (!file.name.toLowerCase().endsWith('.csv')) {
    emit('error', 'Only CSV files are allowed')
    return false
  }

  // Check MIME type only if it's provided (some browsers don't set it reliably)
  // If MIME type is provided and doesn't match, show warning but don't block
  const validMimeTypes = ['text/csv', 'application/csv', 'text/plain', '']
  if (file.type && file.type.length > 0 && !validMimeTypes.includes(file.type)) {
    // Don't block upload, just warn - extension check is more reliable
    console.warn(`File MIME type is ${file.type}, but extension is .csv. Allowing upload.`)
  }

  // Check if file is empty
  if (file.size === 0) {
    emit('error', 'File is empty. Please upload a valid CSV file.')
    return false
  }

  // Check file size
  if (file.size > props.maxSize) {
    emit('error', `File size must be less than ${formatFileSize(props.maxSize)}`)
    return false
  }

  return true
}

const handleFileSelect = event => {
  const file = event.target.files[0]
  if (file) {
    // Always allow file selection, but validate and show error if invalid
    if (validateFile(file)) {
      emit('update:modelValue', file)
      emit('error', '')
    } else {
      // Still emit the file so user can see it, but keep error visible
      emit('update:modelValue', file)
      // Error is already emitted by validateFile
    }
  }
}

const handleDragOver = event => {
  isDragging.value = true
  event.preventDefault()
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = event => {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    // Always allow file drop, but validate and show error if invalid
    if (validateFile(file)) {
      emit('update:modelValue', file)
      emit('error', '')
    } else {
      // Still emit the file so user can see it, but keep error visible
      emit('update:modelValue', file)
      // Error is already emitted by validateFile
    }
  }
}

const clearFile = () => {
  emit('update:modelValue', null)
  emit('error', '')
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const formatFileSize = bytes => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// Watch for file changes via v-model and re-validate
// Only validate when file actually changes (not on every render)
watch(
  () => props.modelValue,
  (newFile, oldFile) => {
    // Only validate if file actually changed
    if (newFile !== oldFile) {
      if (newFile) {
        // Re-validate when file changes
        const isValid = validateFile(newFile)
        // Explicitly clear error if validation passes
        if (isValid) {
          emit('error', '')
        }
      } else {
        // Clear error when file is removed
        emit('error', '')
      }
    }
  }
)
</script>
