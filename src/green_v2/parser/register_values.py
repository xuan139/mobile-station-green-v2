from __future__ import annotations


def decode_u16(value: int, scale: float = 1.0) -> float:
    return value * scale


def decode_s16(value: int, scale: float = 1.0) -> float:
    signed = value - 0x10000 if value >= 0x8000 else value
    return signed * scale


def decode_u32(registers: list[int], offset: int, scale: float = 1.0) -> float:
    chunk = registers[offset : offset + 2]
    if len(chunk) != 2:
        raise ValueError("u32 field requires exactly 2 registers")
    return ((chunk[0] << 16) | chunk[1]) * scale


def decode_s32(registers: list[int], offset: int, scale: float = 1.0) -> float:
    chunk = registers[offset : offset + 2]
    if len(chunk) != 2:
        raise ValueError("s32 field requires exactly 2 registers")
    value = (chunk[0] << 16) | chunk[1]
    if value >= 0x80000000:
        value -= 0x100000000
    return value * scale


def decode_u64(registers: list[int], offset: int, scale: float = 1.0) -> float:
    chunk = registers[offset : offset + 4]
    if len(chunk) != 4:
        raise ValueError("u64 field requires exactly 4 registers")
    value = (chunk[0] << 48) | (chunk[1] << 32) | (chunk[2] << 16) | chunk[3]
    return value * scale
