"""
Observability Module - Distributed Tracing and Metrics

Provides OpenTelemetry integration for:
- Distributed tracing with W3C TraceContext
- Span instrumentation decorators
- Metrics collection (counters, histograms, gauges)
- Jaeger backend integration
"""

# Tracing disabled due to OpenTelemetry version compatibility issues
# from src.observability.tracing import (
#     initialize_tracer,
#     get_tracer,
#     shutdown_tracer,
#     set_up_instrumentation
# )

# from src.observability.instrumentation import (
#     trace_span,
#     trace_async_span,
#     add_span_event,
#     add_span_attribute,
#     record_span_exception,
#     BaggageContext,
#     extract_trace_context,
#     inject_trace_context,
#     get_trace_id,
#     get_span_id
# )

from src.observability.metrics import (
    MetricsCollector,
    get_metrics_collector,
    record_operation_duration
)

__all__ = [
    # Metrics (Tracing disabled due to version compatibility)
    "MetricsCollector",
    "get_metrics_collector",
    "record_operation_duration"
]
