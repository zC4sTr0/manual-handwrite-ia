import json

import pytest

from manual_handwrite.experiments.benchmark import (
    BenchmarkResult,
    LicenseProvenance,
    write_benchmark_result,
)


def _license() -> LicenseProvenance:
    return LicenseProvenance(
        code="MIT (official repository)",
        checkpoint="unknown; not measured",
        base_model="unknown; not measured",
        dataset="unknown; not measured",
    )


def test_result_serializes_the_contract_and_preserves_unknown_measurements(tmp_path):
    result = BenchmarkResult(
        candidate_name="DiffusionPen",
        candidate_version="commit:abc123",
        modality="offline_raster",
        available=False,
        license_provenance=_license(),
        latency_seconds=None,
        peak_vram_mb=None,
        metrics={"cer": None, "wer": None, "stress_token_exact_match": None},
        decision_status="inconclusive",
    )

    output = tmp_path / "result.json"
    write_benchmark_result(output, result)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == {
        "candidate": {
            "name": "DiffusionPen",
            "version": "commit:abc123",
            "modality": "offline_raster",
            "available": False,
        },
        "license_provenance": {
            "code": "MIT (official repository)",
            "checkpoint": "unknown; not measured",
            "base_model": "unknown; not measured",
            "dataset": "unknown; not measured",
        },
        "measurements": {"latency_seconds": None, "peak_vram_mb": None},
        "metrics": {"cer": None, "wer": None, "stress_token_exact_match": None},
        "decision_status": "inconclusive",
    }


def test_unavailable_candidate_cannot_claim_measured_result():
    with pytest.raises(ValueError, match="unavailable"):
        BenchmarkResult(
            candidate_name="missing-model",
            candidate_version="unknown",
            modality="offline_raster",
            available=False,
            license_provenance=_license(),
            latency_seconds=1.2,
            peak_vram_mb=None,
            metrics={"cer": None},
            decision_status="reject",
        )


def test_writer_rejects_local_artifact_fields(tmp_path):
    result = BenchmarkResult(
        candidate_name="fixture",
        candidate_version="1",
        modality="offline_raster",
        available=True,
        license_provenance=_license(),
        latency_seconds=0.25,
        peak_vram_mb=512.0,
        metrics={"cer": 0.1},
        decision_status="retain_behind_flag",
    )

    with pytest.raises(ValueError, match="artifact"):
        write_benchmark_result(tmp_path / "result.json", result, artifacts=["outputs/page.png"])


def test_measurements_and_metrics_must_be_real_or_null():
    with pytest.raises(TypeError, match="metrics"):
        BenchmarkResult(
            candidate_name="fixture",
            candidate_version="1",
            modality="offline_raster",
            available=True,
            license_provenance=_license(),
            latency_seconds=None,
            peak_vram_mb=None,
            metrics=["cer"],
            decision_status="inconclusive",
        )

    with pytest.raises(ValueError, match="non-negative"):
        BenchmarkResult(
            candidate_name="fixture",
            candidate_version="1",
            modality="offline_raster",
            available=True,
            license_provenance=_license(),
            latency_seconds=-1,
            peak_vram_mb=None,
            metrics={"cer": None},
            decision_status="inconclusive",
        )
