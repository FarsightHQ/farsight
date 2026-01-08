import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { initKeycloak } from './services/keycloak.js'
import { authenticated, user } from './composables/useAuth'
import { isAuthenticated, getUserInfo } from './services/keycloak.js'
import { initTracing } from './instrumentation/tracing.js'
import { initErrorHandler } from './instrumentation/error-handler.js'
import './assets/css/main.css'

// Initialize OpenTelemetry tracing and error handler before anything else
initTracing()
const errorHandler = initErrorHandler()

// Initialize Keycloak before mounting the app
async function initApp() {
  try {
    // Initialize Keycloak
    await initKeycloak()
    
    // Set initial authentication state
    authenticated.value = isAuthenticated()
    if (authenticated.value) {
      user.value = getUserInfo()
    }
    
    // Create and mount Vue app
    const app = createApp(App)
    
    // Register Vue error handler for tracing
    if (errorHandler && errorHandler.vueErrorHandler) {
      app.config.errorHandler = errorHandler.vueErrorHandler
    }
    
    app.use(router)
    app.mount('#app')
  } catch (error) {
    console.error('Failed to initialize application:', error)
    // Still mount the app even if Keycloak initialization fails
    // The router guard will handle authentication
    authenticated.value = false
    user.value = null
    const app = createApp(App)
    
    // Register Vue error handler for tracing
    if (errorHandler && errorHandler.vueErrorHandler) {
      app.config.errorHandler = errorHandler.vueErrorHandler
    }
    
    app.use(router)
    app.mount('#app')
  }
}

// Start the application
initApp()

