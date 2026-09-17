"""Offline data-factory contracts for handwriting samples.

This module only represents and persists local annotations.  It deliberately
contains no image processing, transcription service, or network integration.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ConfidenceTier(StrEnum):
    """Quality bucket used to decide whether a sample may enter the dataset."""

    GOLD = "gold"
    SILVER = "silver"
    QUARANTINE = "quarantine"

    @classmethod
    def from_score(cls, score: float) -> ConfidenceTier:
        """Classify a score in ``[0, 1]`` using fixed, conservative cutoffs."""
        if not 0 <= score <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if score >= 0.90:
            return cls.GOLD
        if score >= 0.60:
            return cls.SILVER
        return cls.QUARANTINE

    @property
    def is_eligible(self) -> bool:
        return self is not self.QUARANTINE


@dataclass(frozen=True)
class PageMetadata:
    """Stable metadata identifying the local page from which regions came."""

    page_id: str
    source_path: str
    width: int
    height: int
    dpi: int | None = None
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.page_id or not self.source_path:
            raise ValueError("page_id and source_path are required")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("page dimensions must be positive")
        if self.dpi is not None and self.dpi <= 0:
            raise ValueError("dpi must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_id": self.page_id,
            "source_path": self.source_path,
            "width": self.width,
            "height": self.height,
            "dpi": self.dpi,
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PageMetadata:
        try:
            return cls(
                page_id=str(data["page_id"]),
                source_path=str(data["source_path"]),
                width=int(data["width"]),
                height=int(data["height"]),
                dpi=None if data.get("dpi") is None else int(data["dpi"]),
                provenance=dict(data.get("provenance", {})),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid page metadata") from exc


@dataclass(frozen=True)
class LineRegion:
    """Axis-aligned line crop in page pixel coordinates."""

    x: int
    y: int
    width: int
    height: int
    line_index: int

    def __post_init__(self) -> None:
        if self.x < 0 or self.y < 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("line region must be positive and within non-negative coordinates")
        if self.line_index < 0:
            raise ValueError("line_index must be non-negative")

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    def to_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "line_index": self.line_index,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LineRegion:
        try:
            return cls(*(int(data[key]) for key in ("x", "y", "width", "height", "line_index")))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid line region") from exc


@dataclass(frozen=True)
class ManifestEntry:
    """One locally annotated line and its auditable provenance."""

    sample_id: str
    page: PageMetadata
    region: LineRegion
    text: str | None
    confidence: float
    provenance: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.sample_id:
            raise ValueError("sample_id is required")
        if not self.provenance:
            raise ValueError("provenance is required")
        ConfidenceTier.from_score(self.confidence)

    @property
    def tier(self) -> ConfidenceTier:
        return ConfidenceTier.from_score(self.confidence)

    @property
    def is_eligible(self) -> bool:
        return self.tier.is_eligible

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "page": self.page.to_dict(),
            "region": self.region.to_dict(),
            "text": self.text,
            "confidence": self.confidence,
            "tier": self.tier.value,
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ManifestEntry:
        try:
            entry = cls(
                sample_id=str(data["sample_id"]),
                page=PageMetadata.from_dict(data["page"]),
                region=LineRegion.from_dict(data["region"]),
                text=data.get("text"),
                confidence=float(data["confidence"]),
                provenance=dict(data["provenance"]),
            )
            if data.get("tier") not in (None, entry.tier.value):
                raise ValueError("tier does not match confidence")
            return entry
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid manifest record") from exc


def eligible_entries(entries: Iterable[ManifestEntry]) -> Iterator[ManifestEntry]:
    """Yield only gold and silver entries, never quarantine data."""
    return (entry for entry in entries if entry.is_eligible)


def write_manifest(
    path: str | Path,
    entries: Iterable[ManifestEntry],
    *,
    include_quarantine: bool = False,
) -> int:
    """Write UTF-8 JSONL and return the number of records written.

    Quarantine is excluded by default so uncertain annotations cannot silently
    become training data.  Set ``include_quarantine`` only for an audit dump.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for entry in entries:
            if not include_quarantine and not entry.is_eligible:
                continue
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False, allow_nan=False))
            handle.write("\n")
            count += 1
    return count


def read_manifest(
    path: str | Path,
    *,
    include_quarantine: bool = False,
) -> list[ManifestEntry]:
    """Read JSONL records, optionally filtering quarantine entries."""
    records: list[ManifestEntry] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                entry = ManifestEntry.from_dict(json.loads(line))
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"invalid manifest record on line {line_number}") from exc
            if include_quarantine or entry.is_eligible:
                records.append(entry)
    return records


__all__ = [
    "ConfidenceTier",
    "LineRegion",
    "ManifestEntry",
    "PageMetadata",
    "eligible_entries",
    "read_manifest",
    "write_manifest",
]
