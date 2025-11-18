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
            :error="errors.file"
            :upload-progress="uploadProgress"
            hint="Upload a CSV file containing firewall rules (Max 50MB)"
          />

          <!-- Actions -->
          <div class="flex items-center justify-end space-x-4 pt-4 border-t">
            <Button variant="outline" @click="$router.back()">Cancel</Button>
            <Button
              type="submit"
              variant="primary"
              :disabled="uploading || !form.title || !form.file"
            >
              <Spinner v-if="uploading" size="sm" class="mr-2" />
              {{ uploading ? 'Uploading...' : 'Create Request' }}
            </Button>
          </div>
        </div>
      </form>
    </Card>

    <!-- Processing Prompt Modal -->
    <Modal v-model="showProcessingPrompt" size="lg">
      <template #header>
        <h3 class="text-lg font-semibold text-gray-900">
          <span v-if="!isProcessingPipeline && !pipelineComplete && !pipelineError">
            Upload Successful!
          </span>
          <span v-else-if="isProcessingPipeline">Processing Pipeline</span>
          <span v-else-if="pipelineComplete" class="text-success-600">Processing Complete!</span>
          <span v-else-if="pipelineError" class="text-error-600">Processing Error</span>
        </h3>
      </template>

      <!-- Initial Prompt -->
      <div v-if="!isProcessingPipeline && !pipelineComplete && !pipelineError" class="space-y-4">
        <p class="text-gray-600">
          Your CSV file has been uploaded successfully. Would you like to start processing the
          pipeline now?
        </p>
        <div class="bg-primary-50 border border-primary-200 rounded-lg p-4">
          <p class="text-sm font-medium text-primary-900 mb-2">Processing Pipeline:</p>
          <ul class="text-sm text-primary-800 space-y-1 list-disc list-inside">
            <li>Process CSV and create firewall rules</li>
            <li>Compute standard facts</li>
            <li>Compute hybrid facts</li>
          </ul>
        </div>
      </div>

      <!-- Processing Dashboard -->
      <div v-else-if="isProcessingPipeline || pipelineComplete">
        <ProcessingDashboard
          :steps="pipelineSteps"
          :can-cancel="false"
          @retry="handleRetryStep"
        />
      </div>

      <!-- Error State -->
      <div v-else-if="pipelineError" class="space-y-4">
        <div class="bg-error-50 border border-error-200 rounded-lg p-4">
          <h4 class="text-sm font-medium text-error-900 mb-2">Error Details:</h4>
          <p class="text-sm text-error-700">{{ pipelineError }}</p>
        </div>
        <ProcessingDashboard
          :steps="pipelineSteps"
          :can-cancel="false"
          @retry="handleRetryStep"
        />
      </div>

      <template #footer>
        <div class="flex items-center justify-between w-full">
          <Button
            variant="outline"
            @click="navigateToDetails"
          >
            Go to Details Page
          </Button>
          <div class="flex items-center space-x-2">
            <Button
              v-if="!isProcessingPipeline && !pipelineComplete && !pipelineError"
              variant="primary"
              @click="startProcessing"
              :disabled="starting || isProcessingPipeline"
            >
              <Spinner v-if="starting" size="sm" class="mr-2" />
              Start Processing
            </Button>
            <Button
              v-if="pipelineComplete || pipelineError"
              variant="primary"
              @click="navigateToDetails"
            >
              Go to Details Page
            </Button>
            <Button
              v-if="pipelineError"
              variant="outline"
              @click="retryPipeline"
              :disabled="starting"
            >
              <Spinner v-if="starting" size="sm" class="mr-2" />
              Retry
            </Button>
          </div>
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
import ProcessingDashboard from '@/components/requests/ProcessingDashboard.vue'

const router = useRouter()
const { success, error } = useToast()

const uploading = ref(false)
const uploadProgress = ref(0)
const showProcessingPrompt = ref(false)
const createdRequestId = ref(null)
const starting = ref(false)
const createdRequest = ref(null)
const pipelineComplete = ref(false)
const pipelineError = ref(null)

