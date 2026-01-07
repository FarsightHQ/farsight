import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated, login, refreshToken } from '../services/keycloak.js'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }, // Requires authentication
  },
  {
    path: '/rules',
    name: 'AllRules',
    component: () => import('../views/AllRules.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/rules/:id',
    name: 'RuleDetail',
    component: () => import('../views/RuleDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/requests',
    name: 'Requests',
    component: () => import('../views/RequestsList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/requests/new',
    name: 'RequestNew',
    component: () => import('../views/RequestNew.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/requests/:id',
    name: 'RequestDetail',
    component: () => import('../views/RequestDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/requests/:requestId/rules/:ruleId',
    name: 'RequestRuleDetail',
    component: () => import('../views/RuleDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assets',
    name: 'Assets',
    component: () => import('../views/AssetsList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assets/upload',
    name: 'AssetUpload',
    component: () => import('../views/AssetUpload.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assets/:id',
    name: 'AssetDetail',
    component: () => import('../views/AssetDetail.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard to check authentication
router.beforeEach(async (to, from, next) => {
  // Require authentication by default, unless route is explicitly marked as public
  const isPublicRoute = to.matched.some((record) => record.meta.public === true)
  const requiresAuth = !isPublicRoute // Require auth by default

  if (requiresAuth) {
    // Check if user is authenticated
    if (!isAuthenticated()) {
      // Store intended destination for redirect after login
      const redirectUri = window.location.origin + to.fullPath
      login({ redirectUri })
      return
    }

    // Try to refresh token if needed
    try {
      await refreshToken()
    } catch (error) {
      console.error('Token refresh failed:', error)
      // If refresh fails, redirect to login
      const redirectUri = window.location.origin + to.fullPath
      login({ redirectUri })
      return
    }
  }

  next()
})

export default router

