import pytest

from manual_handwrite.evaluation import (
    EvaluationReport,
    critical_token_accuracy,
    evaluate_content,
    normalized_character_error_rate,
)


def test_character_error_rate_uses_literal_edit_distance_without_fixing_candidate():
    assert normalized_character_error_rate("abc", "axc") == pytest.approx(1 / 3)
    assert normalized_character_error_rate("", "extra") is None


def test_critical_token_accuracy_compares_python_tokens_in_order():
    reference = "if total >= 2:\n    return total\n"
    candidate = "if total > 2:\n    return total\n"
    assert critical_token_accuracy(
        reference, candidate, critical_tokens={"if", "total", ">=", "2", "return"}
    ) == pytest.approx(5 / 6)


def test_report_preserves_text_provenance_and_marks_non_code_metrics_unavailable():
    report = evaluate_content(
        "print('olá')\n",
        "print('ola')\n",
        provenance={"source": "synthetic", "candidate_id": "c-1"},
    )
    assert isinstance(report, EvaluationReport)
    assert report.reference_text == "print('olá')\n"
    assert report.candidate_text == "print('ola')\n"
    assert report.provenance == {"source": "synthetic", "candidate_id": "c-1"}
    assert report.metrics["character_error_rate"] == pytest.approx(1 / 13)
    assert report.unavailable_metrics == ("style", "quality")
    serialized = report.as_dict()
    assert serialized["candidate_text"] == "print('ola')\n"
    assert serialized["unavailable_metrics"] == ["style", "quality"]
