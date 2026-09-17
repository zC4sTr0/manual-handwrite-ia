import pytest

from manual_handwrite.transcribe import (
    OfflineTranscriptionAdapter,
    SuppliedTextTranscriber,
    TranscriptionResult,
    VerificationStatus,
)


def test_supplied_text_transcriber_returns_deterministic_auditable_result():
    transcriber = SuppliedTextTranscriber()

    result = transcriber.transcribe("Olá, mundo!", source="examples/source.py")

    assert isinstance(transcriber, OfflineTranscriptionAdapter)
    assert isinstance(result, TranscriptionResult)
    assert result.candidates == ("Olá, mundo!",)
    assert result.confidence == 1.0
    assert result.verification_status is VerificationStatus.SUPPLIED_TEXT
    assert result.provenance == {
        "adapter": "supplied-text-reference",
        "source": "examples/source.py",
        "input": "pre-supplied-text",
        "visual_transcription": "not-performed",
        "network": "not-called",
    }


def test_supplied_text_transcriber_is_repeatable():
    transcriber = SuppliedTextTranscriber()

    assert transcriber.transcribe("same") == transcriber.transcribe("same")


@pytest.mark.parametrize("text", [None, "", "   ", "\n\t"])
def test_supplied_text_transcriber_refuses_missing_or_empty_text(text):
    with pytest.raises(ValueError, match="non-empty pre-supplied text"):
        SuppliedTextTranscriber().transcribe(text)


def test_result_rejects_invalid_confidence_and_candidates():
    with pytest.raises(ValueError, match="at least one candidate"):
        TranscriptionResult((), {}, 1.0, VerificationStatus.SUPPLIED_TEXT)

    with pytest.raises(ValueError, match="between 0 and 1"):
        TranscriptionResult(("text",), {}, 1.1, VerificationStatus.SUPPLIED_TEXT)


def test_protocol_documents_offline_only_contract():
    assert "network" in OfflineTranscriptionAdapter.transcribe.__doc__
    assert "VLM" in OfflineTranscriptionAdapter.transcribe.__doc__
