"""Deterministic, local simulation of scanned-paper imperfections."""

from __future__ import annotations

import random
from io import BytesIO
from typing import Any

_PRESETS = {
    "scanner-escritorio": {
        "paper": 246,
        "texture": 3,
        "noise": 1.5,
        "bleed": 0.35,
        "rotation": 0.45,
        "vignette": 0.025,
        "jpeg": 85,
    },
    "foto-celular": {
        "paper": 242,
        "texture": 5,
        "noise": 3.0,
        "bleed": 0.65,
        "rotation": 1.5,
        "vignette": 0.12,
        "jpeg": 75,
    },
    "xerox-velho": {
        "paper": 235,
        "texture": 7,
        "noise": 4.0,
        "bleed": 0.8,
        "rotation": 0.8,
        "vignette": 0.16,
        "jpeg": 65,
    },
    "limpo": {
        "paper": 250,
        "texture": 1,
        "noise": 0.7,
        "bleed": 0.2,
        "rotation": 0.0,
        "vignette": 0.0,
        "jpeg": None,
    },
}


def scanify(image: Any, seed: int, preset: str = "scanner-escritorio") -> Any:
    """Return a deterministic scan-like copy of *image*.

    ``image`` is a Pillow ``Image``.  A NumPy array is accepted when NumPy and
    Pillow are installed and is returned as an array with the same shape and
    dtype.  The input is never modified; no stage performs network I/O.
    """
    if preset not in _PRESETS:
        available = ", ".join(sorted(_PRESETS))
        raise ValueError(f"unknown preset {preset!r}; choose one of: {available}")
    if not isinstance(seed, int):
        raise TypeError("seed must be an integer")

    try:
        from PIL import Image, ImageChops, ImageEnhance, ImageFilter
    except ImportError as exc:
        raise RuntimeError("scanify requires Pillow; install it to process images") from exc

    numpy_input = False
    original_shape = None
    original_dtype = None
    if not isinstance(image, Image.Image):
        try:
            import numpy as np
        except ImportError as exc:
            raise TypeError("image must be a Pillow Image (or a NumPy array)") from exc
        array = np.asarray(image)
        if array.ndim not in (2, 3) or array.ndim == 3 and array.shape[2] not in (1, 3, 4):
            raise ValueError("NumPy image must have shape (height, width[, channels])")
        numpy_input = True
        original_shape, original_dtype = array.shape, array.dtype
        if array.ndim == 2 or array.shape[2] == 1:
            image = Image.fromarray(array.squeeze(), mode="L")
        else:
            image = Image.fromarray(array)

    original_mode = image.mode
    has_alpha = "A" in original_mode
    alpha = image.getchannel("A") if has_alpha else None
    working = image.convert("L")
    params = _PRESETS[preset]
    rng = random.Random(seed)

    # Ink density and bleed: preserve dark strokes while making their edges
    # slightly irregular.  A tiny deterministic blur is enough for this v1.
    if params["bleed"]:
        working = working.filter(ImageFilter.GaussianBlur(params["bleed"]))
    pixels = working.load()
    width, height = working.size
    density = params["noise"] / 18.0
    for y in range(height):
        for x in range(width):
            value = pixels[x, y]
            if value < 245:
                variation = 1.0 + rng.uniform(-density, density)
                pixels[x, y] = max(0, min(255, int(255 - (255 - value) * variation)))

    # Paper texture, lighting and tone curve.  The baseline is deliberately
    # off-white, including for a completely white input.
    paper = Image.new("L", (width, height), params["paper"])
    paper_pixels = paper.load()
    for y in range(height):
        for x in range(width):
            edge = min(x, y, width - 1 - x, height - 1 - y) / max(1, min(width, height) / 2)
            light = -params["vignette"] * 32 * (1 - min(1.0, edge))
            paper_value = params["paper"] + light + rng.gauss(0, params["texture"])
            paper_pixels[x, y] = max(0, min(255, int(paper_value)))

    result = ImageChops.multiply(paper, working)
    # Multiply above makes white ink-background equal the paper and keeps ink.
    result = ImageEnhance.Contrast(result).enhance(1.0 + (0.08 if preset == "xerox-velho" else 0.0))
    if params["noise"]:
        result_pixels = result.load()
        for y in range(height):
            for x in range(width):
                noisy_value = result_pixels[x, y] + rng.gauss(0, params["noise"] / 2)
                result_pixels[x, y] = max(0, min(255, int(noisy_value)))

    if params["rotation"]:
        angle = rng.uniform(-params["rotation"], params["rotation"])
        result = result.rotate(
            angle,
            resample=Image.Resampling.BICUBIC,
            expand=False,
            fillcolor=params["paper"],
        )

    if params["jpeg"]:
        encoded = BytesIO()
        result.save(encoded, format="JPEG", quality=params["jpeg"], subsampling=2)
        encoded.seek(0)
        result = Image.open(encoded).copy()

    if original_mode == "1":
        result = result.convert("1")
    elif original_mode in ("RGB", "RGBA"):
        result = result.convert("RGB")
    elif original_mode not in ("L", "LA"):
        result = result.convert(original_mode)
    if has_alpha and alpha is not None:
        result.putalpha(alpha)

    if numpy_input:
        output = np.asarray(result)
        if len(original_shape) == 3 and original_shape[2] == 1:
            output = output[..., None]
        return output.astype(original_dtype, copy=False)
    return result


__all__ = ["scanify"]
