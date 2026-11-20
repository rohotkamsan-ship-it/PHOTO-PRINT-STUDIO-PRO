"""Reliable local AI background removal using rembg and ONNX Runtime."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageOps


# PyInstaller windowed applications may start with stdout/stderr set to None.
# Some rembg/ONNX Runtime initialization paths write diagnostics to these streams.
_NULL_STREAMS = []


def _ensure_stdio():
    """Provide writable standard streams for libraries inside GUI/frozen builds."""
    for name in ("stdout", "stderr"):
        if getattr(sys, name, None) is None:
            stream = open(os.devnull, "w", encoding="utf-8")
            _NULL_STREAMS.append(stream)
            setattr(sys, name, stream)


@lru_cache(maxsize=1)
def _get_rembg_session():
    """Create one reusable CPU session; the model is downloaded on first use."""
    _ensure_stdio()
    try:
        from rembg import new_session
    except ImportError as exc:
        raise RuntimeError(
            "AI background removal components are missing. "
            "Please reinstall PHOTO PRINT STUDIO PRO."
        ) from exc

    try:
        return new_session("u2net", providers=["CPUExecutionProvider"])
    except Exception as exc:
        raise RuntimeError(
            "Could not initialize the AI background-removal model. "
            "Check your internet connection on first use so the free U2-Net "
            "model can download. Technical details: " + str(exc)
        ) from exc


def prepare_image(source: str, output: str, background: str | None = None) -> str:
    """Remove a photo background and optionally composite a solid color.

    rembg receives PNG bytes for consistent behavior across releases and
    frozen EXEs. Standard streams are repaired before importing rembg because
    importing or initializing ONNX Runtime may emit diagnostic messages.
    """
    _ensure_stdio()
    try:
        from rembg import remove
    except ImportError as exc:
        raise RuntimeError(
            "AI background removal components are missing. "
            "Please reinstall PHOTO PRINT STUDIO PRO."
        ) from exc

    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(f"Photo file not found: {source_path}")

    try:
        with Image.open(source_path) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGBA")
            input_buffer = BytesIO()
            image.save(input_buffer, format="PNG")
            input_bytes = input_buffer.getvalue()

        session = _get_rembg_session()
        result = remove(input_bytes, session=session)
        if isinstance(result, Image.Image):
            foreground = result.convert("RGBA")
        elif isinstance(result, (bytes, bytearray)):
            with Image.open(BytesIO(result)) as output_image:
                foreground = output_image.convert("RGBA")
        else:
            raise RuntimeError(
                f"Unexpected AI result type: {type(result).__name__}"
            )

        if background and background.lower() not in {"transparent", "none"}:
            color = background if background.startswith("#") else "#ffffff"
            canvas = Image.new("RGBA", foreground.size, color)
            canvas.alpha_composite(foreground)
            foreground = canvas.convert("RGB")

        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        foreground.save(output_path, format="PNG", optimize=True)
        return str(output_path)
    except Exception as exc:
        if isinstance(exc, (FileNotFoundError, RuntimeError)):
            raise
        raise RuntimeError(
            f"Background removal failed for '{source_path.name}': {exc}"
        ) from exc