// Initialize pipeline composable
const {
  pipelineSteps,
  isProcessingPipeline,
  startFullPipeline,
  handleRetryStep,
  fetchRequest,
} = usePipeline(() => createdRequestId.value, createdRequest)

// Watch for pipeline completion
watch(
  [() => pipelineSteps.value, () => isProcessingPipeline.value],
  ([steps, isProcessing]) => {
    if (!isProcessing) return
    
    const allCompleted = steps.every((s) => s.status === 'completed')
    const hasError = steps.some((s) => s.status === 'error')
    
    if (allCompleted) {
      pipelineComplete.value = true
      // Auto-navigate after 2 seconds
      setTimeout(() => {
        navigateToDetails()
      }, 2000)
    } else if (hasError) {
      const errorStep = steps.find((s) => s.status === 'error')
      pipelineError.value = errorStep?.error || 'An error occurred during processing'
    }
  },
  { deep: true }
)

const form = reactive({
  title: '',
  externalId: '',
  file: null,
})

const errors = reactive({
  title: '',
  file: '',
})

const validateForm = () => {
  errors.title = ''
  errors.file = ''

  if (!form.title.trim()) {
    errors.title = 'Title is required'
    return false
  }

  if (!form.file) {
    errors.file = 'Please select a CSV file'
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
    // API interceptor returns standardized response: { status, message, data: {...} }
    // So response = { status, message, data: { id: 123, ... } }
    // And response.data = { id: 123, ... } (the actual request object)
    
    // Log for debugging
    console.log('[RequestNew] Full response:', JSON.stringify(response, null, 2))
    
    // The interceptor returns: { status, message, data: { id: 123, ... } }
    // So response.data is the request object
    const requestObject = response.data || response
    
    console.log('[RequestNew] Request object:', requestObject)
    
    // Extract ID - simple and direct
    let extractedId = requestObject?.id || requestObject?.request_id
    
    // Validate
    if (!extractedId || (typeof extractedId !== 'number' && typeof extractedId !== 'string')) {
      console.error('[RequestNew] Invalid ID:', extractedId, 'Type:', typeof extractedId)
      throw new Error('Failed to extract valid request ID')
    }
    
    // Convert to string
    createdRequestId.value = String(extractedId)
    createdRequest.value = requestObject
    
    console.log('[RequestNew] ID extracted:', createdRequestId.value)

    success('Request created successfully!')

    // Show processing prompt modal
    showProcessingPrompt.value = true
  } catch (err) {
    error(err.message || 'Failed to create request')
    uploadProgress.value = 0
  } finally {
    uploading.value = false
  }
}

const startProcessing = async () => {
  // Validate request ID before starting
  console.log('[RequestNew] startProcessing - createdRequestId.value:', createdRequestId.value, 'Type:', typeof createdRequestId.value)
  
  if (!createdRequestId.value) {
    error('Request ID is missing. Please try uploading again.')
    return
  }

  // Validate ID is not an object or invalid string
  if (typeof createdRequestId.value === 'object') {
    error('Invalid request ID format. Please try uploading again.')
    return
  }

  const idString = String(createdRequestId.value)
  if (idString === 'null' || idString === 'undefined' || idString === '[object Object]') {
    error('Invalid request ID. Please try uploading again.')
    return
  }

  starting.value = true
  pipelineError.value = null
  pipelineComplete.value = false

  try {
    // Fetch the request to get current status
    const request = await fetchRequest()
    if (!request) {
      throw new Error('Failed to fetch request')
    }

    // Start the full pipeline
    const success = await startFullPipeline(request)
    if (!success) {
      throw new Error('Failed to start pipeline')
    }

    starting.value = false
  } catch (err) {
    error(err.message || 'Failed to start processing')
    starting.value = false
    pipelineError.value = err.message || 'Failed to start processing'
  }
}

const retryPipeline = async () => {
  pipelineError.value = null
  pipelineComplete.value = false
  await startProcessing()
}

const navigateToDetails = () => {
  if (createdRequestId.value) {
    router.push(`/requests/${createdRequestId.value}`)
  }
  showProcessingPrompt.value = false
}

const viewDetails = () => {
  navigateToDetails()
}
</script>

