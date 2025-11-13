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
    <Modal v-model="showProcessingPrompt" size="md">
      <template #header>
        <h3 class="text-lg font-semibold text-gray-900">Upload Successful!</h3>
      </template>

      <div class="space-y-4">
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

      <template #footer>
        <Button variant="outline" @click="viewDetails">View Details</Button>
        <Button variant="primary" @click="startProcessing" :disabled="starting">
          <Spinner v-if="starting" size="sm" class="mr-2" />
          Start Processing
        </Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'
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
const showProcessingPrompt = ref(false)
const createdRequestId = ref(null)
const starting = ref(false)

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
    const requestData = response.data || response
    const requestId = requestData.request_id || requestData.id
    createdRequestId.value = requestId

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
  if (!createdRequestId.value) return

  starting.value = true
  showProcessingPrompt.value = false

  try {
    // Navigate to detail page with processing flag
    router.push({
      path: `/requests/${createdRequestId.value}`,
      query: { startProcessing: 'true' },
    })
  } catch (err) {
    error(err.message || 'Failed to start processing')
    starting.value = false
  }
}

const viewDetails = () => {
  if (createdRequestId.value) {
    router.push(`/requests/${createdRequestId.value}`)
  }
  showProcessingPrompt.value = false
}
</script>
