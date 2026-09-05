from __future__ import annotations

from typing import Any

from green_v2.parser.register_values import (
    decode_s16,
    decode_s32,
    decode_u16,
    decode_u32,
    decode_u64,
)


MAIN_STATUS_ADDRESS = 0x1E0


def parse_main_status(registers: list[int], device_id: str) -> dict[str, Any]:
    metrics = {
        "ac_input_voltage": decode_u16(registers[0], 0.01),
        "ac_output_voltage": decode_u16(registers[1], 0.01),
        "ac_output_power": decode_u16(registers[2]),
        "pv_voltage": decode_u16(registers[3], 0.01),
        "pv_power": decode_u16(registers[4]),
        "dc_output_voltage": decode_u16(registers[5], 0.01),
        "dc_output_current": decode_s16(registers[6]),
        "ct_power_w": decode_u32(registers, 7, 0.01),
        "soc_total": decode_u16(registers[9], 0.01),
        "soh_total": decode_u16(registers[10], 0.01),
        "temperature_c": decode_u16(registers[11], 0.01),
        "ac_energy_kwh": decode_u64(registers, 12, 0.01),
        "ct_energy_kwh": decode_u64(registers, 16, 0.01),
        "pv_energy_kwh": decode_u64(registers, 20, 0.01),
        "dc_output_power": decode_s32(registers, 24, 0.1),
        "power_w": decode_s16(registers[26], 0.1),
        "version_number": decode_u16(registers[27]),
        "utility_charge_energy_kwh": decode_u64(registers, 28, 0.01),
        "with_mains_dc_discharge_energy_kwh": decode_u64(registers, 32, 0.01),
        "without_mains_dc_discharge_energy_kwh": decode_u64(registers, 36, 0.01),
        "power_outage_count": decode_u16(registers[40]),
    }
    return {"source_type": "device", "source_id": device_id, "metrics": metrics}
