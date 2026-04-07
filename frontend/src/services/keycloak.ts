import Keycloak from 'keycloak-js'

const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'farsight',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'farsight-frontend',
}

// Initialize Keycloak instance
const keycloak = new Keycloak(keycloakConfig)

// Token refresh settings
const TOKEN_REFRESH_BUFFER = 5 * 60 * 1000 // 5 minutes before expiration

let tokenRefreshTimer = null

/**
 * Initialize Keycloak and check authentication status
 * @param {Object} options - Initialization options
 * @returns {Promise<boolean>} - True if authenticated, false otherwise
 */
export async function initKeycloak(options = {}) {
  try {
    const authenticated = await keycloak.init({
      onLoad: 'check-sso', // Check SSO status without redirecting
      checkLoginIframe: false, // Disable iframe check for better performance
      pkceMethod: 'S256', // Use PKCE for security
      ...options,
    })

    if (authenticated) {
      setupTokenRefresh()
      keycloak.onTokenExpired = () => {
        refreshToken()
      }
    }

    return authenticated
  } catch (error) {
    console.error('Keycloak initialization error:', error)
    return false
  }
}

/**
 * Setup automatic token refresh
 */
function setupTokenRefresh() {
  if (tokenRefreshTimer) {
    clearTimeout(tokenRefreshTimer)
  }

  const tokenParsed = keycloak.tokenParsed
  if (tokenParsed && tokenParsed.exp) {
    const expirationTime = tokenParsed.exp * 1000 // Convert to milliseconds
    const currentTime = Date.now()
    const timeUntilExpiration = expirationTime - currentTime
    const refreshTime = Math.max(timeUntilExpiration - TOKEN_REFRESH_BUFFER, 0)

    tokenRefreshTimer = setTimeout(() => {
      refreshToken()
    }, refreshTime)
  }
}

/**
 * Login - Redirect to Keycloak login page
 * @param {Object} options - Login options (redirectUri, etc.)
 */
export function login(options = {}) {
  keycloak.login(options)
}

/**
 * Logout - Logout and clear session
 * @param {Object} options - Logout options (redirectUri, etc.)
 */
export function logout(options = {}) {
  if (tokenRefreshTimer) {
    clearTimeout(tokenRefreshTimer)
    tokenRefreshTimer = null
  }
  // Set default redirect URI to home page if not provided
  // Use simple path to avoid URI length issues
  const defaultRedirectUri = window.location.origin + '/'
  const logoutOptions = {
    redirectUri: options.redirectUri || defaultRedirectUri,
  }
  keycloak.logout(logoutOptions)
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
export function isAuthenticated() {
  return keycloak.authenticated || false
}

/**
 * Get current access token
 * @returns {string|null}
 */
export function getToken() {
  return keycloak.token || null
}

/**
 * Refresh access token
 * @returns {Promise<boolean>}
 */
export async function refreshToken() {
  try {
    const refreshed = await keycloak.updateToken(30) // Refresh if expires within 30 seconds
    if (refreshed) {
      setupTokenRefresh()
      return true
    }
    return false
  } catch (error) {
    console.error('Token refresh error:', error)
    // If refresh fails, user needs to login again
    logout()
    return false
  }
}

/**
 * Get user information from token
 * @returns {Object|null}
 */
export function getUserInfo() {
  if (!keycloak.authenticated || !keycloak.tokenParsed) {
    return null
  }

  const token = keycloak.tokenParsed
  return {
    sub: token.sub,
    username: token.preferred_username || token.username,
    email: token.email,
    name: token.name,
    givenName: token.given_name,
    familyName: token.family_name,
    roles: getRoles(),
  }
}

/**
 * Get user roles from token
 * @returns {Array<string>}
 */
export function getRoles() {
  if (!keycloak.authenticated || !keycloak.tokenParsed) {
    return []
  }

  const token = keycloak.tokenParsed
  const roles = []

  // Get realm roles
  if (token.realm_access && token.realm_access.roles) {
    roles.push(...token.realm_access.roles)
  }

  // Get client-specific roles
  if (token.resource_access) {
    const clientAccess = token.resource_access[keycloakConfig.clientId]
    if (clientAccess && clientAccess.roles) {
      roles.push(...clientAccess.roles)
    }
  }

  return roles
}

/**
 * Check if user has a specific role
 * @param {string} role - Role name to check
 * @returns {boolean}
 */
export function hasRole(role) {
  const roles = getRoles()
  return roles.includes(role)
}

/**
 * Get Keycloak instance (for advanced usage)
 * @returns {Keycloak}
 */
export function getKeycloakInstance() {
  return keycloak
}

export default keycloak
