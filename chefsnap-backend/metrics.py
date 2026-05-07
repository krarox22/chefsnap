"""
metrics.py — In-process metrics collector for ChefSnap success KPIs (plan.md §10).

Tracks per-endpoint request counts, p50/p95 latencies, and error rates via a
thread-safe in-process store. For multi-replica production deployments, forward
to Prometheus (via opentelemetry-exporter-prometheus) or Datadog instead.

Exposed via GET /api/v1/metrics in main.py.
KPIs that need client-side events (activation, D7 retention) are tracked via
useAnalytics.ts → Sentry on the React Native side.
"""

import threading
import time
import statistics
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Generator


@dataclass
class _EndpointStats:
    total: int = 0
    errors: int = 0
    _latencies: List[float] = field(default_factory=list)
    _MAX = 1000  # cap list to prevent unbounded growth

    def record(self, latency_ms: float, error: bool) -> None:
        self.total += 1
        if error:
            self.errors += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > self._MAX:
            self._latencies = self._latencies[-self._MAX:]

    def summary(self) -> dict:
        lats = sorted(self._latencies)
        n = len(lats)
        return {
            "total_requests": self.total,
            "error_count": self.errors,
            "error_rate": round(self.errors / self.total, 4) if self.total else 0.0,
            "p50_ms": round(statistics.median(lats), 1) if lats else None,
            "p95_ms": round(lats[int(n * 0.95)], 1) if lats else None,
            "p99_ms": round(lats[int(n * 0.99)], 1) if lats else None,
        }


class MetricsCollector:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stats: Dict[str, _EndpointStats] = {}
        self._started_at = time.time()

    def _bucket(self, key: str) -> _EndpointStats:
        if key not in self._stats:
            self._stats[key] = _EndpointStats()
        return self._stats[key]

    def record(self, endpoint: str, latency_ms: float, error: bool = False) -> None:
        with self._lock:
            self._bucket(endpoint).record(latency_ms, error)

    @contextmanager
    def measure(self, endpoint: str) -> Generator[None, None, None]:
        """Wraps a block and automatically records latency + errors."""
        start = time.perf_counter()
        error = False
        try:
            yield
        except Exception:
            error = True
            raise
        finally:
            self.record(endpoint, (time.perf_counter() - start) * 1000, error)

    def summary(self) -> dict:
        with self._lock:
            return {
                "uptime_hours": round((time.time() - self._started_at) / 3600, 3),
                "endpoints": {
                    ep: s.summary() for ep, s in self._stats.items()
                },
                # Server-side KPIs from plan.md §10 we can derive here:
                #   • p95 end-to-end latency ≤ 8 000 ms  → check suggest p95_ms
                #   • error rate per endpoint             → check error_rate
                # Client-side KPIs (activation, relevance, D7 retention) are
                # tracked via useAnalytics.ts → Sentry on the React Native side.
                "kpi_targets": {
                    "detect_p95_ms_target": 3000,
                    "suggest_p95_ms_target": 8000,
                    "error_rate_target": 0.01,
                },
            }


# Module-level singleton imported by main.py
metrics = MetricsCollector()
