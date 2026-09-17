import json

import pytest

from manual_handwrite import __version__
from manual_handwrite.cli import main


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_scanify_command_writes_processed_image_with_metadata(tmp_path):
    image_module = pytest.importorskip("PIL.Image")
    source = tmp_path / "source.png"
    output = tmp_path / "scanned.png"
    image_module.new("L", (24, 16), 255).save(source)

    assert (
        main(
            [
                "scanify",
                str(source),
                "--preset",
                "limpo",
                "--seed",
                "7",
                "--out",
                str(output),
            ]
        )
        == 0
    )

    result = image_module.open(output)
    assert result.size == (24, 16)
    assert result.info["generator"] == "manual-handwrite-ia"


def test_coverage_command_writes_json_report(tmp_path):
    source = tmp_path / "sample.py"
    output = tmp_path / "coverage.json"
    source.write_text("def f(x):\n    return x >= 2\n", encoding="utf-8")

    assert main(["coverage", str(source), "--out", str(output)]) == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["tokens"]["def"] == 1
    assert report["tokens"]["2"] == 1
    assert report["operators"][">="] == 1


def test_source_pair_command_writes_gold_manifest_to_nested_output(tmp_path):
    image_module = pytest.importorskip("PIL.Image")
    image = tmp_path / "page.png"
    source = tmp_path / "source.py"
    regions = tmp_path / "regions.json"
    output = tmp_path / "nested" / "gold.jsonl"
    image_module.new("L", (80, 40), 255).save(image)
    source.write_text("value = 1\n", encoding="utf-8")
    regions.write_text(
        json.dumps({"regions": [[2, 3, 20, 10]], "texts": ["value"]}),
        encoding="utf-8",
    )

    assert (
        main(
            [
                "source-pair",
                str(image),
                str(source),
                str(regions),
                "--out",
                str(output),
                "--owner-consent",
            ]
        )
        == 0
    )

    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["tier"] == "gold"
    assert record["text"] == "value"
    assert record["provenance"]["method"] == "source-pair-gold"


def test_source_pair_command_rejects_missing_owner_consent(tmp_path):
    image_module = pytest.importorskip("PIL.Image")
    image = tmp_path / "page.png"
    source = tmp_path / "source.py"
    regions = tmp_path / "regions.json"
    output = tmp_path / "gold.jsonl"
    image_module.new("L", (20, 20), 255).save(image)
    source.write_text("value = 1\n", encoding="utf-8")
    regions.write_text(
        json.dumps({"regions": [[0, 0, 10, 10]], "texts": ["value"]}),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit):
        main(["source-pair", str(image), str(source), str(regions), "--out", str(output)])
    assert not output.exists()
