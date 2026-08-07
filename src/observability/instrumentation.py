"""
Instrumentation Decorators and Context Management

Provides decorators and helpers for creating spans, managing trace context,
and propagating W3C TraceContext across requests.
"""

import functools
import logging
import time
from contextvars import ContextVar
from typing import Optional, Dict, Any, Callable

from opentelemetry import trace, baggage
from opentelemetry.trace import Status, StatusCode
from opentelemetry.propagators.jaeger.jaeger import JaegerPropagator
from opentelemetry.propagators.textmap import TextMapPropagator

logger = logging.getLogger(__name__)

# Context variables for trace context
_trace_context: ContextVar[Dict[str, str]] = ContextVar(
    "trace_context", default={}
)

_baggage_context: ContextVar[Dict[str, str]] = ContextVar(
    "baggage_context", default={}
)


def get_tracer():
    """Get the global tracer instance."""
    return trace.get_tracer(__name__)


def trace_span(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Decorator for tracing synchronous functions.
    
    Usage:
        @trace_span("auth.validate_token", {"auth.token_type": "session"})
        def validate_token(token: str):
            return verify_token(token)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                # Set attributes
                if attributes:
                    for key, value in attributes.items():
                        if value is not None:
                            span.set_attribute(key, str(value))

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(e))
                    )
                    raise

        return wrapper
    return decorator


def trace_async_span(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Decorator for tracing async functions.
    
    Usage:
        @trace_async_span("tool.execute", {"tool.name": "run_command"})
        async def execute_tool(tool_name: str, args: dict):
            return await tool_executor(tool_name, args)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(operation_name) as span:
                # Set attributes
                if attributes:
                    for key, value in attributes.items():
                        if value is not None:
                            span.set_attribute(key, str(value))

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(
                        Status(StatusCode.ERROR, description=str(e))
                    )
                    raise

        return wrapper
    return decorator


def add_span_event(event_name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Record an event in the current span.
    
    Usage:
        span = trace.get_current_span()
        add_span_event("auth.success", {"method": "email_password"})
    """
    span = trace.get_current_span()
    if span:
        span.add_event(event_name, attributes or {})


def add_span_attribute(key: str, value: Any):
    """Add an attribute to the current span."""
    span = trace.get_current_span()
    if span and value is not None:
        span.set_attribute(key, str(value))


def record_span_exception(exception: Exception, description: str = ""):
    """Record an exception in the current span."""
    span = trace.get_current_span()
    if span:
        span.record_exception(exception)
        if description:
            span.set_status(Status(StatusCode.ERROR, description=description))


class BaggageContext:
    """Context manager for setting and clearing baggage."""
    
    def __init__(self, key: str, value: str):
        """
        Initialize baggage context.
        
        Usage:
            with BaggageContext("org_id", "tenant-123"):
                # org_id will be propagated in baggage
                tool_call()
        """
        self.key = key
        self.value = value
        self.token = None

    def __enter__(self):
        """Set baggage context."""
        self.token = baggage.set_baggage(self.key, self.value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear baggage context."""
        if self.token:
            baggage.delete_baggage(self.key, self.token)


def extract_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Extract W3C TraceContext from HTTP headers.
    
    Returns:
        Dictionary with traceparent and tracestate
    """
    propagator = TextMapPropagator()
    context = propagator.extract(headers)
    
    # Store in context var for later use
    trace_context = {
        "traceparent": headers.get("traceparent", ""),
        "tracestate": headers.get("tracestate", ""),
    }
    _trace_context.set(trace_context)
    
    return trace_context


def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject W3C TraceContext into HTTP headers.
    
    Usage:
        headers = {}
        inject_trace_context(headers)
        # Now headers contains traceparent and tracestate
    """
    propagator = JaegerPropagator()
    propagator.inject(headers)
    return headers


def get_trace_id() -> Optional[str]:
    """Get current trace ID from active span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        return hex(span.get_span_context().trace_id)
    return None


def get_span_id() -> Optional[str]:
    """Get current span ID from active span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        return hex(span.get_span_context().span_id)
    return None
