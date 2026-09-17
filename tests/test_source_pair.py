import ast
import hashlib

import pytest
from PIL import Image

from manual_handwrite.data.source_pair import SourcePairError, ingest_source_pair


def _fixtures(tmp_path):
    image = tmp_path / "page.png"
    Image.new("L", (200, 100), color=255).save(image)
    source = tmp_path / "source.py"
    source.write_bytes(b"print('synthetic')\n")
    return image, source


def test_ingest_source_pair_emits_deterministic_gold_entries_with_source_provenance(tmp_path):
    image, source = _fixtures(tmp_path)
    regions = [(10, 5, 100, 20), (10, 35, 120, 20)]
    texts = ["linha 1", "linha 2"]
    expected_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    first = ingest_source_pair(
        image,
        source,
        regions,
        texts,
        owner_consent=True,
        page_id="page-001",
    )
    second = ingest_source_pair(
        image,
        source,
        regions,
        texts,
        owner_consent=True,
        page_id="page-001",
    )

    assert first == second
    assert len(first) == 2
    assert all(entry.tier.value == "gold" and entry.confidence == 1.0 for entry in first)
    assert [entry.sample_id for entry in first] == ["page-001-line-0", "page-001-line-1"]
    assert [entry.text for entry in first] == texts
    assert first[0].page.width == 200
    assert first[0].page.height == 100
    assert first[0].provenance == {
        "method": "source-pair-gold",
        "source_path": str(source),
        "source_sha256": expected_hash,
        "owner_consent": "true",
    }


def test_ingest_source_pair_requires_explicit_owner_consent(tmp_path):
    image, source = _fixtures(tmp_path)

    with pytest.raises(SourcePairError, match="owner_consent must be true"):
        ingest_source_pair(image, source, [(0, 0, 10, 10)], ["x"], owner_consent=False)


def test_ingest_source_pair_rejects_signature_marked_metadata(tmp_path):
    image, source = _fixtures(tmp_path)

    with pytest.raises(SourcePairError, match="signature-marked"):
        ingest_source_pair(
            image,
            source,
            [(0, 0, 10, 10)],
            ["x"],
            owner_consent=True,
            metadata={"review": {"is_signature": True}},
        )


def test_ingest_source_pair_requires_valid_python_source(tmp_path):
    image, source = _fixtures(tmp_path)
    source.write_text("def broken(:\n", encoding="utf-8")

    with pytest.raises(SourcePairError, match="valid Python"):
        ingest_source_pair(image, source, [(0, 0, 10, 10)], ["x"], owner_consent=True)


def test_ingest_source_pair_rejects_mismatched_inputs_and_out_of_bounds_regions(tmp_path):
    image, source = _fixtures(tmp_path)

    with pytest.raises(SourcePairError, match="same number"):
        ingest_source_pair(image, source, [(0, 0, 10, 10)], [], owner_consent=True)
    with pytest.raises(SourcePairError, match="within image bounds"):
        ingest_source_pair(image, source, [(195, 0, 10, 10)], ["x"], owner_consent=True)


def test_ingest_source_pair_accepts_empty_valid_python_source(tmp_path):
    image, source = _fixtures(tmp_path)
    source.write_bytes(b"")

    entries = ingest_source_pair(image, source, [(0, 0, 10, 10)], ["x"], owner_consent=True)

    assert entries[0].provenance["source_sha256"] == hashlib.sha256(b"").hexdigest()


def test_source_fixture_is_python_syntax_for_the_contract_test():
    ast.parse("x = 1\n")
