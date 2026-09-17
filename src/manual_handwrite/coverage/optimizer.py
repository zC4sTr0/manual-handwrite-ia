"""Greedy maximum-coverage selection for active handwritten capture."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .analyzer import CORE_OPERATORS, CORE_TOKENS, CoverageReport, analyze_text


@dataclass(frozen=True)
class CoverageSelection:
    """Auditable result of selecting candidate snippets."""

    selected_snippets: tuple[str, ...]
    remaining_missing_tokens: tuple[str, ...]
    remaining_missing_operators: tuple[str, ...]
    selected_reports: tuple[CoverageReport, ...] = ()

    @property
    def selected_count(self) -> int:
        return len(self.selected_snippets)

    @property
    def missing_tokens(self) -> tuple[str, ...]:
        return self.remaining_missing_tokens

    @property
    def missing_operators(self) -> tuple[str, ...]:
        return self.remaining_missing_operators

    def as_dict(self) -> dict[str, object]:
        return {
            "selected_snippets": list(self.selected_snippets),
            "remaining_missing_tokens": list(self.remaining_missing_tokens),
            "remaining_missing_operators": list(self.remaining_missing_operators),
        }


# A shorter name is useful to callers that do not need to distinguish this
# result from the analyzer's CoverageReport.
OptimizationResult = CoverageSelection


def _coverage(report: CoverageReport) -> set[str]:
    """Return only vocabulary observed by ``analyze_text``."""
    return (set(report.tokens) & CORE_TOKENS) | (set(report.operators) & CORE_OPERATORS)


def optimize_coverage(
    candidates: Iterable[str],
    max_snippets: int,
    *,
    existing_text: str = "",
    max_cost: int | float | None = None,
) -> CoverageSelection:
    """Select snippets greedily by newly covered symbols per character.

    Candidate coverage is obtained exclusively from :func:`analyze_text`.
    ``existing_text`` is analyzed as the already captured corpus.  A snippet's
    default cost is its text length; an empty snippet costs one unit so it
    cannot win by division-by-zero.  Selection is deterministic: ties retain
    input order, and candidates with no new coverage are omitted.
    """
    if max_snippets < 0:
        raise ValueError("max_snippets must be non-negative")
    if max_cost is not None and max_cost < 0:
        raise ValueError("max_cost must be non-negative")

    baseline = analyze_text(existing_text)
    covered = _coverage(baseline)
    target = CORE_TOKENS | CORE_OPERATORS
    remaining = set(target - covered)
    prepared = [(text, analyze_text(text)) for text in candidates]
    selected: list[str] = []
    selected_reports: list[CoverageReport] = []
    spent = 0

    while len(selected) < max_snippets and remaining:
        best: tuple[float, int, str, CoverageReport, set[str]] | None = None
        for index, (text, report) in enumerate(prepared):
            if text in selected:
                continue
            cost = max(1, len(text))
            if max_cost is not None and spent + cost > max_cost:
                continue
            gain_set = _coverage(report) & remaining
            if not gain_set:
                continue
            score = len(gain_set) / cost
            choice = (score, -index, text, report, gain_set)
            if best is None or choice[:2] > best[:2]:
                best = choice

        if best is None:
            break
        _, _, text, report, gain_set = best
        selected.append(text)
        selected_reports.append(report)
        spent += max(1, len(text))
        covered.update(gain_set)
        remaining.difference_update(gain_set)

    missing_tokens = tuple(sorted(CORE_TOKENS - covered))
    missing_operators = tuple(sorted(CORE_OPERATORS - covered))
    return CoverageSelection(
        selected_snippets=tuple(selected),
        remaining_missing_tokens=missing_tokens,
        remaining_missing_operators=missing_operators,
        selected_reports=tuple(selected_reports),
    )


# Explicit alias for callers using the algorithm's conventional name.
greedy_select = optimize_coverage

__all__ = ["CoverageSelection", "OptimizationResult", "greedy_select", "optimize_coverage"]
