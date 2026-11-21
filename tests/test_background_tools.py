from types import SimpleNamespace
from PIL import Image
import pytest

from photo_print_studio import background_tools


def test_prepare_image_uses_bytes_and_writes_transparent_png(tmp_path, monkeypatch):
    source = tmp_path / "input.jpg"
    Image.new("RGB", (24, 32), "red").save(source)

    calls = {}

    def fake_new_session(model_name, providers=None):
        calls["model"] = model_name
        calls["providers"] = providers
        return object()

    def fake_remove(data, session=None):
        calls["input_type"] = type(data)
        calls["session"] = session
        image = Image.new("RGBA", (24, 32), (10, 20, 30, 100))
        from io import BytesIO
        stream = BytesIO()
        image.save(stream, format="PNG")
        return stream.getvalue()

    monkeypatch.setitem(
        __import__("sys").modules,
        "rembg",
        SimpleNamespace(new_session=fake_new_session, remove=fake_remove),
    )
    background_tools._get_rembg_session.cache_clear()
    output = tmp_path / "prepared.png"
    try:
        assert background_tools.prepare_image(str(source), str(output)) == str(output)
    finally:
        background_tools._get_rembg_session.cache_clear()

    with Image.open(output) as result:
        assert result.mode == "RGBA"
        assert result.getpixel((0, 0))[3] == 100
    assert calls["model"] == "u2net"
    assert calls["input_type"] is bytes
    assert calls["providers"] == ["CPUExecutionProvider"]


def test_prepare_image_composites_selected_background(tmp_path, monkeypatch):
    source = tmp_path / "input.png"
    Image.new("RGB", (12, 12), "white").save(source)

    def fake_new_session(model_name, providers=None):
        return object()

    def fake_remove(data, session=None):
        from io import BytesIO
        image = Image.new("RGBA", (12, 12), (255, 0, 0, 128))
        stream = BytesIO()
        image.save(stream, format="PNG")
        return stream.getvalue()

    monkeypatch.setitem(
        __import__("sys").modules,
        "rembg",
        SimpleNamespace(new_session=fake_new_session, remove=fake_remove),
    )
    background_tools._get_rembg_session.cache_clear()
    output = tmp_path / "white_background.png"
    try:
        background_tools.prepare_image(str(source), str(output), "#ffffff")
    finally:
        background_tools._get_rembg_session.cache_clear()

    with Image.open(output) as result:
        assert result.mode == "RGB"
        assert result.getpixel((0, 0)) == (255, 127, 127)


def test_prepare_image_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        background_tools.prepare_image(str(tmp_path / "missing.png"), str(tmp_path / "out.png"))


def test_ensure_stdio_repairs_missing_gui_stream(monkeypatch):
    import sys

    monkeypatch.setattr(sys, "stderr", None)
    background_tools._ensure_stdio()
    assert sys.stderr is not None
    assert callable(sys.stderr.write)



def test_background_picker_stays_enabled_for_preset_selection():
    from photo_print_studio.photo_preparation import PhotoPreparationDialog

    class Button:
        enabled = False

        def setEnabled(self, value):
            self.enabled = value

    dialog = SimpleNamespace(custom_button=Button())
    PhotoPreparationDialog._background_changed(dialog, "Blue")
    assert dialog.custom_button.enabled is True


def test_choose_color_switches_background_to_custom(monkeypatch):
    from photo_print_studio.photo_preparation import PhotoPreparationDialog

    class FakeColor:
        def isValid(self):
            return True

        def name(self):
            return "#123456"

    class Combo:
        value = "Blue"

        def currentText(self):
            return self.value

        def setCurrentText(self, value):
            self.value = value

    class Button:
        text = ""

        def setText(self, value):
            self.text = value

    combo = Combo()
    button = Button()
    dialog = SimpleNamespace(
        background_color="#ffffff",
        background=combo,
        custom_button=button,
    )
    monkeypatch.setattr(
        "photo_print_studio.photo_preparation.QColorDialog.getColor",
        lambda *args, **kwargs: FakeColor(),
    )

    PhotoPreparationDialog._choose_color(dialog)

    assert dialog.background_color == "#123456"
    assert combo.currentText() == "Custom color"
    assert button.text == "Color: #123456"


def test_apply_background_color_can_recolor_same_foreground_repeatedly(tmp_path):
    foreground = tmp_path / "subject_foreground.png"
    red_output = tmp_path / "subject_prepared.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 128)).save(foreground)

    background_tools.apply_background_color(str(foreground), str(red_output), "#00ff00")
    with Image.open(red_output) as green_result:
        assert green_result.mode == "RGB"
        assert green_result.getpixel((0, 0)) == (127, 128, 0)

    background_tools.apply_background_color(str(foreground), str(red_output), "#0000ff")
    with Image.open(red_output) as blue_result:
        assert blue_result.mode == "RGB"
        assert blue_result.getpixel((0, 0)) == (127, 0, 128)

    # The retained cutout stays transparent and unchanged for future recolors.
    with Image.open(foreground) as retained:
        assert retained.mode == "RGBA"
        assert retained.getpixel((0, 0)) == (255, 0, 0, 128)


def test_apply_background_color_transparent_keeps_alpha(tmp_path):
    foreground = tmp_path / "subject_foreground.png"
    output = tmp_path / "subject_prepared.png"
    Image.new("RGBA", (4, 4), (20, 40, 60, 90)).save(foreground)

    background_tools.apply_background_color(str(foreground), str(output), None)

    with Image.open(output) as result:
        assert result.mode == "RGBA"
        assert result.getpixel((0, 0)) == (20, 40, 60, 90)
