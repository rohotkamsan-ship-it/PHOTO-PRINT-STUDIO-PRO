import pytest

from photo_print_studio.measurements import photo_size, paper_size, unit_to_mm, mm_to_unit


def test_photo_preset_switches_units():
    assert photo_size("3x4", "mm") == (30.0, 40.0)
    assert photo_size("3x4", "cm") == (3.0, 4.0)


def test_unit_conversion_round_trip():
    assert unit_to_mm(mm_to_unit(42.5, "cm"), "cm") == pytest.approx(42.5)


def test_unknown_unit_fails():
    with pytest.raises(ValueError):
        mm_to_unit(10, "inch")


def test_10x15_cm_paper_preset():
    assert paper_size("10x15 cm") == (100.0, 150.0)
