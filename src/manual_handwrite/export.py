"""PNG and PDF export with mandatory provenance metadata."""

from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import BinaryIO

from PIL import Image
from PIL.PngImagePlugin import PngInfo

GENERATOR = "manual-handwrite-ia"
Destination = str | PathLike[str] | BinaryIO


def _metadata(metadata: dict[str, str] | None) -> dict[str, str]:
    values = {str(key): str(value) for key, value in (metadata or {}).items()}
    values["generator"] = GENERATOR
    return values


def export_png(
    image: Image.Image, destination: Destination, metadata: dict[str, str] | None = None
) -> None:
    """Write a Pillow image as PNG, retaining supplied text metadata."""
    info = PngInfo()
    for key, value in _metadata(metadata).items():
        info.add_text(key, value)
    image.save(destination, format="PNG", pnginfo=info)


def export_pdf(
    image: Image.Image, destination: Destination, metadata: dict[str, str] | None = None
) -> None:
    """Write a single-page PDF whose Producer identifies this generator."""
    values = _metadata(metadata)
    pdf_image = image.convert("RGB") if image.mode not in {"RGB", "L"} else image
    pdf_kwargs: dict[str, str] = {"producer": values["generator"]}
    for key in ("title", "author", "subject", "keywords", "creator"):
        if key in values:
            pdf_kwargs[key] = values[key]
    pdf_image.save(destination, format="PDF", resolution=300.0, **pdf_kwargs)


def export_image(
    image: Image.Image,
    destination: Destination,
    format: str | None = None,
    metadata: dict[str, str] | None = None,
) -> None:
    """Export based on an explicit format or the destination suffix."""
    selected = (format or Path(destination).suffix.lstrip(".")).lower()
    if selected == "png":
        export_png(image, destination, metadata)
    elif selected == "pdf":
        export_pdf(image, destination, metadata)
    else:
        raise ValueError("format must be png or pdf")


save_png = export_png
save_pdf = export_pdf
