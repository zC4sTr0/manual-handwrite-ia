"""Auditable report for code-content evaluation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .metrics import critical_token_accuracy, normalized_character_error_rate


@dataclass(frozen=True)
class EvaluationReport:
    """Content metrics plus raw inputs and their provenance.

    Style and visual-quality evaluation needs rendered pages or human raters;
    those metrics are explicitly listed as unavailable instead of being
    represented by fabricated values.
    """

    reference_text: str
    candidate_text: str
    metrics: Mapping[str, float | None]
    provenance: Mapping[str, str] = field(default_factory=dict)
    unavailable_metrics: tuple[str, ...] = ("style", "quality")

    def __post_init__(self) -> None:
        if not isinstance(self.reference_text, str):
            raise TypeError("reference_text must be a string")
        if not isinstance(self.candidate_text, str):
            raise TypeError("candidate_text must be a string")
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))
        object.__setattr__(self, "unavailable_metrics", tuple(self.unavailable_metrics))

    def as_dict(self) -> dict[str, object]:
        """Serialize without dropping raw disagreements or provenance."""
        return {
            "reference_text": self.reference_text,
            "candidate_text": self.candidate_text,
            "metrics": dict(self.metrics),
            "provenance": dict(self.provenance),
            "unavailable_metrics": list(self.unavailable_metrics),
        }


def evaluate_content(
    reference_text: str,
    candidate_text: str,
    *,
    provenance: Mapping[str, str] | None = None,
) -> EvaluationReport:
    """Evaluate code content while preserving both source strings verbatim."""
    return EvaluationReport(
        reference_text=reference_text,
        candidate_text=candidate_text,
        metrics={
            "character_error_rate": normalized_character_error_rate(reference_text, candidate_text),
            "critical_token_accuracy": critical_token_accuracy(reference_text, candidate_text),
        },
        provenance=provenance or {},
    )


__all__ = ["EvaluationReport", "evaluate_content"]
