<template>
  <div class="max-w-3xl">
  <PageFrame
    :breadcrumb-items="breadcrumbItems"
    :title="pageTitle"
    :subtitle="pageSubtitle"
  >
    <div class="space-y-8">
    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-8 bg-theme-active/30 rounded w-1/3"></div>
      <div class="h-24 bg-theme-active/30 rounded"></div>
    </div>

    <div v-else-if="loadError" class="rounded-lg border border-error-200 bg-error-50 p-4 text-error-800 text-sm">
      {{ loadError }}
    </div>

    <template v-else-if="project">
      <section class="border border-theme-border rounded-lg p-4 space-y-4">
        <h2 class="font-medium text-theme-text-content">Details</h2>
        <form class="space-y-3" @submit.prevent="saveProject">
          <div>
            <label class="block text-sm mb-1">Name</label>
            <input
              v-model="editName"
              type="text"
              class="w-full border border-theme-border rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label class="block text-sm mb-1">Description</label>
            <textarea
              v-model="editDescription"
              rows="3"
              class="w-full border border-theme-border rounded px-3 py-2 text-sm"
            />
          </div>
          <div class="flex items-center gap-2">
            <button
              type="submit"
              class="px-4 py-2 text-sm font-medium rounded-lg bg-theme-nav-selected text-white disabled:opacity-50"
              :disabled="saving"
            >
              {{ saving ? 'Saving…' : 'Save changes' }}
            </button>
            <p v-if="saveError" class="text-sm text-error-600">{{ saveError }}</p>
            <p v-if="saveOk" class="text-sm text-green-600">Saved.</p>
          </div>
          <p class="text-xs text-theme-text-muted">
            Editing requires admin access on this project. If save fails, you may be a viewer only.
          </p>
        </form>
      </section>

      <section class="border border-theme-border rounded-lg p-4 space-y-3">
        <h2 class="font-medium text-theme-text-content">Members</h2>
        <p v-if="membersLoading" class="text-sm text-theme-text-muted">Loading members…</p>
        <p v-else-if="membersError" class="text-sm text-error-600">{{ membersError }}</p>
        <ul v-else class="divide-y divide-theme-border">
          <li
            v-for="m in members"
            :key="m.user_sub"
            class="py-2 flex justify-between text-sm"
          >
            <code class="text-xs break-all">{{ m.user_sub }}</code>
            <span class="text-theme-text-muted shrink-0 ml-2">{{ m.role }}</span>
          </li>
        </ul>
      </section>

      <section class="border border-theme-border rounded-lg p-4 space-y-3">
        <h2 class="font-medium text-theme-text-content">Invite by email</h2>
        <p class="text-xs text-theme-text-muted">
          Creates an invitation token (admin only). Share the token securely with the invitee.
        </p>
        <form class="flex flex-wrap gap-2 items-end" @submit.prevent="createInvite">
          <div>
            <label class="block text-xs mb-1">Email</label>
            <input
              v-model="inviteEmail"
              type="email"
              required
              class="border border-theme-border rounded px-3 py-2 text-sm w-56"
            />
          </div>
          <div>
            <label class="block text-xs mb-1">Role</label>
            <select v-model="inviteRole" class="border border-theme-border rounded px-3 py-2 text-sm">
              <option value="viewer">viewer</option>
              <option value="member">member</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <button
            type="submit"
            class="px-4 py-2 text-sm font-medium rounded-lg bg-theme-sidebar-hover"
            :disabled="inviting"
          >
            {{ inviting ? 'Creating…' : 'Create invitation' }}
          </button>
        </form>
        <p v-if="inviteError" class="text-sm text-error-600">{{ inviteError }}</p>
        <div v-if="lastInviteToken" class="rounded bg-theme-active/20 p-3 text-sm space-y-2">
          <p class="font-medium">Invitation token (copy once)</p>
          <code class="block text-xs break-all select-all">{{ lastInviteToken }}</code>
          <p class="text-xs text-theme-text-muted">
            Expires: {{ lastInviteExpires }}. Accept via API: {{ lastInvitePath }}
          </p>
          <button
            type="button"
            class="text-xs text-primary-600 underline"
            @click="copyToken(lastInviteToken)"
          >
            Copy token
          </button>
        </div>
      </section>

      <div class="flex gap-3">
        <router-link
          :to="{ name: 'Requests', params: { projectId } }"
          class="text-sm text-primary-600 hover:underline"
        >
          Open requests
        </router-link>
        <router-link
          :to="{ name: 'ProjectAssets', params: { projectId } }"
          class="text-sm text-primary-600 hover:underline"
        >
          Project assets
        </router-link>
      </div>
    </template>
    </div>
  </PageFrame>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { projectsService } from '@/services/projects'
