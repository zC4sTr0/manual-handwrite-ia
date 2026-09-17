import json

import pytest

from manual_handwrite.data import (
    ConfidenceTier,
    LineRegion,
    ManifestEntry,
    PageMetadata,
    read_manifest,
    write_manifest,
)


def test_page_metadata_and_line_region_round_trip_preserve_provenance():
    page = PageMetadata(
        page_id="page-001",
        source_path="samples/page-001.png",
        width=2400,
        height=3300,
        dpi=300,
        provenance={"capture": "synthetic-fixture", "operator": "owner"},
    )
    region = LineRegion(x=100, y=200, width=1800, height=120, line_index=3)

    assert PageMetadata.from_dict(page.to_dict()) == page
    assert LineRegion.from_dict(region.to_dict()) == region
    assert region.right == 1900
    assert region.bottom == 320


def test_confidence_tier_classifies_scores_and_quarantine_is_ineligible():
    assert ConfidenceTier.from_score(0.95) is ConfidenceTier.GOLD
    assert ConfidenceTier.from_score(0.75) is ConfidenceTier.SILVER
    assert ConfidenceTier.from_score(0.20) is ConfidenceTier.QUARANTINE
    assert ConfidenceTier.GOLD.is_eligible
    assert ConfidenceTier.SILVER.is_eligible
    assert not ConfidenceTier.QUARANTINE.is_eligible

    with pytest.raises(ValueError):
        ConfidenceTier.from_score(1.1)


def test_manifest_writes_jsonl_and_excludes_quarantine_without_losing_provenance(tmp_path):
    page = PageMetadata("p1", "samples/p1.png", 1000, 1400, 300)
    entries = [
        ManifestEntry(
            sample_id="p1-line-0",
            page=page,
            region=LineRegion(10, 20, 500, 50, 0),
            text="Olá",
            confidence=0.96,
            provenance={"method": "owner-transcribed", "source": "not-network"},
        ),
        ManifestEntry(
            sample_id="p1-line-1",
            page=page,
            region=LineRegion(10, 80, 500, 50, 1),
            text="incerto",
            confidence=0.2,
            provenance={"method": "manual-review-pending"},
        ),
    ]
    manifest = tmp_path / "index.jsonl"

    written = write_manifest(manifest, entries)
    assert written == 1
    assert len(manifest.read_text(encoding="utf-8").splitlines()) == 1

    records = read_manifest(manifest)
    assert [entry.sample_id for entry in records] == ["p1-line-0"]
    assert records[0].provenance == entries[0].provenance
    assert records[0].page.source_path == "samples/p1.png"
    assert records[0].region.line_index == 0


def test_manifest_can_read_quarantine_explicitly_and_rejects_malformed_records(tmp_path):
    path = tmp_path / "index.jsonl"
    path.write_text(
        json.dumps(
            ManifestEntry(
                "q",
                PageMetadata("p", "p.png", 1, 1, None),
                LineRegion(0, 0, 1, 1, 0),
                None,
                0.1,
                {"method": "manual-review-pending"},
            ).to_dict(),
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    assert len(read_manifest(path, include_quarantine=True)) == 1
    path.write_text('{"sample_id": "broken"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid manifest record"):
        read_manifest(path)
