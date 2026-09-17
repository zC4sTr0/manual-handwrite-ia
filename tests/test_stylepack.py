import json

import pytest

from manual_handwrite.style import (
    StylePack,
    StylePackError,
    StyleReference,
    load_stylepack,
    write_stylepack,
)


def _pack() -> StylePack:
    return StylePack(
        references=(
            StyleReference("samples/owner/a.png", {"source": "fixture", "line": 7}),
            StyleReference("samples/owner/b.png", {"source": "fixture", "line": 8}),
        ),
        dataset_id="owner-dataset",
        dataset_hash="sha256:abc123",
        coverage={"characters": 42, "tokens": 12, "operators": 9},
        scan_preset="scanner-escritorio",
        owner_consent=True,
        version="1.0",
    )


def test_stylepack_round_trip_preserves_metadata_and_provenance(tmp_path):
    path = tmp_path / "stylepack.json"
    write_stylepack(path, _pack())

    loaded = load_stylepack(path)

    assert loaded == _pack()
    assert loaded.references[0].path == "samples/owner/a.png"
    assert loaded.references[0].provenance == {"source": "fixture", "line": 7}
    assert json.loads(path.read_text()) == {
        "version": "1.0",
        "owner_consent": True,
        "references": [
            {"path": "samples/owner/a.png", "provenance": {"source": "fixture", "line": 7}},
            {"path": "samples/owner/b.png", "provenance": {"source": "fixture", "line": 8}},
        ],
        "dataset": {"id": "owner-dataset", "hash": "sha256:abc123"},
        "coverage": {"characters": 42, "tokens": 12, "operators": 9},
        "scan_preset": "scanner-escritorio",
    }


def test_loader_fails_closed_without_explicit_consent(tmp_path):
    path = tmp_path / "stylepack.json"
    payload = _pack().to_dict()
    payload["owner_consent"] = 1
    path.write_text(json.dumps(payload))

    with pytest.raises(StylePackError, match="owner_consent"):
        load_stylepack(path)


def test_loader_rejects_signature_marked_style(tmp_path):
    path = tmp_path / "stylepack.json"
    payload = _pack().to_dict()
    payload["signature_marked"] = True
    path.write_text(json.dumps(payload))

    with pytest.raises(StylePackError, match="signature"):
        load_stylepack(path)


def test_references_must_be_relative_and_no_image_is_read(tmp_path):
    path = tmp_path / "stylepack.json"
    payload = _pack().to_dict()
    payload["references"][0]["path"] = "../outside.png"
    path.write_text(json.dumps(payload))

    with pytest.raises(StylePackError, match="relative"):
        load_stylepack(path)


def test_writer_accepts_metadata_without_touching_reference_files(tmp_path):
    pack = _pack()
    manifest = tmp_path / "nested" / "manifest.json"

    write_stylepack(manifest, pack)

    assert manifest.exists()
    assert not (tmp_path / "samples").exists()
