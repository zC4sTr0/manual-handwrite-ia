"""Dependency-free, honest benchmark result contract.

This module records benchmark observations; it does not run model inference.
Unknown or unmeasured values are represented by ``None`` and are never
replaced with estimates.  Generated images, checkpoints, and other local
artifacts are deliberately outside the serializable contract.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from numbers import Real
from pathlib import Path
from typing import Any

_DECISIONS = frozenset({"inconclusive", "promote_experimental", "retain_behind_flag", "reject"})
_MODALITIES = frozenset({"offline_raster", "online_trajectory"})


@dataclass(frozen=True)
class LicenseProvenance:
    """Separate provenance notes for code and model/data assets."""

    code: str
    checkpoint: str
    base_model: str
    dataset: str

    def __post_init__(self) -> None:
        for field in ("code", "checkpoint", "base_model", "dataset"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"license provenance {field} must be a non-empty string")

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "checkpoint": self.checkpoint,
            "base_model": self.base_model,
            "dataset": self.dataset,
        }


@dataclass(frozen=True)
class BenchmarkResult:
    """Measured or explicitly unknown result for one candidate backend.

    ``available`` means that the candidate was actually available to the
    benchmark run.  An unavailable candidate cannot carry measurements: doing
    so would turn a protocol claim or README number into a local result.
    """

    candidate_name: str
    candidate_version: str
    modality: str
    available: bool
    license_provenance: LicenseProvenance
    latency_seconds: float | None
    peak_vram_mb: float | None
    metrics: Mapping[str, Real | None]
    decision_status: str

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_name, str) or not self.candidate_name.strip():
            raise ValueError("candidate name must be a non-empty string")
        if not isinstance(self.candidate_version, str) or not self.candidate_version.strip():
            raise ValueError("candidate version must be a non-empty string")
        if self.modality not in _MODALITIES:
            raise ValueError(f"unsupported modality: {self.modality!r}")
        if not isinstance(self.available, bool):
            raise TypeError("available must be a boolean")
        if not isinstance(self.license_provenance, LicenseProvenance):
            raise TypeError("license_provenance must be LicenseProvenance")
        if self.decision_status not in _DECISIONS:
            raise ValueError(f"unsupported decision status: {self.decision_status!r}")
        _validate_measurement(self.latency_seconds, "latency_seconds")
        _validate_measurement(self.peak_vram_mb, "peak_vram_mb")
        if not isinstance(self.metrics, Mapping):
            raise TypeError("metrics must be a mapping")
        for name, value in self.metrics.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("metric names must be non-empty strings")
            if value is not None:
                _validate_measurement(value, f"metric {name!r}")
        if not self.available:
            if self.latency_seconds is not None or self.peak_vram_mb is not None:
                raise ValueError("unavailable candidates cannot claim measurements")
            if any(value is not None for value in self.metrics.values()):
                raise ValueError("unavailable candidates cannot claim measured metrics")
            if self.decision_status == "promote_experimental":
                raise ValueError("unavailable candidates cannot be promoted")

    def as_dict(self) -> dict[str, Any]:
        """Return only the public result contract, never artifact references."""
        return {
            "candidate": {
                "name": self.candidate_name,
                "version": self.candidate_version,
                "modality": self.modality,
                "available": self.available,
            },
            "license_provenance": self.license_provenance.as_dict(),
            "measurements": {
                "latency_seconds": self.latency_seconds,
                "peak_vram_mb": self.peak_vram_mb,
            },
            "metrics": dict(self.metrics),
            "decision_status": self.decision_status,
        }


def write_benchmark_result(
    destination: str | Path,
    result: BenchmarkResult,
    *,
    artifacts: Iterable[object] | None = None,
) -> None:
    """Write a JSON result without copying local artifacts into it.

    ``artifacts`` is accepted only as a guardrail for callers migrating from
    ad-hoc reports.  Any supplied artifact reference is rejected rather than
    serialized, keeping images, checkpoints, and private paths out of output.
    """
    if not isinstance(result, BenchmarkResult):
        raise TypeError("result must be a BenchmarkResult")
    if artifacts is not None and any(True for _ in artifacts):
        raise ValueError("local artifact references are not allowed in benchmark output")
    path = Path(destination)
    path.write_text(
        json.dumps(result.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validate_measurement(value: object, label: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label} must be a real number or null")
    if not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite")
    if value < 0:
        raise ValueError(f"{label} must be non-negative")
