"""Honest, offline transcription contracts.

This module intentionally does not inspect images or invoke OCR, a VLM, or a
network service.  The reference adapter only packages text supplied by the
caller, such as text paired with a local ``source.py`` example.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


class VerificationStatus(StrEnum):
    """What the adapter can honestly say about a transcription result."""

    SUPPLIED_TEXT = "supplied_text"


@dataclass(frozen=True)
class TranscriptionResult:
    """Candidates and audit data, never a claim of visual transcription.

    ``confidence`` describes certainty that the returned candidate equals the
    caller's supplied text.  It is not an OCR or handwriting-recognition score.
    """

    candidates: tuple[str, ...]
    provenance: Mapping[str, str]
    confidence: float
    verification_status: VerificationStatus

    def __post_init__(self) -> None:
        if not self.candidates:
            raise ValueError("result requires at least one candidate")
        if any(not isinstance(candidate, str) or not candidate for candidate in self.candidates):
            raise ValueError("candidates must contain non-empty text")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not isinstance(self.verification_status, VerificationStatus):
            raise ValueError("invalid verification status")


@runtime_checkable
class OfflineTranscriptionAdapter(Protocol):
    """Minimal adapter contract for deterministic, local transcription.

    Implementations must consume caller-supplied text only.  They must not read
    an image, call a VLM, perform fake OCR, or make a network request.
    """

    def transcribe(self, text: str, *, source: str = "pre-supplied") -> TranscriptionResult:
        """Return a result from supplied text; network and VLM are not called."""
        ...


class SuppliedTextTranscriber:
    """Reference adapter that packages pre-supplied text without interpreting it."""

    def transcribe(self, text: str, *, source: str = "pre-supplied") -> TranscriptionResult:
        """Package text exactly; no image, VLM, OCR, or network call is made."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("transcription requires non-empty pre-supplied text")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must be non-empty")
        return TranscriptionResult(
            candidates=(text,),
            provenance={
                "adapter": "supplied-text-reference",
                "source": source,
                "input": "pre-supplied-text",
                "visual_transcription": "not-performed",
                "network": "not-called",
            },
            confidence=1.0,
            verification_status=VerificationStatus.SUPPLIED_TEXT,
        )


__all__ = [
    "OfflineTranscriptionAdapter",
    "SuppliedTextTranscriber",
    "TranscriptionResult",
    "VerificationStatus",
]
