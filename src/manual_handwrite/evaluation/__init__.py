"""Dependency-free evaluation of transcription content."""

from .metrics import (
    character_error_rate,
    critical_token_accuracy,
    edit_distance,
    normalized_character_error_rate,
)
from .report import EvaluationReport, evaluate_content

__all__ = [
    "EvaluationReport",
    "character_error_rate",
    "critical_token_accuracy",
    "edit_distance",
    "evaluate_content",
    "normalized_character_error_rate",
]
