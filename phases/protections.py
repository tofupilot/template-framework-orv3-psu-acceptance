from utils.recipe import OCP_RAMP_STEP_A, OTP_SWEEP_C, OVP_TRIM_STEP_V, RATED_A, REGULATION_LOW_V, VOUT_SET_V


def protections(measurements, bench, log):
    """OVP by raising the set-point over the management bus in test mode,
    OCP by ramping the load into constant current and timing the restart,
    OTW and OTP by overriding the thermistor reading. Each trip is cleared
    and the output checked back in regulation before the next."""
    bench.set_load_a(0.5 * RATED_A)

    v = VOUT_SET_V
    while not bench.modbus_faults()["ovp"]:
        v = round(v + OVP_TRIM_STEP_V, 2)
        bench.modbus_trim_vout(v)
    ovp_ms = bench.ovp_response_ms()
    bench.modbus_clear_faults()
    log.info(f"OVP at {v:.2f} V, output off in {ovp_ms:.0f} ms")

    amps = RATED_A
    while not bench.modbus_faults()["ocp"]:
        amps += OCP_RAMP_STEP_A
        bench.set_load_a(amps)
    cc_pct = 100.0 * amps / RATED_A
    ocp_s = bench.ocp_shutdown_s()
    bench.set_load_a(0.5 * RATED_A)
    bench.modbus_clear_faults()
    log.info(f"Constant current from {amps:.0f} A ({cc_pct:.0f} %), restart after {ocp_s:.1f} s out of regulation")

    otw_c = None
    otp_c = None
    temp = OTP_SWEEP_C[0]
    while temp <= OTP_SWEEP_C[1]:
        bench.modbus_override_temp_c(temp)
        faults = bench.modbus_faults()
        if faults["otw"] and otw_c is None:
            otw_c = temp
        if faults["otp"]:
            otp_c = temp
            break
        temp = round(temp + OTP_SWEEP_C[2], 1)
    bench.modbus_clear_faults()
    recovered = bench.vout_v() > REGULATION_LOW_V
    log.info(f"OTW at {otw_c:.1f} C, OTP at {otp_c:.1f} C, output back at {bench.vout_v():.2f} V")

    measurements.ovp_trip_v = v
    measurements.ovp_response_ms = ovp_ms
    measurements.cc_limit_a = round(amps, 1)
    measurements.ocp_restart_s = ocp_s
    measurements.otw_trip_c = otw_c
    measurements.otp_trip_c = otp_c
    measurements.otp_minus_otw_c = round(otp_c - otw_c, 1)
    measurements.recovered_after_trips = recovered
