<template>
  <div>
    <h1 class="text-3xl font-bold mb-6">Create New Request</h1>

    <Card>
      <form @submit.prevent="handleSubmit">
        <div class="space-y-6">
          <!-- Title -->
          <Input
            v-model="form.title"
            label="Request Title"
            placeholder="Enter a title for this analysis"
            :required="true"
            :error="errors.title"
          />

          <!-- External ID -->
          <Input
            v-model="form.externalId"
            label="External ID (Optional)"
            placeholder="Reference ID or ticket number"
          />

          <!-- File Upload -->
          <FileUpload
            v-model="form.file"
            label="CSV File"
            :required="true"
            :error="fileUploadError"
            :upload-progress="uploadProgress"
            hint="Upload a CSV file containing firewall rules (Max 50MB)"
            @error="fileUploadError = $event || ''"
          />

          <!-- Actions -->
          <div class="flex items-center justify-end space-x-4 pt-4 border-t">
            <Button variant="outline" @click="$router.back()">Cancel</Button>
            <Button
              type="submit"
              variant="primary"
              :disabled="uploading || !form.title || !form.file || hasFileError"
            >
              <Spinner v-if="uploading" size="sm" class="mr-2" />
              {{ uploading ? 'Uploading...' : 'Create Request' }}
            </Button>
          </div>
        </div>
      </form>
    </Card>

    <!-- Simple Error Modal for Validation Errors -->
    <Modal v-model="showErrorModal" size="lg">
      <template #header>
        <h3 class="text-lg font-semibold text-error-600">Upload Error</h3>
      </template>

      <div class="space-y-4">
        <div class="bg-error-50 border border-error-200 rounded-lg p-4">
          <h4 class="text-sm font-medium text-error-900 mb-2">Error Details:</h4>
          <p class="text-sm text-error-700 whitespace-pre-wrap">{{ uploadError }}</p>
        </div>
        
        <div v-if="errorDetails" class="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 class="text-sm font-medium text-gray-900 mb-2">Additional Information:</h4>
          <div class="text-xs text-gray-700 space-y-2">
            <div v-if="errorDetails.row_number" class="flex items-center space-x-2">
              <span class="font-medium">Row Number:</span>
              <span>{{ errorDetails.row_number }}</span>
            </div>
            <div v-if="errorDetails.column_name" class="flex items-center space-x-2">
              <span class="font-medium">Column:</span>
              <span>{{ errorDetails.column_name }}</span>
            </div>
            <div v-if="errorDetails.missing_columns && errorDetails.missing_columns.length > 0" class="flex items-start space-x-2">
              <span class="font-medium">Missing Columns:</span>
              <span>{{ errorDetails.missing_columns.join(', ') }}</span>
            </div>
            <div v-if="errorDetails.field_errors" class="mt-2">
              <span class="font-medium block mb-1">Field Errors:</span>
              <ul class="list-disc list-inside space-y-1">
                <li v-for="(errorMsg, field) in errorDetails.field_errors" :key="field">
                  <span class="font-medium">{{ field }}:</span> {{ errorMsg }}
                </li>
              </ul>
            </div>
            <div v-if="errorDetails.details" class="mt-2">
              <pre class="text-xs overflow-auto max-h-40">{{ JSON.stringify(errorDetails.details, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end">
          <Button variant="primary" @click="showErrorModal = false">Close</Button>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'
import { usePipeline } from '@/composables/usePipeline'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Card from '@/components/ui/Card.vue'
import Spinner from '@/components/ui/Spinner.vue'
import Modal from '@/components/ui/Modal.vue'
import FileUpload from '@/components/requests/FileUpload.vue'

const router = useRouter()
const { success, error } = useToast()

const uploading = ref(false)
const uploadProgress = ref(0)
const createdRequestId = ref(null)
const uploadError = ref('')
const errorDetails = ref(null)
const showErrorModal = ref(false)

// Initialize pipeline composable (for background processing only)
const {
  startFullPipeline,
  fetchRequest,
} = usePipeline(() => createdRequestId.value, ref(null))

const form = reactive({
  title: '',
  externalId: '',
  file: null,
})

const errors = reactive({
  title: '',
  file: '',
})

// Track FileUpload component error separately
const fileUploadError = ref('')

// Watch for file changes and clear error if file is removed
watch(() => form.file, (newFile, oldFile) => {
  // Only update if file actually changed
  if (newFile !== oldFile) {
    if (!newFile) {
      fileUploadError.value = ''
    }
  }
})

// Check if file has validation error from FileUpload component
const hasFileError = computed(() => {
  // Explicitly check for truthy non-empty string
  const errorValue = fileUploadError.value
  const hasError = Boolean(errorValue && typeof errorValue === 'string' && errorValue.trim().length > 0)
  return hasError
})

const validateForm = () => {
  errors.title = ''
  // Don't clear errors.file here - let FileUpload component manage its own errors

  if (!form.title.trim()) {
    errors.title = 'Title is required'
    return false
  }

  if (!form.file) {
    errors.file = 'Please select a CSV file'
    fileUploadError.value = 'Please select a CSV file'
    return false
  }

  // Check if file has validation error from FileUpload component
  if (hasFileError.value) {
    errors.file = fileUploadError.value || 'File validation failed'
    return false
  }

  return true
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  uploading.value = true
  uploadProgress.value = 0
  uploadError.value = ''
  errorDetails.value = null
  showErrorModal.value = false

  try {
    // Simulate progress (in real app, use axios upload progress)
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    const response = await requestsService.create(
      form.title,
      form.file,
      form.externalId || null
    )

    clearInterval(progressInterval)
    uploadProgress.value = 100

    // Extract request ID from response
    const requestObject = response.data || response
    let extractedId = requestObject?.id || requestObject?.request_id
    
    if (!extractedId || (typeof extractedId !== 'number' && typeof extractedId !== 'string')) {
      throw new Error('Failed to extract valid request ID')
    }
    
    createdRequestId.value = String(extractedId)

    // Show simple success message
    success('File uploaded, file processed')

    // Auto-process in background (silently)
    setTimeout(async () => {
      try {
        const request = await fetchRequest()
        if (request) {
          await startFullPipeline(request)
        }
      } catch (err) {
        // Silently handle processing errors - user already has the request
        console.error('Background processing error:', err)
      }
    }, 500)

    // Redirect to details page after brief delay
    setTimeout(() => {
      router.push(`/requests/${createdRequestId.value}`)
    }, 1500)

  } catch (err) {
    // Handle validation errors from backend
    uploadProgress.value = 0
    
    // Extract error details from response
    let errorMessage = err.message || 'Failed to upload file'
    let details = null

    if (err.response?.data) {
      const errorData = err.response.data
      
      // Handle standardized error response
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : errorData.detail.message || errorMessage
        details = errorData.detail.details || errorData.detail
      } else if (errorData.message) {
        errorMessage = errorData.message
        details = errorData.details || errorData
      } else if (typeof errorData === 'string') {
        errorMessage = errorData
      } else {
        details = errorData
      }
    }

    uploadError.value = errorMessage
    errorDetails.value = details
    showErrorModal.value = true
    
    // Also show toast
    error(errorMessage)
  } finally {
    uploading.value = false
  }
}

</script>

