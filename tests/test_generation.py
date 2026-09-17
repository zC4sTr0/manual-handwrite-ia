import pytest

from manual_handwrite.generation import (
    BackendCapabilities,
    BackendUnavailableError,
    Candidate,
    HandwritingBackend,
    UnavailableBackend,
)
from manual_handwrite.style import StylePack, StyleReference


def _stylepack() -> StylePack:
    return StylePack(
        references=(StyleReference("samples/a.png", {"source": "fixture"}),),
        dataset_id="fixture",
        dataset_hash="sha256:fixture",
        coverage={"characters": 1},
        scan_preset="scanner-escritorio",
        owner_consent=True,
        version="1.0",
    )


def test_backend_contract_exposes_explicit_unavailable_capabilities():
    backend = UnavailableBackend()

    assert isinstance(backend, HandwritingBackend)
    assert backend.capabilities == BackendCapabilities(
        name="unavailable",
        version="0",
        available=False,
        supports_seed=True,
        supports_count=True,
        supports_stylepack=True,
        renders_handwriting=False,
        requires_network=False,
        requires_neural=False,
    )


def test_candidate_is_small_immutable_metadata_contract():
    candidate = Candidate(text="x = 1", seed=7, index=0, backend="fixture")

    assert candidate.text == "x = 1"
    assert candidate.seed == 7
    assert candidate.index == 0
    assert candidate.backend == "fixture"
    with pytest.raises(AttributeError):
        candidate.seed = 8


@pytest.mark.parametrize("seed", [True, False, 1.0, "7"])
def test_generation_rejects_non_integer_seed(seed):
    with pytest.raises(TypeError, match="seed"):
        UnavailableBackend().generate("x", _stylepack(), seed=seed, count=1)


@pytest.mark.parametrize("count", [0, -1, True, 1.5, "2"])
def test_generation_rejects_non_positive_integer_count(count):
    error = ValueError if isinstance(count, int) and not isinstance(count, bool) else TypeError
    with pytest.raises(error, match="count"):
        UnavailableBackend().generate("x", _stylepack(), seed=7, count=count)


def test_unavailable_backend_fails_honestly_without_system_font_fallback():
    backend = UnavailableBackend()

    message = "handwriting generation backend is unavailable"
    with pytest.raises(BackendUnavailableError, match=message):
        backend.generate("x = 1", _stylepack(), seed=7, count=2)


def test_contract_rejects_non_text_and_non_stylepack_inputs():
    backend = UnavailableBackend()

    with pytest.raises(TypeError, match="text"):
        backend.generate(123, _stylepack(), seed=7, count=1)
    with pytest.raises(TypeError, match="stylepack"):
        backend.generate("x", object(), seed=7, count=1)
