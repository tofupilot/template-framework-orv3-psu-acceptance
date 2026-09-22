import numpy as np

from utils.recipe import AC_INPUTS_V, LOAD_POINTS_PCT, RATED_A, WARM_UP_MIN


def sweep(bench, vin, log):
    """Six load points at one input voltage: analyzer in and out, and the
    output current the PSU reports next to the load's own reading."""
    bench.ac_on(vin)
    eff = []
    telemetry_err = []
    for pct in LOAD_POINTS_PCT:
        amps = pct / 100.0 * RATED_A
        bench.set_load_a(amps)
        pin, pout = bench.analyzer_pin_pout_w(pct)
        eff.append(100.0 * pout / pin)
        telemetry_err.append(100.0 * (bench.modbus_iout_a() - amps) / amps)
        log.info(f"{vin:.0f} Vac, {pct:3d} %: {pin:.0f} W in, {pout:.0f} W out, {eff[-1]:.2f} %, Iout telemetry {telemetry_err[-1]:+.2f} %")
    return np.array(eff), np.array(telemetry_err)


def efficiency(measurements, bench, log):
    """Efficiency at both ends of the input range after the spec's 30 min
    warm-up at full load. The ORV3 floor is a stair (94 % below 30 % load,
    96.5 % above) and a peak (97.5 %); the Titanium points sit under it."""
    bench.set_load_a(RATED_A)
    log.info(f"Warm-up: {WARM_UP_MIN} min at {RATED_A:.0f} A (mock: instant)")
    curves = {}
    for vin in AC_INPUTS_V:
        curves[vin] = sweep(bench, vin, log)
    pts = np.array(LOAD_POINTS_PCT)
    low = pts < 30
    high = pts >= 30

    m = measurements.efficiency
    m.x_axis = LOAD_POINTS_PCT
    e277, err = curves[277.0]
    e230, _ = curves[230.0]
    m.y_axis.eff_277 = e277.round(2).tolist()
    m.y_axis.eff_277.aggregations.min_30_100_pct = round(float(e277[high].min()), 2)
    m.y_axis.eff_277.aggregations.min_10_30_pct = round(float(e277[low].min()), 2)
    m.y_axis.eff_277.aggregations.peak_pct = round(float(e277.max()), 2)
    m.y_axis.eff_230 = e230.round(2).tolist()
    m.y_axis.eff_230.aggregations.min_30_100_pct = round(float(e230[high].min()), 2)
    m.y_axis.eff_230.aggregations.min_10_30_pct = round(float(e230[low].min()), 2)
    m.y_axis.eff_230.aggregations.peak_pct = round(float(e230.max()), 2)
    m.y_axis.iout_telemetry_err_pct = err.round(2).tolist()
    m.y_axis.iout_telemetry_err_pct.aggregations.max_abs_pct = round(float(np.abs(err).max()), 2)
    log.info(f"Peak {e277.max():.2f} % at 277 Vac, {e230.max():.2f} % at 230 Vac; floor {min(e277[high].min(), e230[high].min()):.2f} % above 30 % load")
