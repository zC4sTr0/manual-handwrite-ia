"""Deterministic ingestion for owner-consented image/source.py pairs.

This module creates annotations only from caller-supplied regions and text.  It
never performs OCR, calls a model, or stores image/source contents in logs.
"""

from __future__ import annotations

import ast
import hashlib
import tokenize
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from . import LineRegion, ManifestEntry, PageMetadata


class SourcePairError(ValueError):
    """Raised when an image/source pair fails the ingestion contract."""


_SIGNATURE_KEYS = frozenset(
    {"signature", "is_signature", "signature_marked", "is_signature_marked"}
)


def ingest_source_pair(
    image_path: str | Path,
    source_path: str | Path,
    line_regions: Sequence[LineRegion | Mapping[str, Any] | Sequence[int]],
    texts: Sequence[str | None],
    *,
    owner_consent: bool,
    page_id: str | None = None,
    dpi: int | None = None,
    metadata: Mapping[str, Any] | None = None,
    provenance: Mapping[str, str] | None = None,
) -> tuple[ManifestEntry, ...]:
    """Build exact GOLD entries for supplied line regions and text.

    ``source_path`` is checked as Python and hashed byte-for-byte.  The image
    is opened only to obtain dimensions and is never copied.  The two input
    sequences are deliberately caller-supplied: segmentation and transcription
    are outside this primitive.
    """
    if owner_consent is not True:
        raise SourcePairError("owner_consent must be true")
    if metadata is not None and not isinstance(metadata, Mapping):
        raise SourcePairError("metadata must be an object")
    if _contains_signature_marker(metadata):
        raise SourcePairError("signature-marked metadata is not accepted")
    if provenance is not None and not isinstance(provenance, Mapping):
        raise SourcePairError("provenance must be an object")
    if len(line_regions) != len(texts):
        raise SourcePairError("line_regions and texts must have the same number of items")

    image = Path(image_path)
    source = Path(source_path)
    try:
        with Image.open(image) as opened_image:
            width, height = opened_image.size
    except (OSError, UnidentifiedImageError) as exc:
        raise SourcePairError("could not read page image") from exc

    try:
        source_bytes = source.read_bytes()
    except (OSError, UnicodeError) as exc:
        raise SourcePairError("could not read source.py") from exc
    _validate_python_source(source, source_bytes)
    source_hash = hashlib.sha256(source_bytes).hexdigest()

    normalized_regions = tuple(
        _coerce_region(region, index) for index, region in enumerate(line_regions)
    )
    for region in normalized_regions:
        if region.right > width or region.bottom > height:
            raise SourcePairError("line region must be within image bounds")
    for text in texts:
        if text is not None and not isinstance(text, str):
            raise SourcePairError("text must be a string or None")

    resolved_page_id = page_id or image.stem
    if not isinstance(resolved_page_id, str) or not resolved_page_id:
        raise SourcePairError("page_id must be a non-empty string")
    base_provenance = {
        "method": "source-pair-gold",
        "source_path": str(source),
        "source_sha256": source_hash,
        "owner_consent": "true",
    }
    if provenance:
        base_provenance.update({str(key): str(value) for key, value in provenance.items()})
    page = PageMetadata(
        page_id=resolved_page_id,
        source_path=str(image),
        width=width,
        height=height,
        dpi=dpi,
        provenance=base_provenance,
    )
    return tuple(
        ManifestEntry(
            sample_id=f"{resolved_page_id}-line-{region.line_index}",
            page=page,
            region=region,
            text=text,
            confidence=1.0,
            provenance=dict(base_provenance),
        )
        for region, text in zip(normalized_regions, texts, strict=True)
    )


def _validate_python_source(path: Path, source_bytes: bytes) -> None:
    try:
        encoding, _ = tokenize.detect_encoding(
            iter(source_bytes.splitlines(keepends=True)).__next__
        )
        ast.parse(source_bytes.decode(encoding), filename=str(path))
    except (SyntaxError, UnicodeDecodeError, LookupError, StopIteration) as exc:
        raise SourcePairError("source.py must contain valid Python syntax") from exc


def _coerce_region(value: LineRegion | Mapping[str, Any] | Sequence[int], index: int) -> LineRegion:
    try:
        if isinstance(value, LineRegion):
            region = value
        elif isinstance(value, Mapping):
            region = LineRegion.from_dict(value)
        else:
            if len(value) == 4:
                region = LineRegion(*map(int, value), line_index=index)
            elif len(value) == 5:
                region = LineRegion(*map(int, value))
            else:
                raise ValueError
    except (TypeError, ValueError, KeyError) as exc:
        raise SourcePairError("invalid line region") from exc
    return region


def _contains_signature_marker(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            key in _SIGNATURE_KEYS and marker is True for key, marker in value.items()
        ) or any(_contains_signature_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_signature_marker(item) for item in value)
    return False


__all__ = ["SourcePairError", "ingest_source_pair"]
