"""Safe contracts for handwriting generation backends.

This package deliberately contains no renderer.  A backend must provide a real
handwriting implementation; callers must not silently receive system-font text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from manual_handwrite.style import StylePack


@dataclass(frozen=True)
class BackendCapabilities:
    """Machine-readable claims made by a generation backend."""

    name: str
    version: str
    available: bool
    supports_seed: bool
    supports_count: bool
    supports_stylepack: bool
    renders_handwriting: bool
    requires_network: bool
    requires_neural: bool


@dataclass(frozen=True)
class Candidate:
    """Minimal candidate identity and provenance contract.

    Rendered pixels are intentionally not part of this v1 contract.  A future
    backend may attach a raster artifact through its own documented boundary;
    this object cannot be mistaken for rendered handwriting.
    """

    text: str
    seed: int
    index: int
    backend: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("candidate text must be a string")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("candidate seed must be an integer")
        if not isinstance(self.index, int) or isinstance(self.index, bool) or self.index < 0:
            raise ValueError("candidate index must be a non-negative integer")
        if not isinstance(self.backend, str) or not self.backend:
            raise ValueError("candidate backend must be a non-empty string")


class BackendUnavailableError(RuntimeError):
    """Raised when no real handwriting generation backend is installed."""


@runtime_checkable
class HandwritingBackend(Protocol):
    """Backend boundary for deterministic, owner-style-conditioned generation."""

    @property
    def capabilities(self) -> BackendCapabilities: ...

    def generate(
        self,
        text: str,
        stylepack: StylePack,
        *,
        seed: int,
        count: int,
    ) -> tuple[Candidate, ...]: ...


class UnavailableBackend:
    """Explicit v1 fallback when no genuine handwriting renderer is available."""

    capabilities = BackendCapabilities(
        name="unavailable",
        version="0",
        available=False,
        supports_seed=True,
        supports_count=True,
        supports_stylepack=True,
        renders_handwriting=False,
        requires_network=False,
        requires_neural=False,
    )

    def generate(
        self,
        text: str,
        stylepack: StylePack,
        *,
        seed: int,
        count: int,
    ) -> tuple[Candidate, ...]:
        validate_generation_request(text, stylepack, seed=seed, count=count)
        raise BackendUnavailableError(
            "handwriting generation backend is unavailable; no text was rendered"
        )


def validate_generation_request(
    text: object,
    stylepack: object,
    *,
    seed: object,
    count: object,
) -> None:
    """Validate the backend request without coercing caller-controlled values."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(stylepack, StylePack):
        raise TypeError("stylepack must be a StylePack")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")
    if not isinstance(count, int) or isinstance(count, bool):
        raise TypeError("count must be an integer")
    if count <= 0:
        raise ValueError("count must be a positive integer")


# Descriptive alias for callers that prefer the full name.
UnavailableHandwritingBackend = UnavailableBackend


__all__ = [
    "BackendCapabilities",
    "BackendUnavailableError",
    "Candidate",
    "HandwritingBackend",
    "UnavailableBackend",
    "UnavailableHandwritingBackend",
    "validate_generation_request",
]
