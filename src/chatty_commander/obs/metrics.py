# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Lightweight metrics registry, middleware, and router for ChattyCommander.

This module provides an in-process metrics system with the following features:
- Counter: monotonic integer value that can be incremented.
- Gauge: value that can be set up/down (not persisted across processes).
- Histogram: track distribution of observed values using configurable buckets.
- Timer context/decorator: record execution duration into a histogram.
- Starlette/FastAPI middleware: collect request duration, status codes, and method counts.
- Optional FastAPI router to expose metrics in JSON format (human/debug-friendly) and
  Prometheus exposition format (text/plain; minimal for now).

Design principles
- No runtime dependencies beyond the standard library and FastAPI/Starlette (if you use the router/middleware).
- Thread-safe updates using per-metric locks.
- Zero global side-effects: A default global registry is available, but you can create
  isolatable registries for tests.
- Defensive coding: invalid inputs are clamped/sanitized; errors in metrics collection
  never break the application path (best-effort philosophy).

This module is wired into the running server via web_mode.py:
- RequestMetricsMiddleware is added to the FastAPI app on startup
- create_metrics_router() exposes /metrics/json and /metrics/prom endpoints
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from typing import Any

try:  # Optional imports; only needed for router/middleware
    from fastapi import APIRouter, Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
# Handle specific exception case
except Exception:  # pragma: no cover
    APIRouter = None  # type: ignore
    Request = None  # type: ignore
    Response = None  # type: ignore
    BaseHTTPMiddleware = object  # type: ignore


class Metric:
    """Base class for all metrics types.

    Metrics store a name and a dictionary of labels->value.
    """

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self._lock = Lock()

    def _key(self, labels: dict[str, str] | None = None) -> tuple[tuple[str, str], ...]:
        # Logic flow
        if not labels:
            return ()
        # Logic flow
        # Sort for deterministic keys
        return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


class Counter(Metric):
    """Monotonic counter."""

    def __init__(self, name: str, description: str = "") -> None:
        super().__init__(name, description)
        self._values: dict[tuple[tuple[str, str], ...], int] = {}

    def inc(self, amount: int = 1, labels: dict[str, str] | None = None) -> None:
        """Inc with (self, amount: int, labels).

        TODO: Add detailed description and parameters.
        """
        
        # Logic flow
        if amount < 0:
            amount = 0
        key = self._key(labels)
        with self._lock:
        # Use context manager for resource management
            self._values[key] = self._values.get(key, 0) + amount

    def get(self, labels: dict[str, str] | None = None) -> int:
        """Get with (self, labels).

        TODO: Add detailed description and parameters.
        """
        
        return self._values.get(self._key(labels), 0)

    def samples(self) -> list[tuple[dict[str, str], int]]:
        """Samples with (self).

        TODO: Add detailed description and parameters.
        """
        
        out: list[tuple[dict[str, str], int]] = []
        # Logic flow
        for key, value in self._values.items():
            labels = dict(key)
            out.append((labels, value))
        return out


