import numpy as np

from utils.recipe import AC_INPUTS_V, HOLDUP_LOADS_PCT, RATED_A, REGULATION_LOW_V


def hold_up(measurements, bench, log):
    """AC removed at full load and at 120 % (Table 8): the output must stay
    in regulation for 20 ms and 16.67 ms, and AC_Loss_L must lead the
    collapse by at least 5 ms so the rack can shed load. Hold-up is a
    capacitor-energy budget; a bulk capacitor from the wrong reel shows up
    here and nowhere else."""
    margins = []
    traces = {}
    for pct in HOLDUP_LOADS_PCT:
        bench.set_load_a(pct / 100.0 * RATED_A)
        t_ms, v, ac_loss_ms = bench.ac_loss_capture(pct)
        bench.ac_on(AC_INPUTS_V[-1])
        t = np.asarray(t_ms)
        below = np.where(np.asarray(v) < REGULATION_LOW_V)[0]
        held = float(t[below[0]]) if len(below) else float(t[-1])
        margins.append(held - ac_loss_ms)
        traces[pct] = (t_ms, v, held)
        log.info(f"AC loss at {pct} %: output above {REGULATION_LOW_V} V for {held:.1f} ms, AC_Loss_L after {ac_loss_ms:.1f} ms")
    m = measurements.hold_up
    m.x_axis = traces[100][0]
    m.y_axis.vout_100 = traces[100][1]
    m.y_axis.vout_100.aggregations.hold_up_ms = round(traces[100][2], 1)
    m.y_axis.vout_120 = traces[120][1]
    m.y_axis.vout_120.aggregations.hold_up_ms = round(traces[120][2], 1)
    measurements.ac_loss_warning_margin_ms = round(min(margins), 1)
    bench.set_load_a(RATED_A)
