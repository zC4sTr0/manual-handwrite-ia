import json

from manual_handwrite.coverage import analyze_text
from manual_handwrite.data import LineRegion, ManifestEntry, PageMetadata
from manual_handwrite.reporting import (
    write_confidence_report_html,
    write_confidence_report_json,
    write_coverage_report_html,
    write_coverage_report_json,
)


def _entries():
    page = PageMetadata("p1", "samples/p1.png", 1000, 1400, 300)
    return [
        ManifestEntry("gold", page, LineRegion(0, 0, 10, 10, 0), "A", 0.95, {"method": "owner"}),
        ManifestEntry("silver", page, LineRegion(0, 0, 10, 10, 1), "B", 0.65, {"method": "review"}),
        ManifestEntry(
            "quarantine", page, LineRegion(0, 0, 10, 10, 2), None, 0.2, {"method": "pending"}
        ),
    ]


def test_coverage_json_contains_actual_counts_and_provenance(tmp_path):
    report = analyze_text("def f(x):\n    return x >= 2\n")
    path = tmp_path / "coverage.json"

    write_coverage_report_json(path, report, provenance={"source": "fixture", "run": "r1"})

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["provenance"] == {"source": "fixture", "run": "r1"}
    assert data["coverage"]["tokens"]["def"] == 1
    assert data["coverage"]["operators"][">="] == 1
    assert data["coverage"]["missing_tokens"] == list(report.missing_tokens)


def test_coverage_html_is_self_contained_and_has_histogram_and_missing_table(tmp_path):
    report = analyze_text("return x >= 2")
    path = tmp_path / "coverage.html"

    write_coverage_report_html(path, report, provenance={"source": "fixture"})

    html = path.read_text(encoding="utf-8")
    assert "<html" in html and "<style>" in html
    assert "Histogram" in html
    assert "Missing tokens" in html
    assert "fixture" in html
    assert "https://" not in html


def test_confidence_reports_use_manifest_values_and_show_tiers(tmp_path):
    entries = _entries()
    json_path = tmp_path / "confidence.json"
    html_path = tmp_path / "confidence.html"

    write_confidence_report_json(json_path, entries, provenance={"source": "manifest"})
    write_confidence_report_html(html_path, entries, provenance={"source": "manifest"})

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["provenance"] == {"source": "manifest"}
    assert data["summary"] == {"count": 3, "gold": 1, "silver": 1, "quarantine": 1}
    assert data["scores"] == [0.2, 0.65, 0.95]
    html = html_path.read_text(encoding="utf-8")
    assert "gold" in html and "silver" in html and "quarantine" in html
    assert "Histogram" in html and "Sample ID" in html
    assert "gold" in html and "0.95" in html
