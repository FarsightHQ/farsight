<template>
  <PageFrame
    class="flex-1 min-h-0 flex flex-col"
    :breadcrumb-items="breadcrumbItems"
    :title="pageTitle"
    :subtitle="pageSubtitle"
  >
    <div class="w-full max-w-6xl mx-auto">
      <ProjectOverviewSkeleton v-if="loading" />

      <ErrorCallout v-else-if="loadError" variant="inline" :message="loadError" />

      <div v-else-if="project" class="space-y-8">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        <!-- Left: project details -->
        <Card class="p-6 space-y-5">
          <div>
            <h2 class="text-lg font-semibold text-theme-text-content">Project information</h2>
            <p class="text-sm text-theme-text-muted mt-1">
              Name and description for this workspace. Saving changes requires
              <span class="font-medium text-theme-text-content">admin</span> access; if save fails,
              your account may be viewer or member only.
            </p>
          </div>

          <form class="space-y-4" @submit.prevent="saveProject">
            <Input v-model="editName" label="Name" placeholder="Project name" required />
            <div>
              <label
                for="project-description"
                class="block text-sm font-medium text-theme-text-content mb-1"
              >
                Description
              </label>
              <textarea
                id="project-description"
                v-model="editDescription"
                rows="4"
                class="input"
                placeholder="Optional description"
              />
            </div>

            <div class="flex flex-wrap items-center gap-3 pt-1">
              <Button type="submit" variant="primary" :disabled="saving">
                {{ saving ? 'Saving…' : 'Save changes' }}
              </Button>
              <p v-if="saveError" class="text-sm text-error-600">{{ saveError }}</p>
            </div>
          </form>
        </Card>

        <!-- Right: invite first, then members -->
        <div class="space-y-6">
          <Card class="p-6 space-y-4">
            <div>
              <h2 class="text-lg font-semibold text-theme-text-content">Invite by email</h2>
              <p class="text-sm text-theme-text-muted mt-1">
                Creates an invitation token (admins only). Share the token securely with the
                invitee.
              </p>
            </div>
            <form class="space-y-4" @submit.prevent="createInvite">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  v-model="inviteEmail"
                  type="email"
                  label="Email"
                  placeholder="colleague@company.com"
                  required
                />
                <div>
                  <label
                    for="invite-role"
                    class="block text-sm font-medium text-theme-text-content mb-1"
                  >
                    Role
                  </label>
                  <select id="invite-role" v-model="inviteRole" class="input w-full">
                    <option value="viewer">Viewer</option>
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <Button type="submit" variant="primary" :disabled="inviting">
                {{ inviting ? 'Creating…' : 'Create invitation' }}
              </Button>
            </form>
            <p v-if="inviteError" class="text-sm text-error-600">{{ inviteError }}</p>
            <div
              v-if="lastInviteToken"
              class="rounded-lg border border-theme-border-default bg-theme-content p-4 text-sm space-y-2"
            >
              <p class="font-medium text-theme-text-content">Invitation token (copy once)</p>
              <code class="block text-xs break-all select-all text-theme-text-content">{{
                lastInviteToken
              }}</code>
              <p class="text-xs text-theme-text-muted">
                Expires: {{ lastInviteExpires }}. Accept via API: {{ lastInvitePath }}
              </p>
              <Button type="button" variant="outline" size="sm" @click="copyToken(lastInviteToken)">
                Copy token
              </Button>
            </div>
          </Card>

          <Card class="p-6 space-y-4">
            <h2 class="text-lg font-semibold text-theme-text-content">Members</h2>
            <p v-if="membersLoading" class="text-sm text-theme-text-muted">Loading members…</p>
            <p v-else-if="membersError" class="text-sm text-error-600">{{ membersError }}</p>
            <p v-else-if="members.length === 0" class="text-sm text-theme-text-muted">
              No members yet. Use invite by email to add people to this project.
            </p>
            <ul
              v-else
              class="divide-y divide-theme-border-default rounded-lg border border-theme-border-default overflow-hidden"
            >
              <li
                v-for="m in members"
                :key="m.user_sub"
                class="px-4 py-3 flex justify-between gap-4 text-sm bg-theme-card"
              >
                <code class="text-xs break-all text-theme-text-content">{{ m.user_sub }}</code>
                <span class="text-theme-text-muted shrink-0 capitalize">{{ m.role }}</span>
              </li>
            </ul>
          </Card>
        </div>
      </div>

      <Card
        v-if="canDeleteProject"
        class="p-6 border border-error-200 bg-theme-content max-w-6xl mx-auto"
      >
        <h2 class="text-lg font-semibold text-theme-text-content">Danger zone</h2>
        <p class="text-sm text-theme-text-muted mt-2 max-w-2xl">
          Delete this project permanently. This removes all FAR requests (uploaded files and firewall
          rules), members, invitations, and this project’s links to assets. Global asset registry
          rows remain (other projects may still reference the same IP).
        </p>
        <div class="mt-4">
          <Button type="button" variant="danger" @click="openDeleteProjectModal">
            Delete project
          </Button>
        </div>
      </Card>
      </div>

    <Modal v-model="showDeleteProjectModal" title="Delete project" size="md">
      <div class="space-y-4 text-sm text-theme-text-content">
        <p>This cannot be undone. You must type the project slug to confirm.</p>
        <ul class="list-disc list-inside text-theme-text-muted space-y-1">
          <li>All FAR requests and their uploaded files</li>
          <li>All firewall rules derived from those requests</li>
          <li>Members and invitations</li>
          <li>Asset links for this project only</li>
        </ul>
        <div>
          <label class="block text-sm font-medium text-theme-text-content mb-1">
            Type slug <code class="text-xs bg-theme-card px-1 rounded">{{ project?.slug }}</code>
          </label>
          <input
            v-model="deleteSlugConfirm"
            type="text"
            class="input w-full"
            autocomplete="off"
            placeholder="project-slug"
          />
        </div>
      </div>
      <template #footer>
        <Button variant="outline" :disabled="deletingProject" @click="showDeleteProjectModal = false">
          Cancel
        </Button>
        <Button
          variant="danger"
          :disabled="deletingProject || deleteSlugConfirm !== (project?.slug || '')"
          @click="confirmDeleteProject"
        >
          {{ deletingProject ? 'Deleting…' : 'Delete project' }}
        </Button>
      </template>
    </Modal>
    </div>
  </PageFrame>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectsService } from '@/services/projects'
