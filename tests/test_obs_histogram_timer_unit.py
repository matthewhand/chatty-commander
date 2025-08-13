import time

from chatty_commander.obs.metrics import MetricsRegistry, Timer


def test_histogram_and_timer_records_observations():
    reg = MetricsRegistry()
    h = reg.histogram("work_seconds")

    # Observe manually
    h.observe(0.01, labels={"op": "manual"})

    # Observe via timer context
    with Timer(h, labels={"op": "ctx"}):
        time.sleep(0.001)

    snap = h.snapshot()
    assert snap["series"], "expected at least one series in histogram snapshot"
    total = sum(s["count"] for s in [{"count": s.get("count", 0)} for s in snap["series"]])
    assert total >= 2
