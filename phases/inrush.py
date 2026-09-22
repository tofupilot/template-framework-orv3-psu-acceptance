import numpy as np

from utils.recipe import AC_INPUTS_V, MAINS_HZ


def inrush(measurements, bench, log):
    """Cold start at 277 Vac closed at the 90 degree phase angle, the worst
    case for the bulk capacitors, on the inrush CT. Peak and the RMS of the
    first mains cycle, both limits from section 4.7 of the spec."""
    bench.ac_off()
    bench.set_load_a(0.0)
    t_ms, i_a = bench.inrush_capture(90.0)
    bench.ac_on(AC_INPUTS_V[-1])
    t = np.asarray(t_ms)
    i = np.asarray(i_a)
    first_cycle = i[t < 1000.0 / MAINS_HZ]
    peak = float(np.abs(i).max())
    rms = float(np.sqrt(np.mean(first_cycle**2)))

    measurements.inrush.x_axis = t_ms
    measurements.inrush.y_axis.current = i_a
    measurements.inrush.y_axis.current.aggregations.peak_a = round(peak, 2)
    measurements.inrush.y_axis.current.aggregations.first_cycle_rms_a = round(rms, 2)
    log.info(f"Inrush at 90 deg: peak {peak:.1f} A, first-cycle RMS {rms:.1f} A over {len(i_a)} samples")
