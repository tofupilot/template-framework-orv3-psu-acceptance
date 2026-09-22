from utils.recipe import AC_INPUTS_V


def identify(measurements, bench, unit, log):
    """Setup: first power-on at 277 Vac with no load, then the model,
    firmware and serial read over Modbus. The serial the PSU reports must
    be the one on its label: a module programmed with another unit's
    identity is a rack that cannot be inventoried."""
    bench.ac_on(AC_INPUTS_V[-1])
    identity = bench.modbus_identity()
    serial = bench.modbus_serial()
    vout = bench.vout_v()
    measurements.psu_identity = identity
    measurements.reported_serial = serial
    measurements.serial_matches_label = serial == unit.serial_number
    measurements.vout_no_load_v = vout
    unit.metadata["fw"] = identity["fw"]
    log.info(f"{identity['model']} fw {identity['fw']} reports {serial}, label {unit.serial_number}, {vout:.2f} V at no load")
