"""
OpenTelemetry observability initialization module

Configures distributed tracing with error-based sampling:
- 100% sampling for error traces (4xx, 5xx, exceptions)
- 10% sampling for success traces
"""
import logging
import random
from typing import Optional

from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, Tracer
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.sampling import (
    Decision,
    SamplingResult,
    Sampler,
    RECORD_AND_SAMPLE,
    DROP,
)
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semantic_conventions.resource import (
    DEPLOYMENT_ENVIRONMENT,
    SERVICE_NAME as SEMCONV_SERVICE_NAME,
)

# Instrumentation packages
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from app.core.config import settings

logger = logging.getLogger(__name__)


class ErrorBasedSampler(Sampler):
    """
    Custom sampler that implements error-based sampling:
    - 100% sampling for error spans (http.status_code >= 400, exceptions, error status)
    - Configurable sampling rate for success spans (default 10%)
    """

    def __init__(
        self,
        success_sample_rate: float = 0.1,
        error_sample_rate: float = 1.0,
    ):
        """
        Initialize the error-based sampler.

        Args:
            success_sample_rate: Probability of sampling success spans (0.0 to 1.0)
            error_sample_rate: Probability of sampling error spans (0.0 to 1.0)
        """
        if not 0.0 <= success_sample_rate <= 1.0:
            raise ValueError("success_sample_rate must be between 0.0 and 1.0")
        if not 0.0 <= error_sample_rate <= 1.0:
            raise ValueError("error_sample_rate must be between 0.0 and 1.0")

        self.success_sample_rate = success_sample_rate
        self.error_sample_rate = error_sample_rate

    def should_sample(
        self,
        context: Optional[trace.SpanContext],
        trace_id: int,
        name: str,
        kind: Optional[trace.SpanKind] = None,
        attributes: Optional[dict] = None,
        links: Optional[list] = None,
        parent_context: Optional[trace.SpanContext] = None,
    ) -> SamplingResult:
        """
        Determine whether to sample a span based on error status.

        Args:
            context: Current span context
            trace_id: Trace ID
            name: Span name
            kind: Span kind
            attributes: Span attributes (may contain error indicators)
            links: Span links
            parent_context: Parent span context

        Returns:
            SamplingResult with decision and attributes
        """
        # If parent is sampled, always sample child to maintain trace consistency
        if parent_context and parent_context.trace_flags.sampled:
            return SamplingResult(
                decision=RECORD_AND_SAMPLE,
                attributes={},
            )

        # Check for error indicators in attributes
        is_error = False
        if attributes:
            # Check HTTP status code
            http_status = attributes.get("http.status_code")
            if http_status is not None and isinstance(http_status, (int, str)):
                try:
                    status_code = int(http_status)
                    if status_code >= 400:
                        is_error = True
                except (ValueError, TypeError):
                    pass

            # Check for exception attributes
            if any(
                key.startswith("exception.")
                or key in ("error", "error.type", "error.message")
                for key in attributes.keys()
            ):
                is_error = True

        # Check span status if available (for already completed spans)
        # Note: This is typically not available during sampling, but included for completeness
        if hasattr(context, "status") and context.status:
            if context.status.status_code == StatusCode.ERROR:
                is_error = True

        # Apply sampling based on error status
        if is_error:
            # Error spans: use error_sample_rate
            should_sample = random.random() < self.error_sample_rate
        else:
            # Success spans: use success_sample_rate
            should_sample = random.random() < self.success_sample_rate

        decision = RECORD_AND_SAMPLE if should_sample else DROP

        return SamplingResult(
            decision=decision,
            attributes={
                "sampling.rate": (
                    self.error_sample_rate if is_error else self.success_sample_rate
                ),
                "sampling.reason": "error" if is_error else "success",
            },
        )

    def __repr__(self) -> str:
        return (
            f"ErrorBasedSampler(success={self.success_sample_rate}, "
            f"error={self.error_sample_rate})"
        )


def initialize_observability() -> None:
    """
    Initialize OpenTelemetry observability with error-based sampling.

    This function:
    1. Configures the TracerProvider with error-based sampling
    2. Sets up OTLP gRPC exporter
    3. Auto-instruments FastAPI, SQLAlchemy, httpx, and requests
    4. Configures resource attributes (service name, environment, version)
    """
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry is disabled. Skipping observability initialization.")
        return

    try:
        # Create resource with service metadata
        resource = Resource.create(
            {
                SEMCONV_SERVICE_NAME: settings.OTEL_SERVICE_NAME,
                DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
                SERVICE_VERSION: "2.0.0",  # Match API version from main.py
            }
        )

        # Create error-based sampler
        sampler = ErrorBasedSampler(
            success_sample_rate=settings.OTEL_TRACE_SAMPLE_RATE,
            error_sample_rate=settings.OTEL_TRACE_ERROR_SAMPLE_RATE,
        )

        # Create and configure TracerProvider
        tracer_provider = TracerProvider(
            resource=resource,
            sampler=sampler,
        )

        # Configure OTLP gRPC exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            insecure=True,  # Use insecure for local development
        )

        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)

        logger.info(
            f"OpenTelemetry initialized: service={settings.OTEL_SERVICE_NAME}, "
            f"endpoint={settings.OTEL_EXPORTER_OTLP_ENDPOINT}, "
            f"sampling=success:{settings.OTEL_TRACE_SAMPLE_RATE}, "
            f"error:{settings.OTEL_TRACE_ERROR_SAMPLE_RATE}"
        )

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}", exc_info=True)
        # Don't raise - allow application to continue without observability
        return

    # Note: FastAPI instrumentation will be done via instrument_app() after app creation
    # This ensures the app instance is properly instrumented

    # Auto-instrument SQLAlchemy
    try:
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    # Auto-instrument httpx
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("httpx instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument httpx: {e}")

    # Auto-instrument requests
    try:
        RequestsInstrumentor().instrument()
        logger.info("requests instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument requests: {e}")


def instrument_fastapi_app(app: FastAPI) -> None:
    """
    Instrument a FastAPI application instance with OpenTelemetry.

    This should be called after the FastAPI app is created but before
    it starts handling requests.

    Args:
        app: FastAPI application instance
    """
    if not settings.OTEL_ENABLED:
        return

    try:
        FastAPIInstrumentor().instrument_app(app)
        logger.info("FastAPI app instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI app: {e}")


def get_tracer(name: str) -> Tracer:
    """
    Get a tracer instance for manual span creation.

    Args:
        name: Tracer name (typically __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)
