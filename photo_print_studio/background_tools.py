"""Free local background removal and solid-color compositing."""
from __future__ import annotations

from pathlib import Path
from PIL import Image
import io


def prepare_image(source: str, output: str, background: str | None = None) -> str:
    """Remove image background with rembg, optionally composite a solid color."""
    try:
        from rembg import remove
    except ImportError as exc:
        raise RuntimeError(
            "AI background removal is not installed. Install the app's requirements."
        ) from exc

    image = Image.open(source).convert("RGBA")
    result = remove(image)
    if isinstance(result, bytes):
        result = Image.open(io.BytesIO(result)).convert("RGBA")
    else:
        result = result.convert("RGBA")

    if background and background.lower() not in {"transparent", "none"}:
        color = background if background.startswith("#") else "#ffffff"
        canvas = Image.new("RGBA", result.size, color)
        canvas.alpha_composite(result)
        result = canvas.convert("RGB")
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    result.save(output, format="PNG")
    return output
