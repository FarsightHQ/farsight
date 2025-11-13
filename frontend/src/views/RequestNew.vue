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
import FileUpload from '@/components/requests/FileUpload.vue'

const router = useRouter()
const { success, error } = useToast()

const uploading = ref(false)
const uploadProgress = ref(0)

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

    success('Request created successfully!')
    
    // Redirect to detail page
    setTimeout(() => {
      router.push(`/requests/${requestId}`)
    }, 500)
  } catch (err) {
    error(err.message || 'Failed to create request')
    uploadProgress.value = 0
  } finally {
    uploading.value = false
  }
}
</script>
