"""ORV3 PSU acceptance bench (mock): AC source, DC electronic load, power
analyzer, hipot tester, oscilloscope and the PSU's Modbus management port,
one plug because every reading depends on what the source and the load
are doing at that instant.

Maps to a Chroma 61512 AC source (or a Pacific Power 3120AFX), a Chroma
63200A-series 12 kW DC load, a Yokogawa WT5000 power analyzer, a Chroma
19032 hipot/ground-bond tester, a 4-channel scope on the output and the
inrush CT, and a USB-RS485 adapter on the PSU's Modbus port. The mock
synthesizes a healthy module: Titanium-class efficiency peaking at 50 %
load, 7.2 mF of bulk capacitance, comparators inside every window, a
blackbox that records exactly what the test does to it. Swap for classes
speaking SCPI and pymodbus; the phases stay unchanged.
"""

import math

import numpy as np

from utils.recipe import (
    IDENTITY,
    INRUSH_CAPTURE_MS,
    INRUSH_SAMPLE_KHZ,
    MAINS_HZ,
    RATED_A,
    VOUT_SET_V,
)

# Efficiency in percent at the six load points, 277 Vac. 230 Vac runs a
# little lower from the higher input current, except at the 50 % peak.
_EFF_277 = {10: 94.6, 20: 96.3, 30: 97.0, 50: 97.8, 75: 97.7, 100: 97.2}
_EFF_230_DELTA = {10: -0.3, 20: -0.2, 30: -0.1, 50: -0.1, 75: -0.15, 100: -0.2}


