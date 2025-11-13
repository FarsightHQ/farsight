<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-3xl font-bold">FAR Requests</h1>
      <Button variant="primary" @click="$router.push('/requests/new')">
        New Request
      </Button>
    </div>

    <!-- Search and Filters -->
    <Card class="mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="md:col-span-2">
          <Input
            v-model="searchQuery"
            placeholder="Search by title or external ID..."
            @input="handleSearch"
          />
        </div>
        <div>
          <select
            v-model="statusFilter"
            class="input"
            @change="handleFilter"
          >
            <option value="">All Statuses</option>
            <option value="submitted">Submitted</option>
            <option value="processing">Processing</option>
            <option value="ingested">Ingested</option>
            <option value="completed">Completed</option>
            <option value="error">Error</option>
            <option value="failed">Failed</option>
          </select>
        </div>
        <div class="flex items-center space-x-2">
          <Button variant="outline" size="sm" @click="clearFilters">Clear</Button>
        </div>
      </div>
    </Card>

    <!-- View Toggle and Sort -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center space-x-2">
        <Button
          :variant="viewMode === 'table' ? 'primary' : 'outline'"
          size="sm"
          @click="viewMode = 'table'"
        >
          Table
        </Button>
        <Button
          :variant="viewMode === 'card' ? 'primary' : 'outline'"
          size="sm"
          @click="viewMode = 'card'"
        >
          Cards
        </Button>
      </div>
      <div class="text-sm text-gray-600">
        Showing {{ displayedRequests.length }} of {{ totalRequests }} requests
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-4">
      <Card v-for="i in 5" :key="i" class="animate-pulse">
        <div class="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div class="h-4 bg-gray-200 rounded w-1/2"></div>
      </Card>
    </div>

    <!-- Empty State -->
    <Card v-else-if="!loading && filteredRequests.length === 0">
      <div class="text-center py-12">
        <svg
          class="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No requests found</h3>
        <p class="mt-1 text-sm text-gray-500">
          {{ searchQuery || statusFilter ? 'Try adjusting your filters.' : 'Get started by creating a new request.' }}
        </p>
        <div class="mt-6">
          <Button variant="primary" @click="$router.push('/requests/new')">
            Create New Request
          </Button>
        </div>
      </div>
    </Card>

    <!-- Table View -->
    <div v-else-if="viewMode === 'table'">
      <RequestTable
        :requests="displayedRequests"
        :loading="loading"
        :sort-key="sortKey"
        :sort-direction="sortDirection"
        @sort="handleSort"
        @view="handleView"
        @delete="handleDelete"
      />
    </div>

    <!-- Card View -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <RequestCard
        v-for="request in displayedRequests"
        :key="request.id"
        :request="request"
        @view="handleView"
        @delete="handleDelete"
      />
    </div>

    <!-- Pagination -->
    <div v-if="!loading && filteredRequests.length > 0" class="mt-6 flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-sm text-gray-700">Show</span>
        <select v-model="pageSize" class="input text-sm" style="width: auto">
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
        <span class="text-sm text-gray-700">per page</span>
      </div>
      <div class="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          Previous
        </Button>
        <span class="text-sm text-gray-700">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        <Button
          variant="outline"
          size="sm"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          Next
        </Button>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmModal
      v-model="showDeleteModal"
      :request="requestToDelete"
      :deleting="deleting"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { requestsService } from '@/services/requests'
import { useToast } from '@/composables/useToast'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Card from '@/components/ui/Card.vue'
import RequestTable from '@/components/requests/RequestTable.vue'
import RequestCard from '@/components/requests/RequestCard.vue'
import DeleteConfirmModal from '@/components/requests/DeleteConfirmModal.vue'

const router = useRouter()
const { success, error } = useToast()

const loading = ref(false)
const requests = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const viewMode = ref('table')
const sortKey = ref('created_at')
const sortDirection = ref('desc')
const currentPage = ref(1)
const pageSize = ref(25)
const totalRequests = ref(0)
const showDeleteModal = ref(false)
const requestToDelete = ref(null)
const deleting = ref(false)

const filteredRequests = computed(() => {
  let filtered = [...requests.value]

  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(
      (req) =>
        req.title?.toLowerCase().includes(query) ||
        req.external_id?.toLowerCase().includes(query)
    )
  }

  // Status filter
  if (statusFilter.value) {
    filtered = filtered.filter((req) => req.status === statusFilter.value)
  }

  // Sort
  filtered.sort((a, b) => {
    let aVal = a[sortKey.value]
    let bVal = b[sortKey.value]

    if (sortKey.value === 'created_at') {
      aVal = new Date(aVal)
      bVal = new Date(bVal)
    }

    if (sortDirection.value === 'asc') {
      return aVal > bVal ? 1 : -1
    } else {
      return aVal < bVal ? 1 : -1
    }
  })

  return filtered
})

const displayedRequests = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredRequests.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredRequests.value.length / pageSize.value)
})

const fetchRequests = async () => {
  loading.value = true
  try {
    const response = await requestsService.list(0, 1000) // Get all for client-side filtering
    if (response.data) {
      requests.value = Array.isArray(response.data) ? response.data : []
      totalRequests.value = response.metadata?.pagination?.total || requests.value.length
    }
  } catch (err) {
    error(err.message || 'Failed to load requests')
    requests.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleFilter = () => {
  currentPage.value = 1
}

const clearFilters = () => {
  searchQuery.value = ''
  statusFilter.value = ''
  currentPage.value = 1
}

const handleSort = (key) => {
  if (sortKey.value === key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDirection.value = 'asc'
  }
}

const handleView = (request) => {
  router.push(`/requests/${request.id}`)
}

const handleDelete = (request) => {
  requestToDelete.value = request
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!requestToDelete.value) return

  deleting.value = true
  try {
    await requestsService.delete(requestToDelete.value.id)
    success(`Request "${requestToDelete.value.title}" deleted successfully`)
    
    // Remove from local list immediately for better UX
    const index = requests.value.findIndex((r) => r.id === requestToDelete.value.id)
    if (index > -1) {
      requests.value.splice(index, 1)
      totalRequests.value--
    }
    
    // Refresh list to ensure consistency
    await fetchRequests()
    
    // Close modal
    showDeleteModal.value = false
    requestToDelete.value = null
  } catch (err) {
    error(err.message || 'Failed to delete request')
  } finally {
    deleting.value = false
  }
}

const cancelDelete = () => {
  showDeleteModal.value = false
  requestToDelete.value = null
}

watch(pageSize, () => {
  currentPage.value = 1
})

onMounted(() => {
  fetchRequests()
})
</script>
