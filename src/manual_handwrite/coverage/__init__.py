"""Cobertura de símbolos e tokens para captura ativa."""

from .analyzer import CoverageReport, analyze_text
from .optimizer import CoverageSelection, optimize_coverage

__all__ = ["CoverageReport", "CoverageSelection", "analyze_text", "optimize_coverage"]
