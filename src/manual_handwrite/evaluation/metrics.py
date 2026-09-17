"""Deterministic content metrics for supplied transcriptions.

The functions in this module intentionally treat both strings as literal text.
In particular, they do not apply Unicode normalization, whitespace cleanup, or
spell correction: an evaluator must expose disagreements rather than hide them.
"""

from __future__ import annotations

import io
import tokenize
from collections.abc import Iterable

from manual_handwrite.coverage.analyzer import CORE_TOKENS


def edit_distance(reference: str, candidate: str) -> int:
    """Return the Levenshtein distance between two literal character strings."""
    _require_text(reference, "reference")
    _require_text(candidate, "candidate")
    if len(reference) < len(candidate):
        reference, candidate = candidate, reference
    previous = list(range(len(candidate) + 1))
    for reference_char in reference:
        current = [previous[0] + 1]
        for index, candidate_char in enumerate(candidate, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[index] + 1,
                    previous[index - 1] + (reference_char != candidate_char),
                )
            )
        previous = current
    return previous[-1]


def normalized_character_error_rate(reference: str, candidate: str) -> float | None:
    """Return literal character edit distance divided by reference length.

    ``None`` means the metric has no denominator (an empty reference), rather
    than implying that an empty reference was correct.  Candidate text is never
    normalized or replaced.
    """
    _require_text(reference, "reference")
    _require_text(candidate, "candidate")
    if not reference:
        return None
    return edit_distance(reference, candidate) / len(reference)


# The shorter conventional name is useful to callers and keeps the public API
# discoverable without changing the explicit normalized name above.
character_error_rate = normalized_character_error_rate


def _python_tokens(text: str) -> list[str]:
    """Extract token spellings, retaining tokens emitted before a parse error."""
    _require_text(text, "text")
    result: list[str] = []
    try:
        stream = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in stream:
            if token.type in (tokenize.NAME, tokenize.NUMBER, tokenize.STRING, tokenize.OP):
                result.append(token.string)
    except (IndentationError, tokenize.TokenError):
        pass
    return result


def critical_token_accuracy(
    reference: str,
    candidate: str,
    *,
    critical_tokens: Iterable[str] = CORE_TOKENS,
) -> float | None:
    """Compare critical Python token spellings in source order.

    Accuracy is the proportion of exact tokens retained in sequence alignment over
    the longer critical-token sequence. Thus insertions and omissions are
    disagreements, not silently discarded.  By default the project's critical vocabulary is
    used; callers may provide a frozen snapshot or another explicit vocabulary.
    ``None`` indicates that neither text contains a critical token.
    """
    _require_text(reference, "reference")
    _require_text(candidate, "candidate")
    vocabulary = frozenset(critical_tokens)
    if any(not isinstance(token, str) for token in vocabulary):
        raise TypeError("critical_tokens must contain strings")
    expected = [token for token in _python_tokens(reference) if token in vocabulary]
    actual = [token for token in _python_tokens(candidate) if token in vocabulary]
    denominator = max(len(expected), len(actual))
    if not denominator:
        return None
    # Longest common subsequence aligns unchanged tokens around omissions and
    # insertions, while still treating every differing spelling as a miss.
    previous = [0] * (len(actual) + 1)
    for expected_token in expected:
        current = [0]
        for index, actual_token in enumerate(actual, 1):
            if expected_token == actual_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1] / denominator


def _require_text(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")


__all__ = [
    "character_error_rate",
    "critical_token_accuracy",
    "edit_distance",
    "normalized_character_error_rate",
]
