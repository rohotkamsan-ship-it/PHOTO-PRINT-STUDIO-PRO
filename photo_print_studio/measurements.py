"""Unit conversion and standard photo/paper sizes."""
from __future__ import annotations

MM_PER_INCH = 25.4
MM_PER_CM = 10.0

PHOTO_PRESETS_MM: dict[str, tuple[float, float]] = {
    "2x3": (20.0, 30.0),
    "3x4": (30.0, 40.0),
    "4x6": (40.0, 60.0),
}
PAPER_PRESETS_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
    "10x15 cm": (100.0, 150.0),
}


def mm_to_unit(value_mm: float, unit: str) -> float:
    unit = unit.lower()
    if unit == "mm":
        return value_mm
    if unit == "cm":
        return value_mm / MM_PER_CM
    raise ValueError(f"Unsupported unit: {unit}")


def unit_to_mm(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit == "mm":
        return value
    if unit == "cm":
        return value * MM_PER_CM
    raise ValueError(f"Unsupported unit: {unit}")


def photo_size(name: str, unit: str = "mm") -> tuple[float, float]:
    try:
        width, height = PHOTO_PRESETS_MM[name]
    except KeyError as exc:
        raise ValueError(f"Unknown photo preset: {name}") from exc
    return mm_to_unit(width, unit), mm_to_unit(height, unit)


def paper_size(name: str) -> tuple[float, float]:
    try:
        return PAPER_PRESETS_MM[name]
    except KeyError as exc:
        raise ValueError(f"Unknown paper preset: {name}") from exc