class PsuBench:
    BULK_CAP_F = 0.0072
    BUS_V = 400.0
    BUS_UVLO_V = 290.0
    AC_LOSS_DETECT_MS = 2.6  # one missed half-cycle at 50 Hz, then the comparator
    OUTPUT_TAU_MS = 4.0  # output capacitors into the load once the stage stops

    def __init__(self, serial_number):
        self.serial_number = str(serial_number)
        self._rng = np.random.default_rng(12000)
        self._ac_v = 0.0
        self._load_a = 0.0
        self._trim_v = VOUT_SET_V
        self._temp_override_c = None
        self._faults = {"ovp": False, "ocp": False, "otw": False, "otp": False}
        self._blackbox = {"ac_loss": 0, "ovp": 0, "ocp": 0, "otw": 0, "otp": 0, "fan": 0}
        # Comparators of this module, all inside their windows.
        self._ovp_trip_v = 53.12
        self._cc_limit_a = 1.204 * RATED_A  # 286 A
        self._otw_c = 85.4
        self._otp_c = 95.2
        # self.ac = pyvisa...; self.load = pyvisa...; self.wt = pyvisa...; self.hipot = pyvisa...; self.modbus = ModbusSerialClient(...)
        print(f"PSU bench connected: AC source off, load 0 A, Modbus port open for {self.serial_number}")

    # --- hipot and ground bond (AC off) --------------------------------------

    def hipot_dc(self, volts, dwell_s):
        """Primary to chassis withstand; leakage in mA after the dwell.
        Y-capacitors leak nothing at DC, so a healthy module reads in the
        tens of microamps."""
        return round(0.11 + 0.02 * volts / 2121.0 + abs(self._rng.normal(0.0, 0.01)), 3)

    def ground_bond(self, amps, dwell_s):
        """Bond resistance from the inlet earth pin to the chassis, in mOhm."""
        return round(38.0 + self._rng.normal(0.0, 1.5), 1)

    # --- AC source and load ----------------------------------------------------

    def ac_on(self, volts):
        self._ac_v = float(volts)

    def ac_off(self):
        self._ac_v = 0.0

    def set_load_a(self, amps):
        self._load_a = float(amps)
        if amps > self._cc_limit_a:
            self._faults["ocp"] = True

    def vout_v(self):
        if self._ac_v == 0.0 or self._faults["ovp"] or self._faults["otp"]:
            return 0.0
        if self._load_a > self._cc_limit_a:
            return round(VOUT_SET_V * self._cc_limit_a / self._load_a, 2)
        return round(self._trim_v + self._rng.normal(0.0, 0.01), 3)

    def inrush_capture(self, close_angle_deg):
        """Cold start at the stated phase angle: the inrush CT on the scope,
        samples in amps over the capture window."""
        n = int(INRUSH_CAPTURE_MS * INRUSH_SAMPLE_KHZ)
        t = np.arange(n) / (INRUSH_SAMPLE_KHZ * 1000.0)
        peak = 61.8
        tau = 0.008
        i = peak * np.exp(-t / tau) * np.abs(np.sin(2 * math.pi * MAINS_HZ * t + math.radians(close_angle_deg)))
        i += self._rng.normal(0.0, 0.15, n)
        return (t * 1000.0).round(3).tolist(), i.round(2).tolist()

    # --- power analyzer and telemetry ---------------------------------------------

    def analyzer_pin_pout_w(self, load_pct):
        """Input and output power from the analyzer at the present AC voltage
        and load. Efficiency of the mock is a table with 0.03 % of noise."""
        eff = _EFF_277[load_pct] + (_EFF_230_DELTA[load_pct] if self._ac_v < 250.0 else 0.0)
        eff += self._rng.normal(0.0, 0.03)
        pout = self._load_a * self._trim_v
        return round(pout / (eff / 100.0), 1), round(pout, 1)

    def modbus_iout_a(self):
        """Output current as the PSU reports it: a 0.6 % gain error and a
        0.2 A offset in this module's calibration."""
        return round(self._load_a * 1.006 + 0.2, 2)

    def modbus_identity(self):
        return dict(IDENTITY)

    def modbus_serial(self):
        return self.serial_number

    # --- ripple and dynamic load -------------------------------------------------

    def ripple_mvpp(self, bandwidth_mhz):
        return round(210.0 + abs(self._rng.normal(0.0, 6.0)), 1)

    def transient_capture(self, from_pct, to_pct, slew_a_per_us):
        """Output deviation from set-point after a load step, on the scope,
        in volts over the capture window. A damped 0.9 kHz loop response."""
        n = 400
        t = np.arange(n) / 100.0  # ms, 10 us per sample
        sign = -1.0 if to_pct > from_pct else 1.0
        amp = 0.82 if to_pct > from_pct else 0.74
        dev = sign * amp * np.exp(-t / 1.2) * np.cos(2 * math.pi * 0.9 * t)
        dev += self._rng.normal(0.0, 0.008, n)
        return t.round(2).tolist(), dev.round(4).tolist()

    # --- hold-up -----------------------------------------------------------------

    def ac_loss_capture(self, load_pct):
        """AC removed at t = 0 at the present load: output voltage on the scope
        and the AC_Loss_L assertion time. The stage regulates from the bulk
        capacitors until the bus reaches UVLO, then the output capacitors
        discharge into the load."""
        self._blackbox["ac_loss"] += 1
        p = self._load_a * self._trim_v
        hold_s = self.BULK_CAP_F * (self.BUS_V**2 - self.BUS_UVLO_V**2) / (2.0 * p)
        n = 400
        t = np.arange(n) / 10.0  # ms
        v = np.where(t < hold_s * 1000.0, self._trim_v, self._trim_v * np.exp(-(t - hold_s * 1000.0) / self.OUTPUT_TAU_MS))
        v = v + self._rng.normal(0.0, 0.01, n)
        return t.round(1).tolist(), v.round(3).tolist(), self.AC_LOSS_DETECT_MS

    # --- protections, test mode over Modbus ------------------------------------------

    def modbus_trim_vout(self, volts):
        self._trim_v = float(volts)
        if volts >= self._ovp_trip_v:
            self._faults["ovp"] = True

    def ovp_response_ms(self):
        """Trip edge to output off, on the scope."""
        return round(38.0 + abs(self._rng.normal(0.0, 2.0)), 1)

    def ocp_shutdown_s(self):
        """Time in constant current with the output out of regulation before
        the module shuts down and restarts, from the fault log timestamp."""
        return round(10.2 + self._rng.normal(0.0, 0.1), 2)

    def modbus_override_temp_c(self, temp_c):
        self._temp_override_c = float(temp_c)
        if temp_c >= self._otw_c:
            self._faults["otw"] = True
        if temp_c >= self._otp_c:
            self._faults["otp"] = True

    def modbus_faults(self):
        return dict(self._faults)

    def modbus_clear_faults(self):
        for k, v in self._faults.items():
            if v:
                self._blackbox[k] += 1
        self._faults = {k: False for k in self._faults}
        self._trim_v = VOUT_SET_V
        self._temp_override_c = None

    def modbus_blackbox(self):
        return dict(self._blackbox)

    def modbus_clear_blackbox(self):
        self._blackbox = {k: 0 for k in self._blackbox}

    def __del__(self):
        print("Load 0 A, AC source off, bench released")
