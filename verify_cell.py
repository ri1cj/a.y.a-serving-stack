#!/usr/bin/env python3
# Green check for the extra W3D1 lab (the memory leak hunter).
# Paste into a Colab cell next to leak_report.json, or run: python verify_cell.py
# Prints exactly one line last: GREEN CHECK: PASS  or  GREEN CHECK: FAIL (<reason>)
# stdlib only: the slope refit below is plain least squares, no numpy, so the
# verifier shares no code with the detector it is checking.
import json, os
from typing import NoReturn

LEAK_FLOOR_MB_PER_ITER = 5.0    # the deliberate leak retains logits + graph; a
                                # real reproduction climbs far faster than this
FIXED_CEIL_MB_PER_ITER = 1.0    # allocator drift, not a leak
MIN_SAMPLES = 15
DRIFT_CEIL_MB_PER_CYCLE = 100.0  # reload-loop baseline may drift, not climb


class _Stop(Exception):
    """Ends the check without killing the notebook kernel."""


def _fail(reason) -> NoReturn:
    print("GREEN CHECK: FAIL (%s)" % reason)
    raise _Stop()


def slope(ys):
    """Least-squares slope of ys against 0..n-1, no numpy."""
    n = len(ys)
    xs = range(n)
    mx = (n - 1) / 2.0
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else 0.0


def main():
    if not os.path.isfile("leak_report.json"):
        _fail("leak_report.json not found; run Step 5 first")
    try:
        with open("leak_report.json") as f:
            r = json.load(f)
    except json.JSONDecodeError as e:
        _fail("leak_report.json is not valid JSON: %s" % e)

    for key in ("reload_loop_baseline", "leaky_run", "fixed_run",
                "leaky_samples", "fixed_samples"):
        if key not in r:
            _fail("missing key '%s' (Step 5 in the current lab writes raw "
                  "samples too; re-run it)" % key)

    base = r["reload_loop_baseline"]
    if not isinstance(base, list) or len(base) < 5:
        _fail("reload_loop_baseline needs the 5 control cycles")
    unloads = []
    for row in base:
        try:
            if row["after_unload_mb"] >= row["after_load_mb"]:
                _fail("cycle %s: after_unload >= after_load; unload freed "
                      "nothing" % row.get("cycle"))
            unloads.append(float(row["after_unload_mb"]))
        except (KeyError, TypeError):
            _fail("baseline rows need after_load_mb and after_unload_mb")
    base_slope = slope(unloads)
    if base_slope > DRIFT_CEIL_MB_PER_CYCLE:
        _fail("control loop itself climbs %.1f MB/cycle; the notebook leaked "
              "before Step 2 (restart the runtime and rerun)" % base_slope)

    for name, samples_key, run_key in (("leaky", "leaky_samples", "leaky_run"),
                                       ("fixed", "fixed_samples", "fixed_run")):
        ys = r[samples_key]
        if not isinstance(ys, list) or len(ys) < MIN_SAMPLES:
            _fail("%s run has %s samples, need >= %d"
                  % (name, len(ys) if isinstance(ys, list) else "no", MIN_SAMPLES))
        if not all(isinstance(y, (int, float)) for y in ys):
            _fail("%s_samples must be numbers (MB readings)" % name)
        my_slope = slope(ys)
        claimed = r[run_key]
        their_slope = claimed.get("slope_mb_per_iter")
        if not isinstance(their_slope, (int, float)) or abs(their_slope - my_slope) > max(0.5, abs(my_slope) * 0.15):
            _fail("%s run: detector says %.3f MB/iter, an independent refit of "
                  "the same samples says %.3f; the detector is not reading its "
                  "own data" % (name, their_slope or float("nan"), my_slope))
        if name == "leaky":
            if my_slope < LEAK_FLOOR_MB_PER_ITER:
                _fail("leaky run climbs only %.2f MB/iter; the deliberate leak "
                      "was not actually reproduced (both causes in Step 2?)" % my_slope)
            if not claimed.get("leaking"):
                _fail("leaky run climbs %.1f MB/iter but the detector says "
                      "leaking=false" % my_slope)
        else:
            if my_slope > FIXED_CEIL_MB_PER_ITER:
                _fail("fixed run still climbs %.2f MB/iter; one of the two "
                      "causes survived the fix" % my_slope)
            if claimed.get("leaking"):
                _fail("fixed run is flat (%.2f MB/iter) but the detector says "
                      "leaking=true; its threshold is misread" % my_slope)

    print("refit slopes agree with the detector; leak reproduced then removed")
    print("GREEN CHECK: PASS")


if __name__ == "__main__":
    try:
        main()
    except _Stop:
        raise SystemExit(1)
