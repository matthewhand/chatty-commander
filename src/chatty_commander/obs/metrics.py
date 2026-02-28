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

Consumers can import and install the middleware/routers on demand.
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
        if not labels:
            return ()
        # Sort for deterministic keys
        return tuple(sorted((str(k), str(v)) for k, v in labels.items()))


class Counter(Metric):
    """Monotonic counter."""

    def __init__(self, name: str, description: str = "") -> None:
        super().__init__(name, description)
        self._values: dict[tuple[tuple[str, str], ...], int] = {}

    def inc(self, amount: int = 1, labels: dict[str, str] | None = None) -> None:
        if amount < 0:
            amount = 0
        key = self._key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0) + amount

    def get(self, labels: dict[str, str] | None = None) -> int:
        return self._values.get(self._key(labels), 0)

    def samples(self) -> list[tuple[dict[str, str], int]]:
        out: list[tuple[dict[str, str], int]] = []
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
        key = self._key(labels)
        with self._lock:
            self._values[key] = float(value)

    def get(self, labels: dict[str, str] | None = None) -> float:
        return self._values.get(self._key(labels), 0.0)

    def samples(self) -> list[tuple[dict[str, str], float]]:
        out: list[tuple[dict[str, str], float]] = []
        for key, value in self._values.items():
            labels = dict(key)
            out.append((labels, value))
        return out


@dataclass
class HistogramBuckets:
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
        v = self._buckets.clamp(value)
        key = self._key(labels)
        with self._lock:
            counts = self._counts.get(key)
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
                if v <= edge:
                    counts[idx] += 1
                    placed = True
            if not placed:
                counts[-1] += 1

    def snapshot(self) -> dict[str, Any]:
        out: dict[str, Any] = {"buckets": self._buckets.edges, "series": []}
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
            with self:
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
        with self._lock:
            m = self.counters.get(name)
            if m is None:
                m = Counter(name, description)
                self.counters[name] = m
            return m

    def gauge(self, name: str, description: str = "") -> Gauge:
        with self._lock:
            m = self.gauges.get(name)
            if m is None:
                m = Gauge(name, description)
                self.gauges[name] = m
            return m

    def histogram(
        self, name: str, description: str = "", buckets: HistogramBuckets | None = None
    ) -> Histogram:
        with self._lock:
            m = self.hists.get(name)
            if m is None:
                m = Histogram(name, description, buckets=buckets)
                self.hists[name] = m
            return m

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"counters": {}, "gauges": {}, "histograms": {}}
        for k, c in self.counters.items():
            out["counters"][k] = [
                {"labels": labels_map, "value": val} for labels_map, val in c.samples()
            ]
        for k, g in self.gauges.items():
            out["gauges"][k] = [
                {"labels": labels_map, "value": val} for labels_map, val in g.samples()
            ]
        for k, h in self.hists.items():
            out["histograms"][k] = h.snapshot()
        return out


# Global default registry (opt-in usage)
DEFAULT_REGISTRY = MetricsRegistry()


class RequestMetricsMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Starlette middleware to collect per-request metrics."""

    def __init__(
        self, app, registry: MetricsRegistry | None = None, service: str = "chatty"
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
        return response


def create_metrics_router(registry: MetricsRegistry | None = None) -> APIRouter:  # type: ignore[misc]
    """Return a FastAPI router exposing metrics in JSON and Prometheus text format.

    Endpoints:
    - GET /metrics/json
    - GET /metrics/prom
    """
    reg = registry or DEFAULT_REGISTRY
    router = APIRouter()

    @router.get("/metrics/json")
    async def metrics_json() -> dict[str, Any]:  # type: ignore[override]
        return reg.to_json()

    @router.get("/metrics/prom")
    async def metrics_prom() -> Response:  # type: ignore[override]
        lines: list[str] = []
        # Counters
        for name, c in reg.counters.items():
            if c.description:
                lines.append(f"# HELP {name} {c.description}")
            lines.append(f"# TYPE {name} counter")
            for labels, value in c.samples():
                if labels:
                    lbl = ",".join(f"{k}={_quote(v)}" for k, v in labels.items())
                    lines.append(f"{name}{{{lbl}}} {value}")
                else:
                    lines.append(f"{name} {value}")
        # Gauges
        for name, g in reg.gauges.items():
            if g.description:
                lines.append(f"# HELP {name} {g.description}")
            lines.append(f"# TYPE {name} gauge")
            for labels, value in g.samples():
                if labels:
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
            for series in snap.get("series", []):
                labels = series.get("labels", {})
                counts = series.get("counts", [])
                sum_val = series.get("sum", 0.0)
                count_val = series.get("count", 0)
                # Emit cumulative buckets
                for idx, edge in enumerate(snap.get("buckets", [])):
                    lbl = {**labels, "le": str(edge)}
                    lines.append(
                        f"{name}_bucket{{{_lbl(lbl)}}} {counts[idx] if idx < len(counts) else 0}"
                    )
                lbl = {**labels, "le": "+Inf"}
                lines.append(
                    f"{name}_bucket{{{_lbl(lbl)}}} {counts[-1] if counts else 0}"
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
    return ",".join(f"{k}={_quote(v)}" for k, v in labels.items())
