"""Strict, local contracts for the four-pass VLM transcription protocol.

This module only parses JSON with the standard library.  It never evaluates
Python expressions, imports a provider SDK, or performs network I/O.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

PASS_NAMES = (
    "page_structure",
    "line_candidates",
    "reconciliation",
    "ambiguity_resolution",
)


class VLMValidationError(ValueError):
    """Raised when a VLM response is not a complete protocol document."""


def _fail(path: str, message: str) -> None:
    raise VLMValidationError(f"{path}: {message}")


def _object(value: Any, path: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "must be a JSON object")
    if set(value) != keys:
        missing = keys - set(value)
        extra = set(value) - keys
        detail = []
        if missing:
            detail.append(f"missing {sorted(missing)}")
        if extra:
            detail.append(f"unknown {sorted(extra)}")
        _fail(path, "; ".join(detail))
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(path, "must be a non-empty string")
    return value


def _array(value: Any, path: str, *, nonempty: bool = True) -> list[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        _fail(path, "must be a non-empty JSON array")
    return value


def _unique(value: str, seen: set[str], path: str) -> None:
    if value in seen:
        _fail(path, "must be unique")
    seen.add(value)


def _page_structure(value: Any) -> dict[str, Any]:
    root = _object(value, "$", {"page_id", "blocks"})
    _string(root["page_id"], "$.page_id")
    block_ids: set[str] = set()
    line_ids: set[str] = set()
    region_ids: set[str] = set()
    for bi, block in enumerate(_array(root["blocks"], "$.blocks")):
        block = _object(block, f"$.blocks[{bi}]", {"block_id", "lines"})
        block_id = _string(block["block_id"], f"$.blocks[{bi}].block_id")
        _unique(block_id, block_ids, f"$.blocks[{bi}].block_id")
        for li, line in enumerate(_array(block["lines"], f"$.blocks[{bi}].lines")):
            line = _object(line, f"$.blocks[{bi}].lines[{li}]", {"line_id", "regions"})
            line_id = _string(line["line_id"], f"$.blocks[{bi}].lines[{li}].line_id")
            _unique(line_id, line_ids, f"$.blocks[{bi}].lines[{li}].line_id")
            for ri, region in enumerate(_array(line["regions"], f"...lines[{li}].regions")):
                region = _object(region, f"...regions[{ri}]", {"region_id", "bbox"})
                region_id = _string(region["region_id"], f"...regions[{ri}].region_id")
                _unique(region_id, region_ids, f"...regions[{ri}].region_id")
                bbox = _array(region["bbox"], f"...regions[{ri}].bbox", nonempty=False)
                if len(bbox) != 4 or any(
                    isinstance(n, bool) or not isinstance(n, (int, float)) for n in bbox
                ):
                    _fail(f"...regions[{ri}].bbox", "must contain exactly four JSON numbers")
                if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                    _fail(f"...regions[{ri}].bbox", "must have positive width and height")
    return root


def _line_candidates(value: Any) -> dict[str, Any]:
    root = _object(value, "$", {"lines"})
    for li, line in enumerate(_array(root["lines"], "$.lines")):
        line = _object(line, f"$.lines[{li}]", {"line_id", "candidates"})
        _string(line["line_id"], f"$.lines[{li}].line_id")
        seen: set[str] = set()
        for ci, candidate in enumerate(_array(line["candidates"], f"$.lines[{li}].candidates")):
            candidate = _object(
                candidate, f"$.lines[{li}].candidates[{ci}]", {"candidate_id", "text", "confidence"}
            )
            candidate_id = _string(candidate["candidate_id"], f"...candidates[{ci}].candidate_id")
            _unique(candidate_id, seen, f"...candidates[{ci}].candidate_id")
            _string(candidate["text"], f"...candidates[{ci}].text")
            confidence = candidate["confidence"]
            if (
                isinstance(confidence, bool)
                or not isinstance(confidence, (int, float))
                or not 0 <= confidence <= 1
            ):
                _fail(f"...candidates[{ci}].confidence", "must be a JSON number between 0 and 1")
    return root


def _line_map(value: Any, pass_name: str) -> dict[str, Any]:
    root = _object(value, "$", {"lines"})
    for li, line in enumerate(_array(root["lines"], "$.lines")):
        if pass_name == "reconciliation":
            line = _object(
                line, f"$.lines[{li}]", {"line_id", "selected_candidate_id", "alternatives"}
            )
            _string(line["line_id"], f"$.lines[{li}].line_id")
            _string(line["selected_candidate_id"], f"$.lines[{li}].selected_candidate_id")
            alternatives = _array(
                line["alternatives"], f"$.lines[{li}].alternatives", nonempty=False
            )
            for ai, item in enumerate(alternatives):
                _string(item, f"$.lines[{li}].alternatives[{ai}]")
        else:
            line = _object(line, f"$.lines[{li}]", {"line_id", "resolution", "alternatives"})
            _string(line["line_id"], f"$.lines[{li}].line_id")
            _string(line["resolution"], f"$.lines[{li}].resolution")
            for ai, item in enumerate(
                _array(line["alternatives"], f"$.lines[{li}].alternatives", nonempty=False)
            ):
                _string(item, f"$.lines[{li}].alternatives[{ai}]")
    return root


def validate_vlm_response(data: Any, pass_name: str) -> dict[str, Any]:
    """Validate already-decoded JSON data and return it unchanged."""
    if pass_name not in PASS_NAMES:
        raise VLMValidationError(f"unknown pass {pass_name!r}")
    if pass_name == "page_structure":
        return _page_structure(data)
    if pass_name == "line_candidates":
        return _line_candidates(data)
    return _line_map(data, pass_name)


def parse_vlm_pass(response: str, pass_name: str, *, model: str, prompt: str) -> dict[str, Any]:
    """Parse one response strictly, retaining data and model/prompt provenance."""
    if not isinstance(response, str) or not response.strip():
        raise VLMValidationError("response must be non-empty JSON text")
    _string(model, "provenance.model")
    _string(prompt, "provenance.prompt")

    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        data = json.loads(
            response,
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicate_pairs,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise VLMValidationError("response is not valid JSON") from exc
    return {
        "pass": pass_name,
        "data": validate_vlm_response(data, pass_name),
        "provenance": {"model": model, "prompt": prompt},
    }


def parse_vlm_protocol(
    responses: Mapping[str, str], *, model: str, prompts: Mapping[str, str]
) -> dict[str, dict[str, Any]]:
    """Parse all four passes and enforce their shared line/candidate references."""
    if not isinstance(responses, Mapping) or set(responses) != set(PASS_NAMES):
        raise VLMValidationError("protocol requires all four passes")
    if not isinstance(prompts, Mapping) or set(prompts) != set(PASS_NAMES):
        raise VLMValidationError("prompts must identify all four passes")
    result = {
        name: parse_vlm_pass(responses[name], name, model=model, prompt=prompts[name])
        for name in PASS_NAMES
    }
    page_ids = {
        line["line_id"]
        for block in result["page_structure"]["data"]["blocks"]
        for line in block["lines"]
    }
    candidate_data = result["line_candidates"]["data"]
    candidate_ids = {
        c["candidate_id"] for line in candidate_data["lines"] for c in line["candidates"]
    }
    for name in PASS_NAMES[1:]:
        ids = {line["line_id"] for line in result[name]["data"]["lines"]}
        if ids != page_ids:
            raise VLMValidationError(f"{name}: line IDs do not match page structure")
    for line in result["reconciliation"]["data"]["lines"]:
        if line["selected_candidate_id"] not in candidate_ids or any(
            item not in candidate_ids for item in line["alternatives"]
        ):
            raise VLMValidationError("reconciliation: unknown candidate reference")
    return result


# Descriptive alias for callers that process one response at a time.
parse_vlm_response = parse_vlm_pass


__all__ = [
    "PASS_NAMES",
    "VLMValidationError",
    "parse_vlm_pass",
    "parse_vlm_protocol",
    "parse_vlm_response",
    "validate_vlm_response",
]
