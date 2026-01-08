import { trace, context, SpanStatusCode } from '@opentelemetry/api'

/**
 * Global error handler for JavaScript errors
 * Creates error spans and links them to active traces
 */
export function initErrorHandler() {
  // Check if OTEL is enabled
  const otelEnabled = import.meta.env.VITE_OTEL_ENABLED !== 'false'
  if (!otelEnabled) {
    return
  }

  const tracer = trace.getTracer('farsight-frontend-error-handler')

  // Handle unhandled JavaScript errors
  window.addEventListener('error', (event) => {
    handleError({
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error,
      type: 'unhandled_error',
    })
  })

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    handleError({
      message: event.reason?.message || String(event.reason),
      error: event.reason,
      type: 'unhandled_promise_rejection',
    })
  })

  /**
   * Create an error span and link it to the active trace
   */
  function handleError(errorInfo) {
    const activeSpan = trace.getActiveSpan()
    const span = tracer.startSpan('javascript.error', {
      kind: 1, // SPAN_KIND_INTERNAL
      attributes: {
        'error.type': errorInfo.type || 'unknown',
        'error.message': errorInfo.message || 'Unknown error',
        'error.filename': errorInfo.filename || '',
        'error.lineno': errorInfo.lineno || 0,
        'error.colno': errorInfo.colno || 0,
        'error': true,
      },
    })

    // Add stack trace if available
    if (errorInfo.error && errorInfo.error.stack) {
      span.setAttribute('error.stack', errorInfo.error.stack)
    }

    // Add error name and type
    if (errorInfo.error) {
      span.setAttribute('exception.type', errorInfo.error.name || 'Error')
      if (errorInfo.error.message) {
        span.setAttribute('exception.message', errorInfo.error.message)
      }
    }

    // Set error status
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: errorInfo.message || 'JavaScript error',
    })

    // Link to active span if available
    if (activeSpan) {
      const activeContext = trace.setSpan(context.active(), activeSpan)
      context.with(activeContext, () => {
        span.end()
      })
    } else {
      span.end()
    }

    // Log to console for debugging (optional, can be removed in production)
    console.error('Captured error for tracing:', errorInfo)
  }

  // Vue error handler (will be registered in main.js)
  return {
    /**
     * Vue error handler function
     * Can be used with app.config.errorHandler
     */
    vueErrorHandler: (err, instance, info) => {
      const activeSpan = trace.getActiveSpan()
      const span = tracer.startSpan('vue.error', {
        kind: 1, // SPAN_KIND_INTERNAL
        attributes: {
          'error.type': 'vue_error',
          'error.message': err?.message || String(err),
          'vue.error.info': info || '',
          'error': true,
        },
      })

      // Add error details
      if (err) {
        span.setAttribute('exception.type', err.name || 'Error')
        span.setAttribute('exception.message', err.message || String(err))
        if (err.stack) {
          span.setAttribute('error.stack', err.stack)
        }
      }

      // Add Vue component info if available
      if (instance) {
        span.setAttribute('vue.component.name', instance.$options?.name || 'Unknown')
      }

      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: err?.message || 'Vue error',
      })

      if (activeSpan) {
        const activeContext = trace.setSpan(context.active(), activeSpan)
        context.with(activeContext, () => {
          span.end()
        })
      } else {
        span.end()
      }

      console.error('Captured Vue error for tracing:', err, info)
    },
  }
}
