"""Metrics Collection for MCP Server Operations (Simplified)"""

import logging
from typing import Optional, Dict, Any
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Simple metrics collector without external dependencies."""

    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.histograms: Dict[str, list] = defaultdict(list)
        self.start_time = time.time()

    def increment(self, metric: str, value: int = 1):
        """Increment a counter metric."""
        self.counters[metric] += value

    def record_duration(self, metric: str, duration_ms: float):
        """Record a duration metric."""
        self.histograms[metric].append(duration_ms)

    def record_tool_execution_duration(self, duration_ms: float):
        """Record tool execution duration."""
        self.record_duration("tool_execution_duration_ms", duration_ms)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        lines.append("# HELP mcp_counters MCP operation counters")
        lines.append("# TYPE mcp_counters counter")

        for counter_name, value in self.counters.items():
            lines.append(f"mcp_counter{{name=\"{counter_name}\"}} {value}")

        lines.append("# HELP mcp_durations MCP operation durations")
        lines.append("# TYPE mcp_durations histogram")

        for hist_name, values in self.histograms.items():
            if values:
                avg = sum(values) / len(values)
                lines.append(f"mcp_duration_ms{{name=\"{hist_name}\",quantile=\"0.5\"}} {values[len(values)//2]}")
                lines.append(f"mcp_duration_ms{{name=\"{hist_name}\",quantile=\"mean\"}} {avg}")

        return "\n".join(lines) + "\n"

    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics stats."""
        return {
            "counters": dict(self.counters),
            "histograms": {k: {"count": len(v), "avg_ms": sum(v)/len(v) if v else 0} for k, v in self.histograms.items()},
            "uptime_seconds": time.time() - self.start_time
        }


def get_metrics_collector() -> MetricsCollector:
    """Get or create singleton metrics collector."""
    return MetricsCollector()


def record_operation_duration(metric_name: str, duration_ms: float):
    """Record operation duration to default collector."""
    get_metrics_collector().record_duration(metric_name, duration_ms)