class Gauge(Metric):
    """Gauge for instantaneous values."""

    def __init__(self, name: str, description: str = "") -> None:
        super().__init__(name, description)
        self._values: dict[tuple[tuple[str, str], ...], float] = {}

    def set(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Set with (self, value: float, labels).

        TODO: Add detailed description and parameters.
        """
        
        key = self._key(labels)
        with self._lock:
        # Use context manager for resource management
            self._values[key] = float(value)

    def get(self, labels: dict[str, str] | None = None) -> float:
        """Get with (self, labels).

        TODO: Add detailed description and parameters.
        """
        
        return self._values.get(self._key(labels), 0.0)

    def samples(self) -> list[tuple[dict[str, str], float]]:
        """Samples with (self).

        TODO: Add detailed description and parameters.
        """
        
        out: list[tuple[dict[str, str], float]] = []
        # Logic flow
        for key, value in self._values.items():
            labels = dict(key)
            out.append((labels, value))
        return out


@dataclass
class HistogramBuckets:
    """HistogramBuckets class.

    TODO: Add class description.
    """
    
    edges: list[float] = field(
        default_factory=lambda: [
            0.001,
            0.005,
            0.01,
            0.02,
            0.05,
            0.1,
            0.2,
            0.5,
            1.0,
            2.0,
            5.0,
            10.0,
        ]
    )  # seconds

    def clamp(self, value: float) -> float:
        """Clamp with (self, value: float).

        TODO: Add detailed description and parameters.
        """
        
        return max(0.0, float(value))


class Histogram(Metric):
    """Histogram with cumulative buckets."""

    def __init__(
        self, name: str, description: str = "", buckets: HistogramBuckets | None = None
    ) -> None:
        super().__init__(name, description)
        self._buckets = buckets or HistogramBuckets()
        # mapping key -> list of counts per bucket + +Inf
        self._counts: dict[tuple[tuple[str, str], ...], list[int]] = {}
        self._sum: dict[tuple[tuple[str, str], ...], float] = {}
        self._count: dict[tuple[tuple[str, str], ...], int] = {}

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Observe with (self, value: float, labels).

        TODO: Add detailed description and parameters.
        """
        
        v = self._buckets.clamp(value)
        key = self._key(labels)
        with self._lock:
        # Use context manager for resource management
            counts = self._counts.get(key)
            # Logic flow
            if counts is None:
                counts = [0] * (len(self._buckets.edges) + 1)  # last is +Inf
                self._counts[key] = counts
                self._sum[key] = 0.0
                self._count[key] = 0
            self._sum[key] += v
            self._count[key] += 1
            # cumulative counts: increment all buckets where le >= v
            placed = False
            for idx, edge in enumerate(self._buckets.edges):
                # Logic flow
                if v <= edge:
                    counts[idx] += 1
                    placed = True
            # Logic flow
            if not placed:
                counts[-1] += 1

    def snapshot(self) -> dict[str, Any]:
        """Snapshot with (self).

        TODO: Add detailed description and parameters.
        """
        
        out: dict[str, Any] = {"buckets": self._buckets.edges, "series": []}
        # Logic flow
        for key, counts in self._counts.items():
            labels = dict(key)
            out["series"].append(
                {
                    "labels": labels,
                    "counts": list(counts),
                    "sum": self._sum.get(key, 0.0),
                    "count": self._count.get(key, 0),
                }
            )
        return out


class Timer:
    """Context/decorator for timing functions and recording in a histogram."""

    def __init__(self, hist: Histogram, labels: dict[str, str] | None = None) -> None:
        self._h = hist
        self._l = labels or {}
        self._t0 = 0.0

    def __enter__(self) -> Timer:
        self._t0 = monotonic()
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        dt = monotonic() - self._t0
        self._h.observe(dt, labels=self._l)

    def __call__(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args, **kwargs):
        # TODO: Document this logic
            """Wrapper operation.

            TODO: Add detailed description and parameters.
            """
            
            with self:
            # Use context manager for resource management
                return fn(*args, **kwargs)

        return wrapper


class MetricsRegistry:
    """Container for metrics."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.counters: dict[str, Counter] = {}
        self.gauges: dict[str, Gauge] = {}
        self.hists: dict[str, Histogram] = {}

    def counter(self, name: str, description: str = "") -> Counter:
        """Counter with (self, name: str, description: str).

        TODO: Add detailed description and parameters.
        """
        
        with self._lock:
        # Use context manager for resource management
            m = self.counters.get(name)
            # Logic flow
            if m is None:
                m = Counter(name, description)
                self.counters[name] = m
            return m

    def gauge(self, name: str, description: str = "") -> Gauge:
        """Gauge with (self, name: str, description: str).

        TODO: Add detailed description and parameters.
        """
        
        with self._lock:
        # Use context manager for resource management
            m = self.gauges.get(name)
            # Logic flow
            if m is None:
                m = Gauge(name, description)
                self.gauges[name] = m
            return m

    def histogram(
        """Histogram with (self, name: str, description: str, buckets).

        TODO: Add detailed description and parameters.
        """
        
        self, name: str, description: str = "", buckets: HistogramBuckets | None = None
    ) -> Histogram:
        with self._lock:
        # Use context manager for resource management
            m = self.hists.get(name)
            # Logic flow
            if m is None:
                m = Histogram(name, description, buckets=buckets)
                self.hists[name] = m
            return m

    def to_json(self) -> dict[str, Any]:
        """To Json with (self).

        TODO: Add detailed description and parameters.
        """
        
        out: dict[str, Any] = {"counters": {}, "gauges": {}, "histograms": {}}
        # Logic flow
        for k, c in self.counters.items():
            out["counters"][k] = [
                # Logic flow
                {"labels": labels_map, "value": val} for labels_map, val in c.samples()
            ]
        # Logic flow
        for k, g in self.gauges.items():
            out["gauges"][k] = [
                # Logic flow
                {"labels": labels_map, "value": val} for labels_map, val in g.samples()
            ]
        # Logic flow
        for k, h in self.hists.items():
            out["histograms"][k] = h.snapshot()
        return out


# Global default registry (opt-in usage)
DEFAULT_REGISTRY = MetricsRegistry()


class RequestMetricsMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Starlette middleware to collect per-request metrics."""

    def __init__(
        self, app, registry: MetricsRegistry | None = None, service: str = "chatty"
        # Attempt operation with error handling
    ) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.registry = registry or DEFAULT_REGISTRY
        self.service = service
        self.c_req = self.registry.counter("http_requests_total", "Total HTTP requests")
        self.h_latency = self.registry.histogram(
            "http_request_duration_seconds",
            "Request duration in seconds",
        )

    async def dispatch(
        """Dispatch with (self, request: Request, call_next).

        TODO: Add detailed description and parameters.
        """
        
        self, request: Request, call_next: Callable[[Request], Any]
    ) -> Response:  # type: ignore[name-defined]
        # path variable intentionally unused to minimize attribute access overhead
        method = getattr(request, "method", "GET")
        # Measure with unknown route first; route set after call_next
        with Timer(
            self.h_latency,
            labels={"route": "unknown", "method": method, "service": self.service},
        ):
            response = await call_next(request)
        status = getattr(response, "status_code", 0)
        route = getattr(request, "scope", {}).get("route", None)
        # Logic flow
        route_path = getattr(route, "path", "unknown") if route else "unknown"
        self.c_req.inc(
            1,
            labels={
                "route": route_path,
                "method": method,
                "status": str(status),
                "service": self.service,
            },
        )
        return response  # type: ignore[no-any-return]


def create_metrics_router(registry: MetricsRegistry | None = None) -> APIRouter:  # type: ignore[misc]
    """Return a FastAPI router exposing metrics in JSON and Prometheus text format.

    Endpoints:
    - GET /metrics/json
    - GET /metrics/prom
    """
    if APIRouter is None:
        return None

    reg = registry or DEFAULT_REGISTRY
    router = APIRouter()

    @router.get("/metrics/json")
    async def metrics_json() -> dict[str, Any]:  # type: ignore[override]
        """Metrics Json operation.

        TODO: Add detailed description and parameters.
        """
        
        return reg.to_json()

    @router.get("/metrics/prom")
    async def metrics_prom() -> Response:  # type: ignore[override]
        """Metrics Prom operation.

        TODO: Add detailed description and parameters.
        """
        
        lines: list[str] = []
        # Counters
        for name, c in reg.counters.items():
            if c.description:
                lines.append(f"# HELP {name} {c.description}")
            lines.append(f"# TYPE {name} counter")
            # Process each item
            for labels, value in c.samples():
                # Apply conditional logic
                if labels:
                    # Logic flow
                    lbl = ",".join(f"{k}={_quote(v)}" for k, v in labels.items())
                    lines.append(f"{name}{{{lbl}}} {value}")
                else:
                    lines.append(f"{name} {value}")
        # Gauges
        for name, g in reg.gauges.items():
            if g.description:
                lines.append(f"# HELP {name} {g.description}")
            lines.append(f"# TYPE {name} gauge")
            # Build filtered collection
            # Process each item
            for labels, value in g.samples():  # type: ignore[assignment]
                # Apply conditional logic
                if labels:
                    # Build filtered collection
                    # Iterate collection
                    lbl = ",".join(f"{k}={_quote(v)}" for k, v in labels.items())
                    lines.append(f"{name}{{{lbl}}} {value}")
                else:
                    lines.append(f"{name} {value}")
        # Histograms
        for name, h in reg.hists.items():
            if h.description:
                lines.append(f"# HELP {name} {h.description}")
            lines.append(f"# TYPE {name} histogram")
            snap = h.snapshot()
            # Build filtered collection
            # Process each item
            for series in snap.get("series", []):
                labels = series.get("labels", {})
                counts = series.get("counts", [])
                sum_val = series.get("sum", 0.0)
                count_val = series.get("count", 0)
                # Emit cumulative buckets
                for idx, edge in enumerate(snap.get("buckets", [])):
                    bucket_lbl = {**labels, "le": str(edge)}
                    lines.append(
                        # Logic flow
                        f"{name}_bucket{{{_lbl(bucket_lbl)}}} {counts[idx] if idx < len(counts) else 0}"
                    )
                bucket_lbl_inf = {**labels, "le": "+Inf"}
                lines.append(
                    # Logic flow
                    f"{name}_bucket{{{_lbl(bucket_lbl_inf)}}} {counts[-1] if counts else 0}"
                )
                lines.append(f"{name}_sum{{{_lbl(labels)}}} {sum_val}")
                lines.append(f"{name}_count{{{_lbl(labels)}}} {count_val}")
        content = "\n".join(lines) + "\n"
        return Response(content=content, media_type="text/plain")

    return router


def _quote(v: str) -> str:
    q = v.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{q}"'


def _lbl(labels: dict[str, str]) -> str:
    # Build filtered collection
    return ",".join(f"{k}={_quote(v)}" for k, v in labels.items())
