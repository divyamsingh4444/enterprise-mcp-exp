"""
Redis-backed trace storage for recent tool executions.
Shared across all ASGI workers for consistent trace visibility.
"""

import os
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any
import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
TRACES_KEY = "mcp:traces"  # Redis list key for traces
MAX_TRACES = 100

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
    """Redis-backed store for recent traces (last 100 executions)"""

    def __init__(self):
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            logger.info("✅ Connected to Redis for trace storage")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis_client = None

    def _get_redis(self):
        """Get Redis client with reconnection"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                self.redis_client.ping()
            except:
                return None
        return self.redis_client

    def add_trace(self, event: TraceEvent) -> None:
        """Add a trace event to Redis"""
        try:
            r = self._get_redis()
            if r is None:
                logger.warning("Redis unavailable, trace not persisted")
                return

            trace_json = json.dumps(event.to_dict())
            r.lpush(TRACES_KEY, trace_json)
            r.ltrim(TRACES_KEY, 0, MAX_TRACES - 1)  # Keep only last 100
        except Exception as e:
            logger.error(f"Failed to store trace: {e}")

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent traces, newest first"""
        try:
            r = self._get_redis()
            if r is None:
                return []

            traces_json = r.lrange(TRACES_KEY, 0, limit - 1)
            return [json.loads(t) for t in traces_json]
        except Exception as e:
            logger.error(f"Failed to get traces: {e}")
            return []

    def get_by_tool(self, tool_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get traces for specific tool"""
        try:
            r = self._get_redis()
            if r is None:
                return []

            traces_json = r.lrange(TRACES_KEY, 0, -1)
            traces = [json.loads(t) for t in traces_json]
            return [t for t in traces if t["tool_name"] == tool_name][:limit]
        except Exception as e:
            logger.error(f"Failed to get tool traces: {e}")
            return []

    def get_by_user(self, user: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get traces for specific user"""
        try:
            r = self._get_redis()
            if r is None:
                return []

            traces_json = r.lrange(TRACES_KEY, 0, -1)
            traces = [json.loads(t) for t in traces_json]
            return [t for t in traces if t["user"] == user][:limit]
        except Exception as e:
            logger.error(f"Failed to get user traces: {e}")
            return []

    def stats(self) -> Dict[str, Any]:
        """Get stats about traces"""
        try:
            r = self._get_redis()
            if r is None:
                return {"total": 0, "success": 0, "errors": 0, "avg_duration_ms": 0}

            traces_json = r.lrange(TRACES_KEY, 0, -1)
            if not traces_json:
                return {"total": 0, "success": 0, "errors": 0, "avg_duration_ms": 0}

            traces = [json.loads(t) for t in traces_json]
            success = sum(1 for t in traces if t["status"] == "success")
            errors = sum(1 for t in traces if t["status"] == "error")
            avg_duration = sum(t["duration_ms"] for t in traces) / len(traces) if traces else 0

            return {
                "total": len(traces),
                "success": success,
                "errors": errors,
                "avg_duration_ms": round(avg_duration, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total": 0, "success": 0, "errors": 0, "avg_duration_ms": 0}

# Global trace store instance (connects to Redis)
trace_store = TraceStore()
