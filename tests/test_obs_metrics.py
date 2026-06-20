"""Tests for obs/metrics: unit coverage and wired-into-app integration."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from chatty_commander.obs.metrics import (
    Counter,
    Gauge,
    HistogramBuckets,
    MetricsRegistry,
    Timer,
    create_metrics_router,
)

# ─── Counter ────────────────────────────────────────────────────────────────


class TestCounter:
    def test_counter_negative_amount(self):
        """Test that negative amounts are converted to 0"""
        counter = Counter("test_counter", "Test counter")
        counter.inc(-5)
        assert counter.get() == 0

    def test_counter_with_labels(self):
        """Test counter with labels"""
        counter = Counter("test_counter", "Test counter")
        counter.inc(1, {"method": "GET"})
        counter.inc(2, {"method": "POST"})

        assert counter.get({"method": "GET"}) == 1
        assert counter.get({"method": "POST"}) == 2
        assert counter.get({"method": "DELETE"}) == 0

    def test_counter_samples(self):
        """Test counter samples method"""
        counter = Counter("test_counter", "Test counter")
        counter.inc(1, {"method": "GET"})
        counter.inc(2, {"method": "POST"})

        samples = counter.samples()
        assert len(samples) == 2
        sample_dict = {
            tuple(sorted(labels.items())): value for labels, value in samples
        }
        assert sample_dict[(("method", "GET"),)] == 1
        assert sample_dict[(("method", "POST"),)] == 2


# ─── Gauge ──────────────────────────────────────────────────────────────────


class TestGauge:
    def test_gauge_set_and_get(self):
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(42.5)
        assert gauge.get() == 42.5

    def test_gauge_with_labels(self):
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(10.0, {"region": "us-east-1"})
        gauge.set(20.0, {"region": "us-west-2"})

        assert gauge.get({"region": "us-east-1"}) == 10.0
        assert gauge.get({"region": "us-west-2"}) == 20.0
        assert gauge.get({"region": "eu-west-1"}) == 0.0

    def test_gauge_samples(self):
        gauge = Gauge("test_gauge", "Test gauge")
        gauge.set(10.0, {"region": "us-east-1"})
        gauge.set(20.0, {"region": "us-west-2"})

        samples = gauge.samples()
        assert len(samples) == 2
        sample_dict = {
            tuple(sorted(labels.items())): value for labels, value in samples
        }
        assert sample_dict[(("region", "us-east-1"),)] == 10.0
        assert sample_dict[(("region", "us-west-2"),)] == 20.0


# ─── MetricsRegistry ───────────────────────────────────────────────────────


class TestMetricsRegistry:
    def test_registry_counter(self):
        registry = MetricsRegistry()
        counter = registry.counter("test_counter", "Test counter")
        counter2 = registry.counter("test_counter", "Test counter")
        assert counter is counter2

    def test_registry_gauge(self):
        registry = MetricsRegistry()
        gauge = registry.gauge("test_gauge", "Test gauge")
        gauge2 = registry.gauge("test_gauge", "Test gauge")
        assert gauge is gauge2

    def test_registry_histogram(self):
        registry = MetricsRegistry()
        histogram = registry.histogram("test_histogram", "Test histogram")
        histogram2 = registry.histogram("test_histogram", "Test histogram")
        assert histogram is histogram2

    def test_registry_to_json(self):
        registry = MetricsRegistry()
        counter = registry.counter("test_counter", "Test counter")
        gauge = registry.gauge("test_gauge", "Test gauge")
        histogram = registry.histogram("test_histogram", "Test histogram")

        counter.inc(5)
        gauge.set(42.0)
        histogram.observe(1.5)

        json_data = registry.to_json()
        assert "counters" in json_data
        assert "gauges" in json_data
        assert "histograms" in json_data

        assert "test_counter" in json_data["counters"]
        assert "test_gauge" in json_data["gauges"]
        assert "test_histogram" in json_data["histograms"]


# ─── Key generation ─────────────────────────────────────────────────────────


class TestMetricKeyGeneration:
    def test_key_generation_empty_labels(self):
        counter = Counter("test", "test")
        key1 = counter._key(None)
        key2 = counter._key({})
        assert key1 == ()
        assert key2 == ()

    def test_key_generation_sorted_labels(self):
        counter = Counter("test", "test")
        key1 = counter._key({"b": "2", "a": "1"})
        key2 = counter._key({"a": "1", "b": "2"})
        assert key1 == key2
        assert key1 == (("a", "1"), ("b", "2"))

    def test_key_generation_string_conversion(self):
        counter = Counter("test", "test")
        key = counter._key({"num": 123, "bool": True})
        assert key == (("bool", "True"), ("num", "123"))


# ─── Histogram & Timer ──────────────────────────────────────────────────────


class TestHistogramBuckets:
    def test_bucket_clamp_and_snapshot(self):
        buckets = HistogramBuckets([0.1, 0.5, 1.0])
        assert buckets.clamp(-1.0) == 0.0
        assert buckets.clamp(0.3) == 0.3

        registry = MetricsRegistry()
        histogram = registry.histogram("bucket_test", "Bucket test", buckets=buckets)
        histogram.observe(5.0)

        snapshot = histogram.snapshot()
        assert snapshot["buckets"] == [0.1, 0.5, 1.0]
        assert snapshot["series"]
        assert snapshot["series"][0]["counts"][-1] == 1


class TestHistogramAndTimer:
    def test_histogram_and_timer_records_observations(self):
        reg = MetricsRegistry()
        h = reg.histogram("work_seconds")

        h.observe(0.01, labels={"op": "manual"})

        with Timer(h, labels={"op": "ctx"}):
            time.sleep(0.001)

        snap = h.snapshot()
        assert snap["series"], "expected at least one series in histogram snapshot"
        total = sum(
            s["count"] for s in [{"count": s.get("count", 0)} for s in snap["series"]]
        )
        assert total >= 2


# ─── Wired-into-app integration ─────────────────────────────────────────────


def _make_app():
    """Create a minimal WebModeServer app for testing."""
    from chatty_commander.web.web_mode import WebModeServer

    config = MagicMock()
    config.web_server = {}
    config.advisors = {}
    config.default_state = "idle"
    config.state_models = {}
    config.api_endpoints = {}
    config.commands = {}
    config.llm_manager = None
    config.voice_pipeline = None

    state_manager = MagicMock()
    state_manager.current_state = "idle"
    state_manager.add_state_change_callback = MagicMock()

    model_manager = MagicMock()
    command_executor = MagicMock()

    server = WebModeServer(
        config_manager=config,
        state_manager=state_manager,
        model_manager=model_manager,
        command_executor=command_executor,
        no_auth=True,
    )
    return server.app


def test_metrics_json_endpoint_registered():
    """GET /metrics/json should be registered and return a dict."""
    from fastapi.testclient import TestClient

    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/metrics/json")
    assert response.status_code == 200
    data = response.json()
    assert "counters" in data
    assert "gauges" in data
    assert "histograms" in data


def test_metrics_prom_endpoint_registered():
    """GET /metrics/prom should be registered and return Prometheus text format."""
    from fastapi.testclient import TestClient

    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/metrics/prom")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")


def test_request_metrics_middleware_tracks_requests():
    """After making a request, http_requests_total counter should be non-zero."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from chatty_commander.obs.metrics import (
        RequestMetricsMiddleware,
        create_metrics_router,
    )

    registry = MetricsRegistry()

    app = FastAPI()
    app.add_middleware(RequestMetricsMiddleware, registry=registry)
    app.include_router(create_metrics_router(registry=registry))

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)
    client.get("/ping")

    response = client.get("/metrics/json")
    assert response.status_code == 200
    data = response.json()
    counters = data.get("counters", {})
    assert "http_requests_total" in counters
    samples = counters["http_requests_total"]
    total = sum(s.get("value", 0) for s in samples)
    assert total > 0, "Expected at least one request to be counted"


