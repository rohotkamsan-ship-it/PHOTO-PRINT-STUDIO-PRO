"""Deterministic photo-sheet layout calculations in millimetres."""
from __future__ import annotations

from dataclasses import dataclass
from math import floor


@dataclass(frozen=True)
class PhotoPlacement:
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float


def calculate_layout(
    paper_width_mm: float,
    paper_height_mm: float,
    photo_width_mm: float,
    photo_height_mm: float,
    copies: int,
    margin_mm: float = 5.0,
    spacing_mm: float = 3.0,
) -> list[PhotoPlacement]:
    values = (paper_width_mm, paper_height_mm, photo_width_mm, photo_height_mm)
    if any(v <= 0 for v in values):
        raise ValueError("Paper and photo dimensions must be positive.")
    if copies < 1:
        raise ValueError("Copies must be at least 1.")
    if margin_mm < 0 or spacing_mm < 0:
        raise ValueError("Margin and spacing cannot be negative.")

    usable_w = paper_width_mm - 2 * margin_mm
    usable_h = paper_height_mm - 2 * margin_mm
    if usable_w < photo_width_mm or usable_h < photo_height_mm:
        raise ValueError("A photo does not fit inside the printable paper area.")

    cols = floor((usable_w + spacing_mm) / (photo_width_mm + spacing_mm))
    rows = floor((usable_h + spacing_mm) / (photo_height_mm + spacing_mm))
    if cols < 1 or rows < 1:
        raise ValueError("No photos fit on this paper size.")

    capacity = cols * rows
    placements: list[PhotoPlacement] = []
    for index in range(min(copies, capacity)):
        row, col = divmod(index, cols)
        placements.append(
            PhotoPlacement(
                x_mm=margin_mm + col * (photo_width_mm + spacing_mm),
                y_mm=margin_mm + row * (photo_height_mm + spacing_mm),
                width_mm=photo_width_mm,
                height_mm=photo_height_mm,
            )
        )
    return placements


def pages_for_copies(
    paper_width_mm: float,
    paper_height_mm: float,
    photo_width_mm: float,
    photo_height_mm: float,
    copies: int,
    margin_mm: float = 5.0,
    spacing_mm: float = 3.0,
) -> int:
    if copies < 1:
        raise ValueError("Copies must be at least 1.")
    one_page = calculate_layout(
        paper_width_mm, paper_height_mm, photo_width_mm, photo_height_mm,
        copies=10**9, margin_mm=margin_mm, spacing_mm=spacing_mm
    )
    return (copies + len(one_page) - 1) // len(one_page)
