import json

import pytest

from manual_handwrite.transcribe.vlm_schema import (
    VLMValidationError,
    parse_vlm_pass,
    parse_vlm_protocol,
)

PAGE = {
    "page_id": "page-1",
    "blocks": [
        {
            "block_id": "block-1",
            "lines": [
                {
                    "line_id": "line-1",
                    "regions": [{"region_id": "region-1", "bbox": [0, 1, 10, 11]}],
                }
            ],
        }
    ],
}
CANDIDATES = {
    "lines": [
        {
            "line_id": "line-1",
            "candidates": [
                {"candidate_id": "candidate-1", "text": "x = 1", "confidence": 0.8},
                {"candidate_id": "candidate-2", "text": "x == 1", "confidence": 0.4},
            ],
        }
    ]
}
RECONCILIATION = {
    "lines": [
        {
            "line_id": "line-1",
            "selected_candidate_id": "candidate-1",
            "alternatives": ["candidate-2"],
        }
    ]
}
AMBIGUITY = {
    "lines": [
        {
            "line_id": "line-1",
            "resolution": "x = 1",
            "alternatives": ["x == 1"],
        }
    ]
}


def test_parse_pass_requires_json_and_attaches_provenance():
    result = parse_vlm_pass(
        json.dumps(CANDIDATES), "line_candidates", model="local-vlm", prompt="p-2"
    )

    assert result["pass"] == "line_candidates"
    assert result["data"] == CANDIDATES
    assert result["provenance"] == {"model": "local-vlm", "prompt": "p-2"}


def test_parse_pass_preserves_all_candidate_alternatives():
    result = parse_vlm_pass(json.dumps(CANDIDATES), "line_candidates", model="m", prompt="p")

    assert result["data"]["lines"][0]["candidates"] == CANDIDATES["lines"][0]["candidates"]


@pytest.mark.parametrize(
    "pass_name,payload",
    [
        ("page_structure", PAGE),
        ("line_candidates", CANDIDATES),
        ("reconciliation", RECONCILIATION),
        ("ambiguity_resolution", AMBIGUITY),
    ],
)
def test_each_protocol_pass_is_validated_strictly(pass_name, payload):
    assert parse_vlm_pass(json.dumps(payload), pass_name, model="m", prompt="p")["data"] == payload


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "null", "[]", "{}", "{'lines': []}", "not json", '{"lines": [], "lines": []}'],
)
def test_malformed_or_empty_responses_are_rejected(raw):
    with pytest.raises(VLMValidationError):
        parse_vlm_pass(raw, "line_candidates", model="m", prompt="p")


def test_unknown_fields_and_wrong_types_are_rejected():
    bad = {"lines": [{"line_id": "l", "candidates": [], "extra": True}]}
    with pytest.raises(VLMValidationError):
        parse_vlm_pass(json.dumps(bad), "line_candidates", model="m", prompt="p")

    bad = {
        "lines": [
            {"line_id": "l", "candidates": [{"candidate_id": "c", "text": 1, "confidence": 2}]}
        ]
    }
    with pytest.raises(VLMValidationError):
        parse_vlm_pass(json.dumps(bad), "line_candidates", model="m", prompt="p")


def test_protocol_requires_all_four_passes_and_checks_cross_pass_ids():
    result = parse_vlm_protocol(
        {
            "page_structure": json.dumps(PAGE),
            "line_candidates": json.dumps(CANDIDATES),
            "reconciliation": json.dumps(RECONCILIATION),
            "ambiguity_resolution": json.dumps(AMBIGUITY),
        },
        model="m",
        prompts={
            name: f"{name}-prompt"
            for name in (
                "page_structure",
                "line_candidates",
                "reconciliation",
                "ambiguity_resolution",
            )
        },
    )
    assert set(result) == {
        "page_structure",
        "line_candidates",
        "reconciliation",
        "ambiguity_resolution",
    }
    assert result["line_candidates"]["provenance"]["model"] == "m"

    missing = {"page_structure": json.dumps(PAGE)}
    with pytest.raises(VLMValidationError, match="four passes"):
        parse_vlm_protocol(missing, model="m", prompts={"page_structure": "p"})

    wrong_id = {**RECONCILIATION, "lines": [{**RECONCILIATION["lines"][0], "line_id": "other"}]}
    with pytest.raises(VLMValidationError):
        parse_vlm_protocol(
            {
                "page_structure": json.dumps(PAGE),
                "line_candidates": json.dumps(CANDIDATES),
                "reconciliation": json.dumps(wrong_id),
                "ambiguity_resolution": json.dumps(AMBIGUITY),
            },
            model="m",
            prompts={
                name: "p"
                for name in (
                    "page_structure",
                    "line_candidates",
                    "reconciliation",
                    "ambiguity_resolution",
                )
            },
        )
