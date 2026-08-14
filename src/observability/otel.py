"""
OpenTelemetry instrumentation and tracing setup.
Exports spans to Jaeger for distributed tracing via OTLP gRPC.
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
import os
import logging

logger = logging.getLogger(__name__)

# Jaeger/OTLP configuration (inside Docker, use service name 'mcp-jaeger')
JAEGER_OTLP_HOST = os.getenv("JAEGER_OTLP_HOST", "mcp-jaeger")
JAEGER_OTLP_PORT = int(os.getenv("JAEGER_OTLP_PORT", "4317"))

# Initialize OTLP gRPC exporter (Jaeger OTLP receiver)
otlp_exporter = OTLPSpanExporter(
    endpoint=f"grpc://{JAEGER_OTLP_HOST}:{JAEGER_OTLP_PORT}",
    insecure=True,
)

# Create resource
resource = Resource(attributes={
    SERVICE_NAME: "enterprise-mcp-server",
    "environment": os.getenv("ENVIRONMENT", "development"),
})

# Initialize tracer provider
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(trace_provider)

# Get global tracer
tracer = trace.get_tracer(__name__)

logger.info(f"✅ OpenTelemetry initialized - Jaeger OTLP at {JAEGER_OTLP_HOST}:{JAEGER_OTLP_PORT}")
