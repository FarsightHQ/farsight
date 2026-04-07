<template>
  <div>
    <PageFrame
      :breadcrumb-items="breadcrumbItems"
      title="Upload assets"
      subtitle="Import a CSV to add or update assets in this project."
    >
      <template #actions>
        <Button variant="outline" @click="goAssetsList">Back to assets</Button>
      </template>

    <Card>
      <form @submit.prevent="handleSubmit">
        <div class="space-y-6">
          <!-- File Upload -->
          <FileUpload
            v-model="form.file"
            label="CSV File"
            :required="true"
            :error="errors.file"
            :upload-progress="uploadProgress"
            hint="Upload a CSV file containing asset data (Max 50MB)"
          />

          <!-- Actions -->
          <div class="flex items-center justify-end space-x-4 pt-4 border-t">
            <Button type="submit" variant="primary" :disabled="uploading || !form.file">
              <Spinner v-if="uploading" size="sm" class="mr-2" />
              {{ uploading ? 'Uploading...' : 'Upload CSV' }}
            </Button>
          </div>
        </div>
      </form>
    </Card>

    <!-- Upload Results -->
    <Card v-if="uploadResult" class="mt-6">
      <h2 class="text-xl font-semibold text-gray-900 mb-4">Upload Results</h2>

      <!-- Summary -->
      <div class="bg-primary-50 border border-primary-200 rounded-lg p-4 mb-4">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <div class="text-sm text-primary-700">Total Rows</div>
            <div class="text-2xl font-bold text-primary-900">
              {{ uploadResult.summary.total_rows }}
            </div>
          </div>
          <div>
            <div class="text-sm text-primary-700">Created Assets</div>
            <div class="text-2xl font-bold text-success-700">
              {{ uploadResult.summary.created_assets }}
            </div>
          </div>
          <div>
            <div class="text-sm text-primary-700">Updated Assets</div>
            <div class="text-2xl font-bold text-info-700">
              {{ uploadResult.summary.updated_assets }}
            </div>
          </div>
          <div>
            <div class="text-sm text-primary-700">Processed Rows</div>
            <div class="text-2xl font-bold text-primary-900">
              {{ uploadResult.summary.processed_rows }}
            </div>
          </div>
          <div>
            <div class="text-sm text-primary-700">Error Rows</div>
            <div class="text-2xl font-bold text-error-700">
              {{ uploadResult.summary.error_rows }}
            </div>
          </div>
          <div v-if="uploadResult.summary.processing_time_ms">
            <div class="text-sm text-primary-700">Processing Time</div>
            <div class="text-2xl font-bold text-primary-900">
              {{ formatTime(uploadResult.summary.processing_time_ms) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Batch ID -->
      <div class="mb-4">
        <label class="text-sm font-medium text-gray-700">Batch ID</label>
        <div class="mt-1 flex items-center space-x-2">
          <code class="text-sm font-mono bg-gray-100 px-3 py-2 rounded">{{
            uploadResult.batch_id
          }}</code>
          <Button variant="ghost" size="sm" @click="copyToClipboard(uploadResult.batch_id)">
            Copy
          </Button>
        </div>
      </div>

      <!-- Error Details -->
      <div
        v-if="
          uploadResult.upload_details?.error_details &&
          Object.keys(uploadResult.upload_details.error_details).length > 0
        "
        class="mt-4"
      >
        <h3 class="text-sm font-medium text-gray-700 mb-2">Error Details</h3>
        <div class="bg-error-50 border border-error-200 rounded-lg p-4 max-h-64 overflow-y-auto">
          <pre class="text-xs text-error-800">{{
            JSON.stringify(uploadResult.upload_details.error_details, null, 2)
          }}</pre>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center space-x-4 mt-6 pt-4 border-t">
        <Button variant="outline" @click="goAssetsList"> View All Assets </Button>
        <Button variant="primary" @click="viewBatchDetails"> View Batch Details </Button>
        <Button variant="outline" @click="resetForm"> Upload Another </Button>
      </div>
    </Card>
    </PageFrame>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { projectPath } from '@/utils/projectRoutes'
import PageFrame from '@/components/layout/PageFrame.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'
import { assetsService } from '@/services/assets'
import { useToast } from '@/composables/useToast'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Spinner from '@/components/ui/Spinner.vue'
import FileUpload from '@/components/requests/FileUpload.vue'

const router = useRouter()
const route = useRoute()
const { success, error } = useToast()
const { breadcrumbItems } = usePageBreadcrumbs()

const goAssetsList = () => {
  router.push(projectPath('/assets', route.params.projectId))
}

const uploading = ref(false)
const uploadProgress = ref(0)
const uploadResult = ref(null)

const form = reactive({
  file: null,
})

const errors = reactive({
  file: '',
})

const validateForm = () => {
  errors.file = ''

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

    const response = await assetsService.uploadCSV(form.file)

    clearInterval(progressInterval)
    uploadProgress.value = 100

    // Extract upload result from response
    const resultData = response.data || response
    uploadResult.value = {
      batch_id: resultData.batch_id,
      filename: resultData.filename,
      summary: resultData.summary,
      upload_details: resultData.upload_details,
    }

    success('Assets uploaded successfully!')
  } catch (err) {
    error(err.message || 'Failed to upload assets')
    uploadProgress.value = 0
  } finally {
    uploading.value = false
  }
}

const viewBatchDetails = () => {
  if (uploadResult.value?.batch_id) {
    router.push(
      projectPath(`/assets/upload-batches/${uploadResult.value.batch_id}`, route.params.projectId)
    )
  }
}

const resetForm = () => {
  form.file = null
  uploadResult.value = null
  uploadProgress.value = 0
  errors.file = ''
}

const copyToClipboard = async text => {
  try {
    await navigator.clipboard.writeText(text)
    success('Copied to clipboard')
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

const formatTime = ms => {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}
</script>
