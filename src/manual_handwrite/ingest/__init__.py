"""Deterministic offline page preprocessing."""

from __future__ import annotations

from numbers import Integral

import numpy as np
from PIL import Image, ImageOps

from manual_handwrite.data import LineRegion


def _as_grayscale_image(image: Image.Image | np.ndarray) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.copy()
    if not isinstance(image, np.ndarray):
        raise TypeError("image must be a Pillow Image or NumPy array")
    if image.ndim not in (2, 3) or image.ndim == 3 and image.shape[2] not in (1, 3, 4):
        raise ValueError("NumPy image must have shape (height, width[, channels])")
    if image.dtype.kind not in "biuf":
        raise TypeError("NumPy image must contain numeric pixels")
    array = image
    if array.dtype.kind == "f":
        if not np.isfinite(array).all():
            raise ValueError("image contains non-finite pixels")
        array = np.clip(array, 0, 255).astype(np.uint8)
    elif array.dtype != np.uint8:
        array = np.clip(array, 0, 255).astype(np.uint8)
    if array.ndim == 3 and array.shape[2] == 1:
        array = array[..., 0]
    return Image.fromarray(array)


def normalize_page(image: Image.Image | np.ndarray) -> np.ndarray:
    """Return an EXIF-oriented, grayscale, contrast-normalized page.

    The source is copied and never modified. Contrast limits are the 1st and
    99th percentiles; a flat page is returned unchanged rather than becoming
    black or white through division by zero.
    """
    oriented = ImageOps.exif_transpose(_as_grayscale_image(image))
    gray = np.asarray(oriented.convert("L"), dtype=np.uint8)
    if gray.size == 0:
        return gray.copy()

    low, high = np.percentile(gray, (1, 99))
    if high <= low:
        return gray.copy()
    normalized = (gray.astype(np.float64) - low) * (255.0 / (high - low))
    return np.clip(np.rint(normalized), 0, 255).astype(np.uint8)


def segment_lines(
    page: np.ndarray,
    *,
    threshold: int = 200,
    min_ink_pixels: int = 1,
    gap_tolerance: int = 0,
) -> list[LineRegion]:
    """Find dark horizontal runs and return full-width page regions.

    A row is active when it contains at least ``min_ink_pixels`` pixels below
    ``threshold``. Consecutive active rows form one region; ``gap_tolerance``
    optionally bridges short blank gaps within a handwritten line.
    """
    if not isinstance(page, np.ndarray) or page.ndim != 2:
        raise ValueError("page must be a two-dimensional NumPy array")
    if page.dtype.kind not in "biuf":
        raise TypeError("page must contain numeric grayscale pixels")
    if not isinstance(threshold, Integral) or not 0 <= threshold <= 255:
        raise ValueError("threshold must be an integer between 0 and 255")
    if not isinstance(min_ink_pixels, Integral) or min_ink_pixels < 1:
        raise ValueError("min_ink_pixels must be a positive integer")
    if not isinstance(gap_tolerance, Integral) or gap_tolerance < 0:
        raise ValueError("gap_tolerance must be a non-negative integer")

    height, width = page.shape
    if height == 0 or width == 0:
        return []
    active = np.count_nonzero(page < threshold, axis=1) >= min_ink_pixels
    if gap_tolerance:
        active = active.copy()
        active_indices = np.flatnonzero(active)
        for start, end in zip(active_indices, active_indices[1:], strict=False):
            if end - start - 1 <= gap_tolerance:
                active[start : end + 1] = True

    regions: list[LineRegion] = []
    row = 0
    while row < height:
        if not active[row]:
            row += 1
            continue
        start = row
        while row < height and active[row]:
            row += 1
        regions.append(
            LineRegion(x=0, y=start, width=width, height=row - start, line_index=len(regions))
        )
    return regions


__all__ = ["normalize_page", "segment_lines"]