import { useToast } from '@/composables/useToast'
import { useAuth } from '@/composables/useAuth'
import { getActiveProjectId, setActiveProjectId } from '@/utils/projectContext'
import PageFrame from '@/components/layout/PageFrame.vue'
import ProjectOverviewSkeleton from '@/components/ui/ProjectOverviewSkeleton.vue'
import ErrorCallout from '@/components/ui/ErrorCallout.vue'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Modal from '@/components/ui/Modal.vue'
import { usePageBreadcrumbs } from '@/composables/usePageBreadcrumbs'

const route = useRoute()
const router = useRouter()
const { user } = useAuth()
const { breadcrumbItems, projectName: breadcrumbProjectName } = usePageBreadcrumbs()
const { success, error: toastError } = useToast()

const projectId = computed(() => route.params.projectId)

const pageTitle = computed(() => project.value?.name || breadcrumbProjectName.value || 'Project')
const pageSubtitle = computed(() => (project.value?.slug ? `slug: ${project.value.slug}` : ''))

const project = ref(null)
const loading = ref(true)
const loadError = ref('')

const editName = ref('')
const editDescription = ref('')
const saving = ref(false)
const saveError = ref('')

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

const showDeleteProjectModal = ref(false)
const deleteSlugConfirm = ref('')
const deletingProject = ref(false)

const canDeleteProject = computed(() => {
  const u = user.value
  if (!u?.sub || !project.value) return false
  if (project.value.slug === 'default') return false
  return members.value.some(m => m.user_sub === u.sub && m.role === 'owner')
})

function openDeleteProjectModal() {
  deleteSlugConfirm.value = ''
  showDeleteProjectModal.value = true
}

async function confirmDeleteProject() {
  if (!project.value || deleteSlugConfirm.value !== project.value.slug) return
  deletingProject.value = true
  try {
    await projectsService.delete(projectId.value)
    success('Project deleted')
    showDeleteProjectModal.value = false
    if (String(getActiveProjectId()) === String(projectId.value)) {
      setActiveProjectId(null)
    }
    router.push({ name: 'Projects' })
  } catch (e) {
    toastError(e.message || 'Failed to delete project')
  } finally {
    deletingProject.value = false
  }
}

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
  saving.value = true
  try {
    const res = await projectsService.update(projectId.value, {
      name: editName.value.trim(),
      description: editDescription.value.trim() || null,
    })
    const p = unwrap(res)
    project.value = p
    success('Project updated')
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
