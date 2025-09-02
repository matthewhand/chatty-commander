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
    total = sum(
        s["count"] for s in [{"count": s.get("count", 0)} for s in snap["series"]]
    )
    assert total >= 2
