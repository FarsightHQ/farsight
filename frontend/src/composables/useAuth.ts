import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  login,
  logout,
  isAuthenticated,
  getUserInfo,
  getRoles,
  hasRole,
  getKeycloakInstance,
} from '../services/keycloak'

// Global authentication state
const authenticated = ref(false)
const user = ref(null)
const loading = ref(true)

// Set up Keycloak event listeners once globally
let listenersSetup = false

function setupKeycloakListeners() {
  if (listenersSetup) return

  const keycloak = getKeycloakInstance()
  if (!keycloak) return

  // Update state when authentication succeeds
  keycloak.onAuthSuccess = () => {
    authenticated.value = isAuthenticated()
    if (authenticated.value) {
      user.value = getUserInfo()
    }
  }

  // Update state on authentication error
  keycloak.onAuthError = () => {
    authenticated.value = false
    user.value = null
  }

  // Update state on logout
  keycloak.onAuthLogout = () => {
    authenticated.value = false
    user.value = null
  }

  // Update state when token is refreshed
  keycloak.onTokenExpired = () => {
    // Token refresh will be handled by the refresh function
    // But we should update user info in case it changed
    if (isAuthenticated()) {
      user.value = getUserInfo()
    }
  }

  listenersSetup = true
}

/**
 * Check authentication status (without initializing Keycloak)
 */
function checkAuth() {
  authenticated.value = isAuthenticated()
  if (authenticated.value) {
    user.value = getUserInfo()
  } else {
    user.value = null
  }
}

/**
 * Composable for authentication state and methods
 */
export function useAuth() {
  /**
   * Login function
   */
  const handleLogin = (options = {}) => {
    login(options)
  }

  /**
   * Logout function
   */
  const handleLogout = (options = {}) => {
    logout(options)
    authenticated.value = false
    user.value = null
  }

  /**
   * Check if user has a specific role
   */
  const userHasRole = role => {
    return hasRole(role)
  }

  /**
   * Get user roles
   */
  const userRoles = computed(() => {
    return getRoles()
  })

  // Initialize on mount - Keycloak is already initialized in main.js
  onMounted(() => {
    // Set up Keycloak event listeners if not already done
    setupKeycloakListeners()
    // Check current authentication status
    checkAuth()
    loading.value = false
  })

  return {
    // State
    authenticated: computed(() => authenticated.value),
    user: computed(() => user.value),
    loading: computed(() => loading.value),

    // Methods
    checkAuth,
    login: handleLogin,
    logout: handleLogout,
    hasRole: userHasRole,
    roles: userRoles,
  }
}

// Export reactive state for global access
export { authenticated, user, loading }
