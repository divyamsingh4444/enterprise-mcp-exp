"""
OpenTelemetry instrumentation and tracing setup.
Exports spans to Jaeger for distributed tracing.
"""

from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
import os
import logging

logger = logging.getLogger(__name__)

# Jaeger configuration
JAEGER_HOST = os.getenv("JAEGER_HOST", "localhost")
JAEGER_PORT = int(os.getenv("JAEGER_PORT", "6831"))
JAEGER_SAMPLER = os.getenv("JAEGER_SAMPLER", "const")  # const, probabilistic, etc.
JAEGER_SAMPLER_PARAM = float(os.getenv("JAEGER_SAMPLER_PARAM", "1.0"))  # 1.0 = sample all

# Initialize Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name=JAEGER_HOST,
    agent_port=JAEGER_PORT,
)

# Create resource
resource = Resource(attributes={
    SERVICE_NAME: "enterprise-mcp-server",
    "environment": os.getenv("ENVIRONMENT", "development"),
})

# Initialize tracer provider
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(trace_provider)

# Get global tracer
tracer = trace.get_tracer(__name__)

logger.info(f"OpenTelemetry initialized - Jaeger at {JAEGER_HOST}:{JAEGER_PORT}")
