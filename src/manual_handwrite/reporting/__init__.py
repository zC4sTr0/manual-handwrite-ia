"""Dependency-free, auditable reports for local coverage and confidence data."""

from .writers import (
    write_confidence_report_html,
    write_confidence_report_json,
    write_coverage_report_html,
    write_coverage_report_json,
)

__all__ = [
    "write_confidence_report_html",
    "write_confidence_report_json",
    "write_coverage_report_html",
    "write_coverage_report_json",
]
