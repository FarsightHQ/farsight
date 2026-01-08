import axios from 'axios'
import { getToken, refreshToken, isAuthenticated, login } from './keycloak.js'
import { context, propagation, trace, SpanStatusCode } from '@opentelemetry/api'

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
  async (config) => {
    // Add auth token if available
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add trace context headers (W3C Trace Context) for distributed tracing
    const activeContext = context.active()
    const headers = {}
    propagation.inject(activeContext, headers)
    
    // Merge trace context headers into request headers
    Object.keys(headers).forEach((key) => {
      config.headers[key] = headers[key]
    })

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response) => {
    // Handle standardized response format
    if (response.data && response.data.data) {
      return response.data
    }
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return apiClient(originalRequest)
          })
          .catch((err) => {
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
      // Server responded with error - capture for 100% sampling
      const statusCode = error.response.status
      const activeSpan = trace.getActiveSpan()
      
      // Mark the span as error for 100% sampling
      if (activeSpan) {
        activeSpan.setAttribute('http.status_code', statusCode)
        activeSpan.setAttribute('error', true)
        if (statusCode >= 400) {
          activeSpan.setStatus({
            code: SpanStatusCode.ERROR,
            message: `HTTP ${statusCode}: ${error.response.statusText}`,
          })
        }
      }

      // Server responded with error
      const errorMessage =
        error.response.data?.detail ||
        error.response.data?.message ||
        error.response.statusText ||
        'An error occurred'
      return Promise.reject(new Error(errorMessage))
    } else if (error.request) {
      // Request made but no response - capture network errors
      const activeSpan = trace.getActiveSpan()
      if (activeSpan) {
        activeSpan.setAttribute('error', true)
        activeSpan.setAttribute('error.type', 'network_error')
        activeSpan.setStatus({
          code: SpanStatusCode.ERROR,
          message: 'Network error: No response received',
        })
      }
      return Promise.reject(new Error('Network error. Please check your connection.'))
    } else {
      // Something else happened - capture other errors
      const activeSpan = trace.getActiveSpan()
      if (activeSpan) {
        activeSpan.setAttribute('error', true)
        activeSpan.setAttribute('error.type', 'request_error')
        activeSpan.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message || 'Request error',
        })
      }
      return Promise.reject(error)
    }
  }
)

export default apiClient

