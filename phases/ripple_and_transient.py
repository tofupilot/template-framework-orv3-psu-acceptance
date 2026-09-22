import numpy as np

from utils.recipe import DYN_CAPTURE_MS, DYN_LOAD_PCT, DYN_SLEW_A_PER_US, RATED_A, RIPPLE_BW_MHZ, SETTLE_BAND_V


def settle_ms(t_ms, dev_v):
    """Last excursion outside the +-1 % band; settled from the next sample."""
    t = np.asarray(t_ms)
    outside = np.where(np.abs(np.asarray(dev_v)) > SETTLE_BAND_V)[0]
    return float(t[outside[-1] + 1]) if len(outside) else 0.0


def ripple_and_transient(measurements, bench, log):
    """Ripple at full load in the spec's 20 MHz bandwidth, then the dynamic
    load step of section 4.15 in both directions: 70 to 130 % of rated at
    3 A/us. The deviation limit keeps the overshoot under the OVP threshold
    and the undershoot inside the regulation window."""
    bench.set_load_a(RATED_A)
    ripple = bench.ripple_mvpp(RIPPLE_BW_MHZ)
    measurements.ripple_mvpp = ripple

    lo, hi = DYN_LOAD_PCT
    bench.set_load_a(lo / 100.0 * RATED_A)
    t_ms, up = bench.transient_capture(lo, hi, DYN_SLEW_A_PER_US)
    _, down = bench.transient_capture(hi, lo, DYN_SLEW_A_PER_US)
    bench.set_load_a(RATED_A)
    up_settle = settle_ms(t_ms, up)
    down_settle = settle_ms(t_ms, down)

    m = measurements.load_step
    m.x_axis = t_ms
    m.y_axis.step_up = up
    m.y_axis.step_up.aggregations.min_v = round(float(min(up)), 3)
    m.y_axis.step_up.aggregations.settle_ms = round(up_settle, 2)
    m.y_axis.step_down = down
    m.y_axis.step_down.aggregations.max_v = round(float(max(down)), 3)
    m.y_axis.step_down.aggregations.settle_ms = round(down_settle, 2)
    log.info(f"Ripple {ripple:.0f} mVpp; step {lo}->{hi} % undershoots {min(up):.2f} V, settles in {up_settle:.2f} ms; {hi}->{lo} % overshoots {max(down):+.2f} V, settles in {down_settle:.2f} ms over a {DYN_CAPTURE_MS:.0f} ms capture")
