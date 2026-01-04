import { ref, computed, onMounted } from 'vue'
import {
  initKeycloak,
  login,
  logout,
  isAuthenticated,
  getUserInfo,
  getRoles,
  hasRole,
} from '../services/keycloak.js'

// Global authentication state
const authenticated = ref(false)
const user = ref(null)
const loading = ref(true)

/**
 * Composable for authentication state and methods
 */
export function useAuth() {
  /**
   * Initialize Keycloak and check authentication status
   */
  const checkAuth = async () => {
    try {
      loading.value = true
      const authStatus = await initKeycloak()
      authenticated.value = authStatus
      
      if (authStatus) {
        user.value = getUserInfo()
      } else {
        user.value = null
      }
    } catch (error) {
      console.error('Authentication check failed:', error)
      authenticated.value = false
      user.value = null
    } finally {
      loading.value = false
    }
  }

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
  const userHasRole = (role) => {
    return hasRole(role)
  }

  /**
   * Get user roles
   */
  const userRoles = computed(() => {
    return getRoles()
  })

  // Initialize on mount
  onMounted(() => {
    if (loading.value) {
      checkAuth()
    }
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
