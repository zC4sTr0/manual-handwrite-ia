"""Conservative glyph evidence extraction from an aligned handwritten line.

This module deliberately does not infer missing glyphs.  It only returns a crop
when the supplied transcription and a simple image segmentation agree exactly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import numpy as np
from PIL import Image

# Characters that commonly have syntactic meaning in Python source.
CRITICAL_GLYPHS = frozenset("()[]{}:,.=+-*/%_<>!&|^~;#'\\\"@")
BBox: TypeAlias = tuple[int, int, int, int]


@dataclass(frozen=True)
class GlyphProvenance:
    """Location and source facts retained with an extracted crop."""

    source_text: str
    character_index: int
    bbox: BBox
    segmentation: str = "vertical_projection"


@dataclass(frozen=True)
class GlyphCandidate:
    """A pixel crop that is safe to associate with one transcription character."""

    symbol: str
    image: np.ndarray
    bbox: BBox
    provenance: GlyphProvenance


@dataclass(frozen=True)
class UnresolvedAlignment:
    """An alignment that was intentionally not guessed."""

    reason: str
    character_index: int | None = None


@dataclass(frozen=True)
class GlyphHarvest:
    """Diagnostic-only result of harvesting one aligned line."""

    candidates: tuple[GlyphCandidate, ...]
    unresolved: tuple[UnresolvedAlignment, ...]


def harvest_critical_glyphs(
    image: Image.Image | np.ndarray,
    transcription: str,
    *,
    threshold: int = 200,
) -> GlyphHarvest:
    """Harvest critical-symbol crops only when alignment is unambiguous.

    ``image`` is a grayscale or RGB line image with dark ink on a light
    background.  The vertical projection is split into contiguous ink runs;
    whitespace in the transcription is ignored for this one-line operation.
    If the number of runs differs from the number of non-whitespace characters,
    no crop is returned.  This conservative rule avoids assigning a component
    to the wrong symbol when cursive joins, dots, or touching marks occur.
    """
    if not isinstance(transcription, str):
        raise TypeError("transcription must be a string")
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be between 0 and 255")

    gray = _as_grayscale_array(image)
    ink = gray < threshold
    characters = [(index, char) for index, char in enumerate(transcription) if not char.isspace()]
    runs = _projection_runs(ink)

    if not runs:
        return GlyphHarvest((), (UnresolvedAlignment("blank_image"),))
    if len(runs) != len(characters):
        return GlyphHarvest((), (UnresolvedAlignment("component_count_mismatch"),))

    candidates: list[GlyphCandidate] = []
    for (x0, x1), (character_index, symbol) in zip(runs, characters, strict=True):
        if symbol not in CRITICAL_GLYPHS:
            continue
        ys, xs = np.nonzero(ink[:, x0:x1])
        if len(xs) == 0:
            return GlyphHarvest((), (UnresolvedAlignment("empty_component", character_index),))
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        actual_x0, actual_x1 = x0 + int(xs.min()), x0 + int(xs.max()) + 1
        bbox = (actual_x0, y0, actual_x1, y1)
        crop = np.array(gray[y0:y1, actual_x0:actual_x1], copy=True)
        provenance = GlyphProvenance(transcription, character_index, bbox)
        candidates.append(GlyphCandidate(symbol, crop, bbox, provenance))

    return GlyphHarvest(tuple(candidates), ())


def _as_grayscale_array(image: Image.Image | np.ndarray) -> np.ndarray:
    if isinstance(image, Image.Image):
        array = np.asarray(image.convert("L"))
    elif isinstance(image, np.ndarray):
        if image.ndim == 2:
            array = image
        elif image.ndim == 3 and image.shape[2] in (3, 4):
            array = np.asarray(Image.fromarray(image).convert("L"))
        else:
            raise ValueError("image must be a 2-D array or an RGB/RGBA array")
    else:
        raise TypeError("image must be a Pillow image or numpy array")
    if array.size == 0:
        raise ValueError("image must not be empty")
    if not np.issubdtype(array.dtype, np.number):
        raise TypeError("image array must contain numeric pixels")
    return np.asarray(array, dtype=np.uint8)


def _projection_runs(ink: np.ndarray) -> list[tuple[int, int]]:
    occupied = np.any(ink, axis=0)
    padded = np.concatenate(([False], occupied, [False]))
    starts = np.flatnonzero(~padded[:-1] & padded[1:])
    ends = np.flatnonzero(padded[:-1] & ~padded[1:])
    return [(int(start), int(end)) for start, end in zip(starts, ends, strict=True)]


# Short compatibility spelling for callers that use the generic verb.
harvest_glyphs = harvest_critical_glyphs
