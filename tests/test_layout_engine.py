import pytest

from photo_print_studio.layout_engine import calculate_layout, pages_for_copies


def test_a4_fits_expected_number_of_3x4_photos():
    items = calculate_layout(210, 297, 30, 40, 8, margin_mm=5, spacing_mm=3)
    assert len(items) == 8
    assert items[0].x_mm == 5
    assert items[0].y_mm == 5


def test_placements_stay_inside_paper():
    items = calculate_layout(148, 210, 30, 40, 20, margin_mm=5, spacing_mm=3)
    for item in items:
        assert item.x_mm + item.width_mm <= 148 - 5
        assert item.y_mm + item.height_mm <= 210 - 5


def test_invalid_dimensions_raise():
    with pytest.raises(ValueError):
        calculate_layout(210, 297, 0, 40, 1)


def test_pages_for_large_copy_count():
    assert pages_for_copies(210, 297, 30, 40, 100) > 1
