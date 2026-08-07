"""
Observability Module - Distributed Tracing and Metrics

Provides OpenTelemetry integration for:
- Distributed tracing with W3C TraceContext
- Span instrumentation decorators
- Metrics collection (counters, histograms, gauges)
- Jaeger backend integration
"""

from observability.tracing import (
    initialize_tracer,
    get_tracer,
    shutdown_tracer,
    set_up_instrumentation
)

from observability.instrumentation import (
    trace_span,
    trace_async_span,
    add_span_event,
    add_span_attribute,
    record_span_exception,
    BaggageContext,
    extract_trace_context,
    inject_trace_context,
    get_trace_id,
    get_span_id
)

from observability.metrics import (
    MetricsCollector,
    get_metrics_collector,
    record_operation_duration
)

__all__ = [
    # Tracing
    "initialize_tracer",
    "get_tracer",
    "shutdown_tracer",
    "set_up_instrumentation",
    # Instrumentation
    "trace_span",
    "trace_async_span",
    "add_span_event",
    "add_span_attribute",
    "record_span_exception",
    "BaggageContext",
    "extract_trace_context",
    "inject_trace_context",
    "get_trace_id",
    "get_span_id",
    # Metrics
    "MetricsCollector",
    "get_metrics_collector",
    "record_operation_duration"
]