# ── Full-app metrics endpoint tests (from test_metrics_endpoint) ─────────


class TestMetricsEndpoints:
    """Integration tests for /api/v1/metrics, /metrics/json, /metrics/prom via create_app."""

    def _client(self):
        from chatty_commander.web.web_mode import create_app

        app = create_app(no_auth=True)
        return TestClient(app)

    def test_metrics_counts_increment(self):
        client = self._client()
        m1 = client.get("/api/v1/metrics").json()

        client.get("/api/v1/health")
        client.get("/api/v1/status")
        client.get("/api/v1/state")
        client.post("/api/v1/state", json={"state": "chatty"})
        client.post("/api/v1/command", json={"command": "hello"})

        m2 = client.get("/api/v1/metrics").json()

        assert m2["status"] >= (m1.get("status", 0) + 1)
        assert m2["response_time_avg"] >= 0.0
        assert m2["config_get"] >= m1.get("config_get", 0)
        assert m2["state_get"] >= (m1.get("state_get", 0) + 1)
        assert m2["state_post"] >= (m1.get("state_post", 0) + 1)
        assert m2["command_post"] >= (m1.get("command_post", 0) + 1)

    def test_metrics_json_endpoint(self):
        client = self._client()
        client.get("/api/v1/health")

        response = client.get("/metrics/json")
        assert response.status_code == 200
        data = response.json()
        assert "counters" in data
        assert "gauges" in data
        assert "histograms" in data
        assert "http_requests_total" in data["counters"]
        assert "http_request_duration_seconds" in data["histograms"]

    def test_metrics_prom_endpoint(self):
        client = self._client()
        client.get("/api/v1/health")

        response = client.get("/metrics/prom")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        text = response.text
        assert "http_requests_total" in text
        assert "http_request_duration_seconds" in text


