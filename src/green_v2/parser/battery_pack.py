from __future__ import annotations

from typing import Any

from green_v2.parser.register_values import decode_s16, decode_u16


PACK_BASES = {
    0x000: 1,
    0x050: 2,
    0x0A0: 3,
    0x0F0: 4,
    0x140: 5,
    0x190: 6,
}


def parse_pack_metrics(registers: list[int], pack_index: int) -> dict[str, Any]:
    metrics = _base_metrics(registers)
    _add_temperature_metrics(metrics, registers)
    _add_cell_metrics(metrics, registers)
    metrics["power_w"] = round(metrics["voltage_v"] * metrics["current_a"], 2)
    metrics["balance_count_total"] = sum(
        metrics[f"cell_{index}_balance_count"] for index in range(1, 17)
    )
    metrics.update(_protection_metrics(registers))
    return _metric_group(pack_index, metrics)


def parse_pack_alarms(bits: list[int], pack_index: int) -> dict[str, Any]:
    metrics = _base_alarm_metrics(bits)
    for index in range(16):
        number = index + 1
        metrics[f"cell_{number}_over_voltage_alarm"] = bool(bits[6 + index])
        metrics[f"cell_{number}_under_voltage_alarm"] = bool(bits[22 + index])
        metrics[f"cell_{number}_generic_alarm"] = bool(bits[64 + index])
    return _metric_group(pack_index, metrics)


def _base_metrics(registers: list[int]) -> dict[str, Any]:
    return {
        "remaining_ah": decode_u16(registers[0], 0.01),
        "environment_temperature_c": decode_s16(registers[1]),
        "voltage_v": decode_u16(registers[2], 0.01),
        "current_a": decode_s16(registers[3], 0.01),
        "soc": decode_u16(registers[4], 0.1),
        "soh": decode_u16(registers[5], 0.1),
        "daily_charge_ah": decode_u16(registers[6], 0.1),
        "daily_discharge_ah": decode_u16(registers[7], 0.1),
        "cell_max_voltage_v": decode_u16(registers[8], 0.001),
        "cell_min_voltage_v": decode_u16(registers[9], 0.001),
        "cell_max_index": decode_u16(registers[10]),
        "cell_min_index": decode_u16(registers[11]),
        "cell_voltage_delta_v": decode_u16(registers[12], 0.001),
        "average_cell_voltage_v": decode_u16(registers[13], 0.001),
    }


def _add_temperature_metrics(metrics: dict[str, Any], registers: list[int]) -> None:
    temperatures = [decode_s16(registers[14 + index], 0.1) for index in range(4)]
    metrics["temperature_c"] = max(temperatures)
    for index, value in enumerate(temperatures, start=1):
        metrics[f"temperature_probe_{index}_c"] = value
    for index in range(4):
        metrics[f"max_temperature_index_{index + 1}"] = decode_u16(registers[18 + index])
        metrics[f"min_temperature_index_{index + 1}"] = decode_u16(registers[22 + index])


def _add_cell_metrics(metrics: dict[str, Any], registers: list[int]) -> None:
    for index in range(16):
        number = index + 1
        metrics[f"cell_{number}_voltage_v"] = decode_u16(registers[26 + index], 0.001)
        metrics[f"cell_{number}_balance_count"] = decode_u16(registers[42 + index])


def _protection_metrics(registers: list[int]) -> dict[str, Any]:
    return {
        "pack_over_voltage_alarm_v": decode_u16(registers[64], 0.01),
        "pack_under_voltage_alarm_v": decode_u16(registers[65], 0.01),
        "charge_over_temperature_protection_c": decode_s16(registers[66]),
        "discharge_over_temperature_protection_c": decode_s16(registers[67]),
        "max_charge_voltage_v": decode_u16(registers[68], 0.01),
        "max_charge_current_a": decode_u16(registers[69]),
        "cycle_count": decode_u16(registers[70]),
    }


def _base_alarm_metrics(bits: list[int]) -> dict[str, Any]:
    names = {
        0: "communication_alarm",
        1: "pack_alarm_active",
        2: "charging",
        3: "discharging",
        4: "pack_over_voltage_alarm",
        5: "pack_under_voltage_alarm",
        38: "cell_voltage_abnormal_alarm",
        39: "cell_temperature_abnormal_alarm",
        40: "charge_over_temperature_alarm",
        41: "charge_under_temperature_alarm",
        42: "discharge_over_temperature_alarm",
        43: "discharge_under_temperature_alarm",
        44: "charge_temperature_1_alarm",
        45: "charge_temperature_2_alarm",
        46: "charge_temperature_3_alarm",
        47: "charge_temperature_4_alarm",
        48: "charge_temperature_low_1_alarm",
        49: "charge_temperature_low_2_alarm",
        50: "charge_temperature_low_3_alarm",
        51: "charge_temperature_low_4_alarm",
        52: "discharge_temperature_1_alarm",
        53: "discharge_temperature_2_alarm",
        54: "discharge_temperature_3_alarm",
        55: "discharge_temperature_4_alarm",
        56: "discharge_temperature_low_1_alarm",
        57: "discharge_temperature_low_2_alarm",
        58: "discharge_temperature_low_3_alarm",
        59: "discharge_temperature_low_4_alarm",
        60: "cell_balance_alarm",
        61: "discharge_contactor_closed",
        62: "charge_contactor_closed",
        63: "cell_voltage_delta_alarm",
    }
    metrics = {name: bool(bits[index]) for index, name in names.items()}
    metrics["active_alarm_count"] = sum(1 for bit in bits if bit)
    return metrics


def _metric_group(pack_index: int, metrics: dict[str, Any]) -> dict[str, Any]:
    return {"source_type": "battery_pack", "source_id": f"pack-{pack_index}", "metrics": metrics}
