"""
OpenTelemetry Distributed Tracing Setup

Configures OTLP exporter, tracer provider, and instrumentation for
all operations: auth, tool execution, container management.
"""

import logging
import os
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None
_tracer_provider: Optional[TracerProvider] = None


def initialize_tracer() -> trace.Tracer:
    """
    Initialize OpenTelemetry tracer with Jaeger exporter.
    
    Returns:
        Configured tracer instance
    """
    global _tracer, _tracer_provider

    if _tracer is not None:
        return _tracer

    # Get environment configuration
    jaeger_host = os.getenv("JAEGER_HOST", "localhost")
    jaeger_port = int(os.getenv("JAEGER_PORT", "6831"))
    service_name = os.getenv("SERVICE_NAME", "enterprise-mcp")
    service_version = os.getenv("SERVICE_VERSION", "0.1.0")

    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )

    # Create resource with service metadata
    resource = Resource(
        attributes={
            SERVICE_NAME: service_name,
            "service.version": service_version,
            "environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)
    _tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    # Get tracer
    _tracer = trace.get_tracer(__name__, version=service_version)

    logger.info(
        f"OpenTelemetry tracer initialized: {service_name}@{service_version} "
        f"→ Jaeger({jaeger_host}:{jaeger_port})"
    )

    return _tracer


def get_tracer() -> trace.Tracer:
    """Get initialized tracer (initializes if needed)."""
    global _tracer
    if _tracer is None:
        initialize_tracer()
    return _tracer


def shutdown_tracer():
    """Shutdown tracer and flush pending spans."""
    global _tracer_provider
    if _tracer_provider is not None:
        _tracer_provider.force_flush()
        logger.info("OpenTelemetry tracer shutdown")


def set_up_instrumentation():
    """
    Enable automatic instrumentation for supported libraries.
    
    Instruments:
    - Starlette/FastAPI (HTTP requests)
    - HTTPX (HTTP client calls)
    """
    try:
        # Instrument Starlette (must be called after app creation)
        StarletteInstrumentor().instrument()
        logger.info("Starlette instrumentation enabled")
    except Exception as e:
        logger.warning(f"Could not instrument Starlette: {e}")

    try:
        # Instrument HTTPX (HTTP client)
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation enabled")
    except Exception as e:
        logger.warning(f"Could not instrument HTTPX: {e}")