# ─── Concurrency / reader-writer race regression ─────────────────────────────


class TestMetricsConcurrency:
    def test_scrape_during_concurrent_observes_no_exception(self):
        """A /metrics scrape that reads while many threads mutate the metrics
        must never raise 'dictionary changed size during iteration'.

        Readers (samples/snapshot/to_json) must snapshot the underlying dicts
        under the lock; this stresses that guarantee.
        """
        registry = MetricsRegistry()
        counter = registry.counter("race_counter", "race counter")
        gauge = registry.gauge("race_gauge", "race gauge")
        hist = registry.histogram("race_hist", "race hist")

        stop = threading.Event()
        errors: list[BaseException] = []

        def writer(n: int) -> None:
            i = 0
            try:
                while not stop.is_set():
                    # Use distinct label values to keep growing the dicts,
                    # which is what triggers "changed size during iteration".
                    labels = {"worker": str(n), "iter": str(i)}
                    counter.inc(1, labels=labels)
                    gauge.set(float(i), labels=labels)
                    hist.observe(0.001 * (i % 50), labels=labels)
                    i += 1
            except BaseException as exc:  # pragma: no cover - failure path
                errors.append(exc)

        def reader() -> None:
            try:
                while not stop.is_set():
                    # Exercise every reader path that iterates the dicts.
                    counter.samples()
                    counter.get({"worker": "0", "iter": "0"})
                    gauge.samples()
                    gauge.get({"worker": "0", "iter": "0"})
                    hist.snapshot()
                    registry.to_json()
            except BaseException as exc:  # pragma: no cover - failure path
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(n,)) for n in range(6)]
        threads += [threading.Thread(target=reader) for _ in range(4)]
        for t in threads:
            t.start()
        time.sleep(0.5)
        stop.set()
        for t in threads:
            t.join(timeout=5)

        assert not errors, f"concurrent access raised: {errors!r}"


