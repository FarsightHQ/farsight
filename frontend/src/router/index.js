import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated, login, refreshToken } from '../services/keycloak'
import { getActiveProjectId, setActiveProjectId } from '../utils/projectContext'

/** Map /segment/... → /projects/:id/segment/... */
function redirectLegacyProjectSegment(segment, to) {
  const id = getActiveProjectId()
  if (!id) {
    return { path: '/projects', query: { redirect: to.fullPath } }
  }
  const pm = to.params.pathMatch
  let extra = ''
  if (Array.isArray(pm)) {
    if (pm.length && pm[0] !== '') extra = `/${pm.join('/')}`
  } else if (pm) {
    extra = `/${pm}`
  }
  return {
    path: `/projects/${id}/${segment}${extra}`,
    query: to.query,
    hash: to.hash,
  }
}

const routes = [
  {
    path: '/',
    redirect: { name: 'Projects' },
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('../views/ProjectsManage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/projects/new',
    name: 'ProjectCreate',
    component: () => import('../views/ProjectCreate.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/projects/:projectId',
    name: 'ProjectOverview',
    component: () => import('../views/ProjectDetail.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/requests',
    name: 'Requests',
    component: () => import('../views/RequestsList.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/requests/new',
    name: 'RequestNew',
    component: () => import('../views/RequestNew.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/requests/:id',
    name: 'RequestDetail',
    component: () => import('../views/RequestDetail.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/requests/:requestId/rules/:ruleId',
    name: 'RequestRuleDetail',
    component: () => import('../views/RuleDetail.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/rules',
    name: 'AllRules',
    component: () => import('../views/AllRules.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/rules/:id',
    name: 'RuleDetail',
    component: () => import('../views/RuleDetail.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/assets',
    name: 'ProjectAssets',
    component: () => import('../views/AssetsList.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/assets/upload',
    name: 'AssetUpload',
    component: () => import('../views/AssetUpload.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/assets/:id',
    name: 'AssetDetail',
    component: () => import('../views/AssetDetail.vue'),
    meta: { requiresAuth: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/visualize/unified',
    name: 'UnifiedGraph',
    component: () => import('../views/UnifiedGraphView.vue'),
    meta: { requiresAuth: true, vizWorkspace: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/visualize/classic',
    name: 'ClassicRuleTopology',
    component: () => import('../views/ClassicRuleTopologyView.vue'),
    meta: { requiresAuth: true, vizWorkspace: true, requiresProject: true },
  },
  {
    path: '/projects/:projectId/visualize/zone-adjacency',
    name: 'ZoneAdjacency',
    component: () => import('../views/ZoneAdjacencyView.vue'),
    meta: { requiresAuth: true, vizWorkspace: true, requiresProject: true },
  },
  {
    path: '/registry/assets',
    name: 'RegistryAssets',
    component: () => import('../views/RegistryAssetsList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/registry/assets/:ip(.*)',
    name: 'RegistryAssetDetail',
    component: () => import('../views/RegistryAssetDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    redirect: '/settings/appearance',
  },
  {
    path: '/settings/appearance',
    name: 'SettingsAppearance',
    component: () => import('../views/settings/SettingsAppearanceView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings/risky-port-policy',
    name: 'SettingsRiskyPortPolicy',
    component: () => import('../views/settings/SettingsRiskyPortPolicyView.vue'),
    meta: { requiresAuth: true },
  },
  // Legacy flat URLs → nested project routes
  {
    path: '/requests/:pathMatch(.*)*',
    redirect: to => redirectLegacyProjectSegment('requests', to),
  },
  {
    path: '/rules/:pathMatch(.*)*',
    redirect: to => redirectLegacyProjectSegment('rules', to),
  },
  {
    path: '/assets/:pathMatch(.*)*',
    redirect: to => redirectLegacyProjectSegment('assets', to),
  },
  {
    path: '/visualize/:pathMatch(.*)*',
    redirect: to => redirectLegacyProjectSegment('visualize', to),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const isPublicRoute = to.matched.some(record => record.meta.public === true)
  const requiresAuth = !isPublicRoute

  if (requiresAuth) {
    if (!isAuthenticated()) {
      const redirectUri = window.location.origin + to.path
      login({ redirectUri })
      next(false)
      return
    }

    try {
      await refreshToken()
    } catch (error) {
      console.error('Token refresh failed:', error)
      const redirectUri = window.location.origin + to.path
      login({ redirectUri })
      next(false)
      return
    }
  }

  const projectId = to.params.projectId
  if (projectId != null && projectId !== '') {
    setActiveProjectId(projectId)
  }

  const needsProject = to.matched.some(record => record.meta.requiresProject === true)
  if (needsProject) {
    const resolvedId = projectId || getActiveProjectId()
    if (!resolvedId) {
      next({
        path: '/projects',
        query: { redirect: to.fullPath },
      })
      return
    }
  }

  next()
})

export default router
