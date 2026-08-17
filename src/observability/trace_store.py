"""
In-memory trace storage for recent tool executions.
Stores spans locally so frontend can query execution history.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any
from collections import deque
import json

@dataclass
class TraceEvent:
    """Single trace event from tool execution"""
    timestamp: str
    tool_name: str
    user: str
    org_id: str
    status: str  # success, error, insufficient_scope
    duration_ms: float
    exit_code: int = None
    error: str = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class TraceStore:
    """In-memory store for recent traces (last 100 executions)"""

    def __init__(self, max_size: int = 100):
        self.traces: deque = deque(maxlen=max_size)
        self.lock = __import__('threading').Lock()

    def add_trace(self, event: TraceEvent) -> None:
        """Add a trace event"""
        with self.lock:
            self.traces.append(event)

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent traces, newest first"""
        with self.lock:
            return [t.to_dict() for t in reversed(list(self.traces))][:limit]

    def get_by_tool(self, tool_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get traces for specific tool"""
        with self.lock:
            return [t.to_dict() for t in reversed(list(self.traces))
                   if t.tool_name == tool_name][:limit]

    def get_by_user(self, user: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get traces for specific user"""
        with self.lock:
            return [t.to_dict() for t in reversed(list(self.traces))
                   if t.user == user][:limit]

    def stats(self) -> Dict[str, Any]:
        """Get stats about traces"""
        with self.lock:
            if not self.traces:
                return {"total": 0, "success": 0, "errors": 0, "avg_duration_ms": 0}

            success = sum(1 for t in self.traces if t.status == "success")
            errors = sum(1 for t in self.traces if t.status == "error")
            avg_duration = sum(t.duration_ms for t in self.traces) / len(self.traces)

            return {
                "total": len(self.traces),
                "success": success,
                "errors": errors,
                "avg_duration_ms": round(avg_duration, 2)
            }

# Global trace store instance
trace_store = TraceStore()
