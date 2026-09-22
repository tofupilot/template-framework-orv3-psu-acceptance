from utils.recipe import GROUND_BOND_A, GROUND_BOND_DWELL_S, HIPOT_DWELL_S, HIPOT_VDC


def hipot_and_bond(measurements, bench, unit, log):
    """Setup: withstand and ground bond with the AC source off. A module
    with a pinched primary lead or a missing earth screw fails here in
    three seconds, before any of the 12 kW ever flows through it."""
    bench.ac_off()
    bench.set_load_a(0.0)
    leak = bench.hipot_dc(HIPOT_VDC, HIPOT_DWELL_S)
    bond = bench.ground_bond(GROUND_BOND_A, GROUND_BOND_DWELL_S)
    measurements.hipot_leakage_ma = leak
    measurements.ground_bond_mohm = bond
    unit.metadata["hipot_vdc"] = HIPOT_VDC
    log.info(f"{unit.serial_number}: {HIPOT_VDC:.0f} Vdc for {HIPOT_DWELL_S:.0f} s leaks {leak:.3f} mA, bond {bond:.1f} mOhm at {GROUND_BOND_A:.0f} A")
