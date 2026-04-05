import axios from 'axios'
import { getToken, refreshToken, isAuthenticated, login } from './keycloak.js'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor
apiClient.interceptors.request.use(
  async config => {
    // Add auth token if available
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

/** FastAPI may return detail as a string, object, or list of validation errors */
function normalizeApiDetail(detail) {
  if (detail == null) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && item.msg) return item.msg
        try {
          return JSON.stringify(item)
        } catch {
          return String(item)
        }
      })
      .join('; ')
  }
  if (typeof detail === 'object') {
    try {
      return JSON.stringify(detail)
    } catch {
      return String(detail)
    }
  }
  return String(detail)
}

apiClient.interceptors.response.use(
  response => {
    // Handle standardized response format
    if (response.data && response.data.data) {
      return response.data
    }
    return response
  },
  async error => {
    const originalRequest = error.config

    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return apiClient(originalRequest)
          })
          .catch(err => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      // Check if user is authenticated
      if (!isAuthenticated()) {
        // Not authenticated, redirect to login
        login()
        processQueue(new Error('Not authenticated'), null)
        isRefreshing = false
        return Promise.reject(error)
      }

      try {
        // Attempt to refresh token
        const refreshed = await refreshToken()
        if (refreshed) {
          const newToken = getToken()
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          processQueue(null, newToken)
          isRefreshing = false
          // Retry original request
          return apiClient(originalRequest)
        } else {
          // Refresh failed, redirect to login
          processQueue(new Error('Token refresh failed'), null)
          isRefreshing = false
          login()
          return Promise.reject(error)
        }
      } catch (refreshError) {
        processQueue(refreshError, null)
        isRefreshing = false
        login()
        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      const detail = normalizeApiDetail(data?.detail)
      const errorMessage =
        detail || data?.message || error.response.statusText || 'An error occurred'
      const err = new Error(status === 503 ? `Service unavailable: ${errorMessage}` : errorMessage)
      return Promise.reject(err)
    } else if (error.request) {
      // Request made but no response
      return Promise.reject(new Error('Network error. Please check your connection.'))
    } else {
      // Something else happened
      return Promise.reject(error)
    }
  }
)

export default apiClient
