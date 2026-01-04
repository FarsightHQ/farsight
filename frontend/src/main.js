import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { initKeycloak } from './services/keycloak.js'
import './assets/css/main.css'

// Initialize Keycloak before mounting the app
async function initApp() {
  try {
    // Initialize Keycloak
    await initKeycloak()
    
    // Create and mount Vue app
    const app = createApp(App)
    app.use(router)
    app.mount('#app')
  } catch (error) {
    console.error('Failed to initialize application:', error)
    // Still mount the app even if Keycloak initialization fails
    // The router guard will handle authentication
    const app = createApp(App)
    app.use(router)
    app.mount('#app')
  }
}

// Start the application
initApp()