import { useToast } from '@/composables/useToast'
import PageFrame from '@/components/layout/PageFrame.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const route = useRoute()
const { breadcrumbItems, projectName: breadcrumbProjectName } = usePageBreadcrumbs()
const { success, error: toastError } = useToast()

const projectId = computed(() => route.params.projectId)

const pageTitle = computed(
  () => project.value?.name || breadcrumbProjectName.value || 'Project'
)
const pageSubtitle = computed(() =>
  project.value?.slug ? `slug: ${project.value.slug}` : ''
)

const project = ref(null)
const loading = ref(true)
const loadError = ref('')

const editName = ref('')
const editDescription = ref('')
const saving = ref(false)
const saveError = ref('')
const saveOk = ref(false)

const members = ref([])
const membersLoading = ref(false)
const membersError = ref('')

const inviteEmail = ref('')
const inviteRole = ref('member')
const inviting = ref(false)
const inviteError = ref('')
const lastInviteToken = ref('')
const lastInviteExpires = ref('')
const lastInvitePath = ref('')

function unwrap(res) {
  const d = res?.data ?? res
  return d?.data ?? d
}

async function loadProject() {
  loadError.value = ''
  loading.value = true
  try {
    const res = await projectsService.get(projectId.value)
    const p = unwrap(res)
    project.value = p
    editName.value = p.name || ''
    editDescription.value = p.description || ''
  } catch (e) {
    loadError.value = e.message || 'Failed to load project'
    project.value = null
  } finally {
    loading.value = false
  }
}

async function loadMembers() {
  membersError.value = ''
  membersLoading.value = true
  try {
    const res = await projectsService.listMembers(projectId.value)
    const body = unwrap(res)
    members.value = body.members || []
  } catch (e) {
    membersError.value = e.message || 'Failed to load members'
    members.value = []
  } finally {
    membersLoading.value = false
  }
}

async function saveProject() {
  saveError.value = ''
  saveOk.value = false
  saving.value = true
  try {
    const res = await projectsService.update(projectId.value, {
      name: editName.value.trim(),
      description: editDescription.value.trim() || null,
    })
    const p = unwrap(res)
    project.value = p
    success('Project updated')
    saveOk.value = true
  } catch (e) {
    saveError.value = e.message || 'Update failed'
  } finally {
    saving.value = false
  }
}

async function createInvite() {
  inviteError.value = ''
  lastInviteToken.value = ''
  inviting.value = true
  try {
    const res = await projectsService.createInvitation(projectId.value, {
      email: inviteEmail.value.trim(),
      role: inviteRole.value,
    })
    const out = unwrap(res)
    lastInviteToken.value = out.token || ''
    lastInviteExpires.value = out.expires_at ? String(out.expires_at) : ''
    lastInvitePath.value = out.accept_path || ''
    success('Invitation created')
    inviteEmail.value = ''
  } catch (e) {
    inviteError.value = e.message || 'Invitation failed'
  } finally {
    inviting.value = false
  }
}

async function copyToken(text) {
  try {
    await navigator.clipboard.writeText(text)
    success('Copied')
  } catch {
    toastError('Could not copy')
  }
}

watch(
  projectId,
  id => {
    if (!id) return
    loadProject()
    loadMembers()
  },
  { immediate: true }
)
</script>
