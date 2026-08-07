"""
Metrics Collection for MCP Server Operations

Collects metrics for:
- Authentication operations (success, failure, duration)
- Scope checks (granted, denied)
- Tool execution (duration, exit code, resource usage)
- Container management (startup, cleanup)
"""

import logging
import time
from typing import Optional, Dict, Any

from opentelemetry import trace, metrics as otel_metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and records metrics for MCP operations."""
    
    def __init__(self):
        """Initialize metrics collector with meter provider."""
        self.meter = otel_metrics.get_meter(__name__)
        
        # Create counters
        self.auth_success_counter = self.meter.create_counter(
            "auth_success_total",
            description="Total successful authentication attempts",
            unit="1"
        )
        
        self.auth_failure_counter = self.meter.create_counter(
            "auth_failure_total",
            description="Total failed authentication attempts",
            unit="1"
        )
        
        self.scope_check_counter = self.meter.create_counter(
            "scope_check_total",
            description="Total scope checks performed",
            unit="1"
        )
        
        self.tool_execution_counter = self.meter.create_counter(
            "tool_execution_total",
            description="Total tool executions",
            unit="1"
        )
        
        self.container_creation_counter = self.meter.create_counter(
            "container_creation_total",
            description="Total container creations",
            unit="1"
        )
        
        # Create histograms (duration tracking)
        self.auth_duration_histogram = self.meter.create_histogram(
            "auth_validation_duration_ms",
            description="Auth validation duration in milliseconds",
            unit="ms"
        )
        
        self.tool_execution_duration_histogram = self.meter.create_histogram(
            "tool_execution_duration_ms",
            description="Tool execution duration in milliseconds",
            unit="ms"
        )
        
        self.container_startup_histogram = self.meter.create_histogram(
            "container_startup_duration_ms",
            description="Container startup duration in milliseconds",
            unit="ms"
        )
    
    def record_auth_success(
        self,
        method: str,
        duration_ms: float,
        attributes: Optional[Dict[str, str]] = None
    ):
        """Record successful authentication."""
        attrs = attributes or {}
        attrs["auth.method"] = method
        
        self.auth_success_counter.add(1, attributes=attrs)
        self.auth_duration_histogram.record(duration_ms, attributes=attrs)
        
        logger.debug(f"Auth success recorded: {method} ({duration_ms:.2f}ms)")
    
    def record_auth_failure(
        self,
        reason: str,
        attributes: Optional[Dict[str, str]] = None
    ):
        """Record failed authentication."""
        attrs = attributes or {}
        attrs["auth.failure_reason"] = reason
        
        self.auth_failure_counter.add(1, attributes=attrs)
        
        logger.debug(f"Auth failure recorded: {reason}")
    
    def record_scope_check(
        self,
        scope: str,
        granted: bool,
        attributes: Optional[Dict[str, str]] = None
    ):
        """Record scope check result."""
        attrs = attributes or {}
        attrs["scope"] = scope
        attrs["granted"] = str(granted)
        
        self.scope_check_counter.add(1, attributes=attrs)
        
        status = "GRANTED" if granted else "DENIED"
        logger.debug(f"Scope check: {scope} {status}")
    
    def record_tool_execution(
        self,
        tool_name: str,
        duration_ms: float,
        exit_code: int = 0,
        attributes: Optional[Dict[str, str]] = None
    ):
        """Record tool execution."""
        attrs = attributes or {}
        attrs["tool.name"] = tool_name
        attrs["tool.exit_code"] = str(exit_code)
        
        self.tool_execution_counter.add(1, attributes=attrs)
        self.tool_execution_duration_histogram.record(
            duration_ms, attributes=attrs
        )
        
        logger.debug(
            f"Tool execution recorded: {tool_name} "
            f"(exit={exit_code}, duration={duration_ms:.2f}ms)"
        )
    
    def record_container_creation(
        self,
        duration_ms: float,
        attributes: Optional[Dict[str, str]] = None
    ):
        """Record container creation."""
        attrs = attributes or {}
        
        self.container_creation_counter.add(1, attributes=attrs)
        self.container_startup_histogram.record(duration_ms, attributes=attrs)
        
        logger.debug(f"Container creation recorded: {duration_ms:.2f}ms")


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_operation_duration(
    operation: str,
    duration_ms: float,
    attributes: Optional[Dict[str, str]] = None
):
    """
    Record operation duration for various operations.
    
    Usage:
        start = time.time()
        result = do_operation()
        duration_ms = (time.time() - start) * 1000
        record_operation_duration("my_operation", duration_ms)
    """
    collector = get_metrics_collector()
    
    if "auth" in operation:
        collector.record_auth_success(operation, duration_ms, attributes)
    elif "tool" in operation:
        collector.record_tool_execution(operation, duration_ms, 0, attributes)
    elif "container" in operation:
        collector.record_container_creation(duration_ms, attributes)