# ─── Prometheus cumulative-histogram correctness ─────────────────────────────


def _parse_prom_buckets(text: str, name: str) -> list[tuple[str, float]]:
    """Return [(le, value), ...] for the given histogram metric name."""
    out: list[tuple[str, float]] = []
    prefix = f"{name}_bucket{{"
    for line in text.splitlines():
        if not line.startswith(prefix):
            continue
        labelpart, _, value = line.rpartition(" ")
        # Extract le="..." label
        le_idx = labelpart.find('le="')
        le = labelpart[le_idx + len('le="') : labelpart.find('"', le_idx + len('le="'))]
        out.append((le, float(value)))
    return out


class TestPrometheusHistogramCumulative:
    def test_prom_histogram_is_valid_cumulative_with_inf_equals_count(self):
        registry = MetricsRegistry()
        buckets = HistogramBuckets([0.1, 0.5, 1.0])
        hist = registry.histogram("lat", "latency", buckets=buckets)

        # Observations spread across and beyond the buckets.
        for v in [0.05, 0.05, 0.3, 0.7, 0.7, 5.0]:  # total 6
            hist.observe(v)

        router = create_metrics_router(registry=registry)
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        text = client.get("/metrics/prom").text
        bkts = _parse_prom_buckets(text, "lat")
        assert bkts, "expected histogram buckets in prom output"

        by_le = dict(bkts)
        # le="0.1": v<=0.1 -> the two 0.05 obs = 2
        assert by_le["0.1"] == 2
        # le="0.5": <=0.5 -> two 0.05 + one 0.3 = 3
        assert by_le["0.5"] == 3
        # le="1.0": <=1.0 -> + two 0.7 = 5
        assert by_le["1.0"] == 5
        # +Inf must equal the total observation count (6).
        assert by_le["+Inf"] == 6

        # Cumulative invariant: non-decreasing in bucket order, +Inf is max.
        finite_in_order = [by_le["0.1"], by_le["0.5"], by_le["1.0"]]
        assert finite_in_order == sorted(finite_in_order)
        assert by_le["+Inf"] >= finite_in_order[-1]

        # _count line must also equal +Inf bucket.
        count_line = [
            line for line in text.splitlines() if line.startswith("lat_count")
        ]
        assert count_line
        assert float(count_line[0].rpartition(" ")[2]) == 6


# ─── Duration histogram gets a real route label ──────────────────────────────


def test_duration_histogram_uses_real_route_label():
    """The http_request_duration_seconds histogram must be labeled with the
    resolved route path (e.g. '/ping'), not the placeholder 'unknown'.
    """
    from fastapi import FastAPI

    from chatty_commander.obs.metrics import RequestMetricsMiddleware

    registry = MetricsRegistry()
    app = FastAPI()
    app.add_middleware(RequestMetricsMiddleware, registry=registry)
    app.include_router(create_metrics_router(registry=registry))

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)
    client.get("/ping")

    snap = registry.histogram("http_request_duration_seconds").snapshot()
    routes = {s["labels"].get("route") for s in snap["series"]}
    assert "/ping" in routes, f"expected real route label, got {routes!r}"
    assert "unknown" not in routes, "duration histogram still labeled 'unknown'"


def test_request_counter_increments_on_handler_exception():
    """If a downstream handler raises, the request counter must still be
    incremented (try/finally guarantee) so errors are not undercounted.
    """
    from fastapi import FastAPI

    from chatty_commander.obs.metrics import RequestMetricsMiddleware

    registry = MetricsRegistry()
    app = FastAPI()
    app.add_middleware(RequestMetricsMiddleware, registry=registry)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("kaboom")

    client = TestClient(app, raise_server_exceptions=False)
    try:
        client.get("/boom")
    except Exception:
        pass

    counter = registry.counter("http_requests_total")
    total = sum(value for _labels, value in counter.samples())
    assert total > 0, "request counter must increment even when handler raises"
