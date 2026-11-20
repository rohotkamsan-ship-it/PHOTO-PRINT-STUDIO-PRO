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
