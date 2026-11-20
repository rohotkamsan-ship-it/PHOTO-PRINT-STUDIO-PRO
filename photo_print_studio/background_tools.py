"""Reliable local AI background removal using rembg and ONNX Runtime."""
from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageOps


@lru_cache(maxsize=1)
def _get_rembg_session():
    """Create one reusable CPU session; the model is downloaded on first use."""
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
            "On first use, connect to the internet so the free U2-Net model "
            "can download, then try again. Details: " + str(exc)
        ) from exc


def prepare_image(source: str, output: str, background: str | None = None) -> str:
    """Remove a photo background and optionally composite a solid color.

    The rembg API is called with PNG bytes rather than a PIL object to keep
    input/output behavior consistent across rembg releases and frozen EXEs.
    """
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
