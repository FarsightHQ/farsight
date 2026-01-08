import { WebTracerProvider } from '@opentelemetry/sdk-trace-web'
import { Resource } from '@opentelemetry/resources'
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions'
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-web'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http'
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch'
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load'
import { registerInstrumentations } from '@opentelemetry/instrumentation'
import { trace, context, SpanStatusCode } from '@opentelemetry/api'

/**
 * Error-based sampler implementation
 * - 100% sampling for error traces (HTTP status >= 400, exceptions)
 * - 10% sampling for success traces
 */
class ErrorBasedSampler {
  constructor(options = {}) {
    this.errorSampleRate = options.errorSampleRate ?? 1.0 // 100% for errors
    this.successSampleRate = options.successSampleRate ?? 0.1 // 10% for success
  }

  shouldSample(context, traceId, spanName, spanKind, attributes, links) {
    // Check if this is an error span based on attributes
    const isError = this._isErrorSpan(attributes)
    
    // For error spans, always sample
    if (isError) {
      return {
        decision: 1, // RECORD_AND_SAMPLE
        attributes: {},
      }
    }

    // For success spans, use probabilistic sampling
    // Use traceId as seed for consistent sampling within a trace
    const traceIdHash = this._hashTraceId(traceId)
    const sampleRate = isError ? this.errorSampleRate : this.successSampleRate
    
    if (traceIdHash < sampleRate) {
      return {
        decision: 1, // RECORD_AND_SAMPLE
        attributes: {},
      }
    }

    return {
      decision: 0, // NOT_RECORD
      attributes: {},
    }
  }

  _isErrorSpan(attributes) {
    if (!attributes) return false
    
    // Check for HTTP error status codes
    const httpStatusCode = attributes['http.status_code']
    if (httpStatusCode !== undefined && httpStatusCode >= 400) {
      return true
    }

    // Check for error flag
    if (attributes['error'] === true) {
      return true
    }

    // Check for exception attributes
    if (attributes['exception.type'] || attributes['exception.message']) {
      return true
    }

    return false
  }

  _hashTraceId(traceId) {
    // Simple hash function to convert traceId to a number between 0 and 1
    // Use the last 8 characters of traceId for consistent sampling
    const hash = traceId.slice(-8)
    const num = parseInt(hash, 16)
    return (num % 10000) / 10000
  }
}

/**
 * Initialize OpenTelemetry tracing for the frontend
 */
export function initTracing() {
  // Check if OTEL is enabled
  const otelEnabled = import.meta.env.VITE_OTEL_ENABLED !== 'false'
  if (!otelEnabled) {
    console.log('OpenTelemetry tracing is disabled')
    return
  }

  // Get configuration from environment variables
  const otlpEndpoint = 
    import.meta.env.VITE_OTEL_EXPORTER_OTLP_ENDPOINT || 
    'http://localhost:4318/v1/traces'
  const serviceName = 
    import.meta.env.VITE_OTEL_SERVICE_NAME || 
    'farsight-frontend'

  // Create resource with service information
  const resource = new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    [SemanticResourceAttributes.SERVICE_VERSION]: '2.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 
      import.meta.env.MODE || 'development',
  })

  // Create OTLP exporter
  const exporter = new OTLPTraceExporter({
    url: otlpEndpoint,
    headers: {},
  })

  // Create tracer provider with error-based sampler
  const tracerProvider = new WebTracerProvider({
    resource,
    sampler: new ErrorBasedSampler({
      errorSampleRate: parseFloat(
        import.meta.env.VITE_OTEL_TRACE_ERROR_SAMPLE_RATE || '1.0'
      ),
      successSampleRate: parseFloat(
        import.meta.env.VITE_OTEL_TRACE_SAMPLE_RATE || '0.1'
      ),
    }),
  })

  // Add span processor
  tracerProvider.addSpanProcessor(new BatchSpanProcessor(exporter))

  // Register the provider
  tracerProvider.register()

  // Register auto-instrumentations
  registerInstrumentations({
    instrumentations: [
      new FetchInstrumentation({
        // Capture request/response headers for better trace context
        propagateTraceHeaderCorsUrls: [
          /^https?:\/\/localhost/,
          /^https?:\/\/.*\.local/,
          new RegExp(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'),
        ],
        // Clear timings to avoid conflicts
        clearTimingResources: true,
        // Apply custom attributes
        applyCustomAttributesOnSpan: (span, request, response) => {
          if (response) {
            const statusCode = response.status
            span.setAttribute('http.status_code', statusCode)
            
            // Mark as error if status >= 400
            if (statusCode >= 400) {
              span.setStatus({
                code: SpanStatusCode.ERROR,
                message: `HTTP ${statusCode}`,
              })
              span.setAttribute('error', true)
            }
          }
        },
      }),
      new DocumentLoadInstrumentation({
        // Capture document load performance
        enabled: true,
      }),
    ],
  })

  console.log(`OpenTelemetry tracing initialized for ${serviceName}`)
  console.log(`OTLP endpoint: ${otlpEndpoint}`)

  return tracerProvider
}
