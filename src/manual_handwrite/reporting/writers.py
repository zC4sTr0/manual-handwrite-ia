"""Writers for reports; all values come from supplied domain objects."""

from __future__ import annotations

import html
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from manual_handwrite.coverage import CoverageReport
from manual_handwrite.data import ManifestEntry


def _write_text(path: str | Path, content: str) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8", newline="\n")


def _provenance(value: Mapping[str, str] | None) -> dict[str, str]:
    return {} if value is None else dict(value)


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2) + "\n"


def _table(
    title: str,
    rows: Iterable[tuple[str, object]],
    headers: tuple[str, str] = ("Value", "Count"),
) -> str:
    body = "".join(
        f"<tr><td>{html.escape(str(label))}</td><td>{html.escape(str(value))}</td></tr>"
        for label, value in rows
    )
    return (
        f"<h2>{html.escape(title)}</h2><table><tr><th>{html.escape(headers[0])}</th>"
        f"<th>{html.escape(headers[1])}</th></tr>{body}</table>"
    )


def _histogram(title: str, values: Mapping[str, int]) -> str:
    ordered = sorted(values.items(), key=lambda pair: (-pair[1], pair[0]))
    maximum = max((count for _, count in ordered), default=0)
    rows = []
    for label, count in ordered:
        width = 0 if maximum == 0 else round(count * 100 / maximum)
        rows.append(
            '<div class="bar-row"><span class="bar-label">'
            f'{html.escape(label)}</span><span class="bar" style="width:{width}%"></span>'
            f"<span>{count}</span></div>"
        )
    return f'<h2>{html.escape(title)}</h2><div class="histogram">{"".join(rows)}</div>'


def _document(title: str, provenance: Mapping[str, str], sections: Iterable[str]) -> str:
    provenance_rows = "".join(
        f"<tr><td>{html.escape(key)}</td><td>{html.escape(value)}</td></tr>"
        for key, value in sorted(provenance.items())
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title><style>"
        "body{font:14px system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%;margin-bottom:1.5rem}"
        "th,td{border:1px solid #ccc;padding:.35rem;text-align:left}"
        ".bar-row{display:flex;gap:.5rem;align-items:center;margin:.2rem 0}"
        ".bar-label{width:10rem;overflow-wrap:anywhere}.bar{height:1rem;background:#5680e9;min-width:1px}"
        "</style></head><body>"
        f"<h1>{html.escape(title)}</h1><h2>Provenance</h2>"
        f"<table><tr><th>Field</th><th>Value</th></tr>{provenance_rows}</table>"
        f"{''.join(sections)}</body></html>"
    )


def write_coverage_report_json(
    path: str | Path,
    report: CoverageReport,
    *,
    provenance: Mapping[str, str] | None = None,
) -> None:
    """Write exact coverage counters, missing sets, and caller-supplied provenance."""
    _write_text(path, _json({"provenance": _provenance(provenance), "coverage": report.as_dict()}))


def write_coverage_report_html(
    path: str | Path,
    report: CoverageReport,
    *,
    provenance: Mapping[str, str] | None = None,
) -> None:
    """Write a self-contained coverage page with evidence histograms and missing tables."""
    sections = [
        _histogram("Character Histogram", report.characters),
        _histogram("Token Histogram", report.tokens),
        _histogram("Operator Histogram", report.operators),
        _table("Missing tokens", ((item, "missing") for item in report.missing_tokens)),
        _table("Missing operators", ((item, "missing") for item in report.missing_operators)),
    ]
    _write_text(path, _document("Coverage report", _provenance(provenance), sections))


def _confidence_data(
    entries: Iterable[ManifestEntry], provenance: Mapping[str, str] | None
) -> dict[str, Any]:
    records = list(entries)
    counts = {tier: 0 for tier in ("gold", "silver", "quarantine")}
    for entry in records:
        counts[entry.tier.value] += 1
    return {
        "provenance": _provenance(provenance),
        "summary": {"count": len(records), **counts},
        "scores": sorted(entry.confidence for entry in records),
        "entries": [entry.to_dict() for entry in records],
    }


def write_confidence_report_json(
    path: str | Path,
    entries: Iterable[ManifestEntry],
    *,
    provenance: Mapping[str, str] | None = None,
) -> None:
    """Write confidence scores and every manifest record without filtering data."""
    _write_text(path, _json(_confidence_data(entries, provenance)))


def write_confidence_report_html(
    path: str | Path,
    entries: Iterable[ManifestEntry],
    *,
    provenance: Mapping[str, str] | None = None,
) -> None:
    """Write a self-contained confidence histogram and manifest evidence table."""
    records = list(entries)
    histogram = {f"{index / 10:.1f}-{(index + 1) / 10:.1f}": 0 for index in range(10)}
    for entry in records:
        index = min(int(entry.confidence * 10), 9)
        key = f"{index / 10:.1f}-{(index + 1) / 10:.1f}"
        histogram[key] += 1
    rows = ((entry.sample_id, f"{entry.confidence:.6g} ({entry.tier.value})") for entry in records)
    sections = [
        _histogram("Histogram", histogram),
        _table("Manifest entries", rows, ("Sample ID", "Confidence")),
    ]
    _write_text(path, _document("Dataset confidence report", _provenance(provenance), sections))
