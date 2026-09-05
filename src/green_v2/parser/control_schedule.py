from __future__ import annotations

from typing import Any

from green_v2.parser.register_values import decode_u16


CONTROL_ADDRESS = 0x000
EXTRA_CONTROL_ADDRESS = 0x046
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
PERIODS = (
    "charge_1_start_hhmm",
    "charge_1_end_hhmm",
    "discharge_1_start_hhmm",
    "discharge_1_end_hhmm",
    "charge_2_start_hhmm",
    "charge_2_end_hhmm",
    "discharge_2_start_hhmm",
    "discharge_2_end_hhmm",
)


def parse_control_schedule(registers: list[int], device_id: str) -> dict[str, Any]:
    metrics = {
        "demand_setting_kw": decode_u16(registers[0]),
        "charge_discharge_mode": decode_u16(registers[1]),
        "backup_start_charging_pct": decode_u16(registers[64]),
        "backup_stop_charging_pct": decode_u16(registers[65]),
        "reboot_flag": decode_u16(registers[66]),
        "disaster_dispatch_backup": decode_u16(registers[67]),
        "backup_discharge_test": decode_u16(registers[68]),
        "backup_discharge_test_soc_min": decode_u16(registers[69]),
    }
    if len(registers) > 70:
        metrics["non_custom_soc_stop_discharge_pct"] = decode_u16(registers[70])
    _add_weekly_periods(metrics, registers)
    return _device_group(device_id, metrics)


def parse_extra_control(registers: list[int], device_id: str) -> dict[str, Any]:
    return _device_group(
        device_id,
        {"non_custom_soc_stop_discharge_pct": decode_u16(registers[0])},
    )


def _add_weekly_periods(metrics: dict[str, Any], registers: list[int]) -> None:
    for day_index, weekday in enumerate(WEEKDAYS):
        for period_index, period in enumerate(PERIODS):
            offset = 2 + day_index * len(PERIODS) + period_index
            metrics[f"schedule_{weekday}_{period}"] = decode_u16(registers[offset])


def _device_group(device_id: str, metrics: dict[str, Any]) -> dict[str, Any]:
    return {"source_type": "device", "source_id": device_id, "metrics": metrics}
