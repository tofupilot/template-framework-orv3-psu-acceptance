"""Acceptance recipe for an OCP Open Rack V3 HPR 12 kW PSU module: the
stimulus applied at every step and the limit each result is judged on.

Limits come from the OCP "Open Rack V3 HPR V2 12 kW PSU Module" spec where
it gives a number (efficiency, hold-up, inrush, ripple, OVP, dynamic load,
production hipot) and from IEC 62368-1 routine tests for the safety
figures. The OTW-to-OTP margin is the M-CRPS rule. Everything else (the
regulation window, the OCP restart delay tolerance) is this line's
derivation and is marked as such in procedure.yaml."""

# Unit under test
VOUT_SET_V = 50.5
RATED_W = 12000.0
RATED_A = RATED_W / VOUT_SET_V  # 237.6 A
AC_INPUTS_V = [230.0, 277.0]  # spec range 230-277 Vac, tested at both ends
IDENTITY = {"model": "PSU-ORV3-12K-277", "fw": "2.4.1", "protocol": "modbus-rtu"}

# Safety, before AC is ever applied (IEC 62368-1 routine tests)
HIPOT_VDC = 2121.0  # 1500 Vac equivalent, primary to chassis, basic insulation
HIPOT_DWELL_S = 1.0
GROUND_BOND_A = 40.0
GROUND_BOND_DWELL_S = 2.0

# Inrush at cold start, 277 Vac, closed at the 90 degree phase angle (spec 4.7)
INRUSH_CAPTURE_MS = 40.0
INRUSH_SAMPLE_KHZ = 20.0
MAINS_HZ = 50.0

# Efficiency sweep (spec 4.8), warm for 30 min at full load before the sweep
LOAD_POINTS_PCT = [10, 20, 30, 50, 75, 100]
WARM_UP_MIN = 30
TITANIUM_230V = {10: 90.0, 20: 94.0, 50: 96.0, 100: 91.0}  # 80 PLUS, internal redundant

# Ripple and dynamic load (spec 4.14, 4.15)
RIPPLE_BW_MHZ = 20.0
DYN_LOAD_PCT = (70, 130)
DYN_SLEW_A_PER_US = 3.0
DYN_CAPTURE_MS = 4.0
SETTLE_BAND_V = 0.01 * VOUT_SET_V  # settled when inside +-1 %

# Hold-up (spec 4.17, Table 8): the output must stay in regulation
HOLDUP_LOADS_PCT = [100, 120]
HOLDUP_CAPTURE_MS = 40.0
REGULATION_LOW_V = 48.5  # below this the output has left regulation

# Protections
OVP_TRIM_STEP_V = 0.1  # output set-point raised over the management bus in test mode
OCP_RAMP_STEP_A = 2.0
OTP_SWEEP_C = (80.0, 100.0, 0.2)  # thermistor reading overridden in test mode
