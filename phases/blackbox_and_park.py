def blackbox_and_park(measurements, bench, log):
    """Teardown: the blackbox must hold exactly the events this test caused,
    then it is cleared so the log the customer reads starts in their rack.
    Load to zero and AC off last, whatever happened before."""
    bench.set_load_a(0.0)
    before = bench.modbus_blackbox()
    bench.modbus_clear_blackbox()
    after = bench.modbus_blackbox()
    bench.ac_off()
    measurements.blackbox_after_test = before
    measurements.blackbox_after_clear = after
    log.info(f"Blackbox held {before}, cleared to {after}, AC off")
