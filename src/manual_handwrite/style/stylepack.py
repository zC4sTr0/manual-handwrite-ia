"""Consent and provenance metadata for local handwriting style references."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import PurePath, PureWindowsPath
from typing import Any


class StylePackError(ValueError):
    """Raised when a StylePack manifest is unsafe or malformed."""


@dataclass(frozen=True)
class StyleReference:
    """A relative reference and its caller-supplied provenance only."""

    path: str
    provenance: dict[str, Any]

    def __post_init__(self) -> None:
        _validate_relative_reference(self.path)
        if not isinstance(self.provenance, dict):
            raise StylePackError("reference provenance must be an object")
        object.__setattr__(self, "provenance", dict(self.provenance))

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "provenance": dict(self.provenance)}


@dataclass(frozen=True)
class StylePack:
    """Metadata needed to identify an owner-consented local style pack.

    This object deliberately contains paths and metadata, never image bytes or
    image objects.  Consumers are responsible for any later local access.
    """

    references: tuple[StyleReference, ...]
    dataset_id: str
    dataset_hash: str
    coverage: dict[str, Any]
    scan_preset: str
    owner_consent: bool
    version: str

    def __post_init__(self) -> None:
        if self.owner_consent is not True:
            raise StylePackError("owner_consent must be true")
        if not isinstance(self.references, tuple):
            object.__setattr__(self, "references", tuple(self.references))
        if not self.references:
            raise StylePackError("references must not be empty")
        if not isinstance(self.dataset_id, str) or not self.dataset_id:
            raise StylePackError("dataset id must be a non-empty string")
        if not isinstance(self.dataset_hash, str) or not self.dataset_hash:
            raise StylePackError("dataset hash must be a non-empty string")
        if not isinstance(self.coverage, dict):
            raise StylePackError("coverage must be an object")
        if not isinstance(self.scan_preset, str) or not self.scan_preset:
            raise StylePackError("scan_preset must be a non-empty string")
        if not isinstance(self.version, str) or not self.version:
            raise StylePackError("version must be a non-empty string")
        object.__setattr__(self, "coverage", dict(self.coverage))

    def to_dict(self) -> dict[str, Any]:
        """Return the stable JSON manifest shape without reading references."""
        return {
            "version": self.version,
            "owner_consent": True,
            "references": [reference.to_dict() for reference in self.references],
            "dataset": {"id": self.dataset_id, "hash": self.dataset_hash},
            "coverage": dict(self.coverage),
            "scan_preset": self.scan_preset,
        }

    @classmethod
    def from_dict(cls, payload: object) -> StylePack:
        """Validate and construct a pack from decoded JSON metadata."""
        if not isinstance(payload, dict):
            raise StylePackError("StylePack manifest must be a JSON object")
        if _has_signature_marker(payload):
            raise StylePackError("signature-marked styles are not accepted")
        if payload.get("owner_consent") is not True:
            raise StylePackError("owner_consent must be true")

        references_data = payload.get("references")
        if not isinstance(references_data, list):
            raise StylePackError("references must be an array")
        references = []
        for item in references_data:
            if not isinstance(item, dict):
                raise StylePackError("each reference must be an object")
            if _has_signature_marker(item):
                raise StylePackError("signature-marked styles are not accepted")
            references.append(StyleReference(item.get("path"), item.get("provenance", {})))

        dataset = payload.get("dataset")
        if not isinstance(dataset, dict):
            raise StylePackError("dataset must be an object")
        return cls(
            references=tuple(references),
            dataset_id=dataset.get("id"),
            dataset_hash=dataset.get("hash"),
            coverage=payload.get("coverage"),
            scan_preset=payload.get("scan_preset"),
            owner_consent=payload.get("owner_consent"),
            version=payload.get("version"),
        )


def load_stylepack(path: os.PathLike[str] | str) -> StylePack:
    """Load and validate JSON metadata; only the manifest file is opened."""
    try:
        with open(path, encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StylePackError(f"could not load StylePack manifest: {exc}") from exc
    return StylePack.from_dict(payload)


def write_stylepack(path: os.PathLike[str] | str, pack: StylePack) -> None:
    """Write metadata JSON, without inspecting or copying referenced files."""
    if not isinstance(pack, StylePack):
        raise TypeError("pack must be a StylePack")
    destination = os.fspath(path)
    parent = os.path.dirname(destination)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(destination, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(pack.to_dict(), stream, ensure_ascii=False, indent=2)
        stream.write("\n")


# Explicit manifest names make the file-format boundary discoverable.
load_stylepack_manifest = load_stylepack
write_stylepack_manifest = write_stylepack
load_manifest = load_stylepack
write_manifest = write_stylepack


def _validate_relative_reference(path: object) -> None:
    if not isinstance(path, str) or not path:
        raise StylePackError("reference path must be relative")
    windows_path = PureWindowsPath(path)
    if PurePath(path).is_absolute() or windows_path.is_absolute() or windows_path.drive:
        raise StylePackError("reference path must be relative")
    if any(part == ".." for part in path.replace("\\", "/").split("/")):
        raise StylePackError("reference path must stay relative")


def _has_signature_marker(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    markers = {"signature", "is_signature", "signature_marked", "is_signature_marked"}
    return any(key in markers and value[key] is True for key in value)


__all__ = [
    "StylePack",
    "StylePackError",
    "StyleReference",
    "load_stylepack",
    "load_stylepack_manifest",
    "load_manifest",
    "write_stylepack",
    "write_stylepack_manifest",
    "write_manifest",
]
