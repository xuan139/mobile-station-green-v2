from __future__ import annotations

from typing import Any


CONTROLLER_STATUS_ADDRESS = 0x1F0


def parse_controller_bits(bits: list[int], device_id: str) -> dict[str, Any]:
    metrics = {
        "ac_in": bool(bits[0]),
        "pv_in": bool(bits[1]),
        "battery_in": bool(bits[2]),
        "bypass": bool(bits[3]),
        "ac_charging": bool(bits[4]),
        "pv_charging": bool(bits[5]),
        "inverter_output": bool(bits[6]),
        "fault_active_count": sum(1 for bit in bits[16:] if bit),
    }
    metrics.update(_fault_metrics(bits))
    return {"source_type": "device", "source_id": device_id, "metrics": metrics}


def _fault_metrics(bits: list[int]) -> dict[str, bool]:
    names = {
        16: "fan_fault",
        17: "over_temperature_fault",
        18: "battery_voltage_high_fault",
        19: "battery_voltage_low_fault",
        20: "output_shorted_fault",
        21: "inverter_voltage_over_fault",
        22: "over_load_fault",
        23: "pv_voltage_high_fault",
        24: "over_current_fault",
        25: "bus_voltage_under_fault",
        26: "inverter_softstart_fault",
        27: "dc_voltage_ct_fault",
        28: "current_detect_fault",
        29: "inverter_voltage_low_fault",
        30: "fan_alarm",
        31: "over_temperature_alarm",
        32: "battery_over_charged_alarm",
        33: "battery_voltage_low_alarm",
        34: "over_load_alarm",
        35: "output_derating_alarm",
        36: "pv_energy_weak_alarm",
        37: "ac_voltage_high_alarm",
        38: "bus_voltage_over_fault",
        39: "no_battery_alarm",
    }
    return {name: bool(bits[index]) for index, name in names.items()}
