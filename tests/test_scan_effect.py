import pytest

Image = pytest.importorskip("PIL.Image")
ImageChops = pytest.importorskip("PIL.ImageChops")
ImageDraw = pytest.importorskip("PIL.ImageDraw")

from manual_handwrite.scan import scanify  # noqa: E402


def _synthetic_page() -> Image.Image:
    image = Image.new("L", (96, 64), 255)
    ImageDraw.Draw(image).rectangle((18, 20, 76, 43), fill=0)
    return image


def test_scanify_is_deterministic_for_seed():
    image = _synthetic_page()

    first = scanify(image, seed=42, preset="scanner-escritorio")
    second = scanify(image, seed=42, preset="scanner-escritorio")
    other = scanify(image, seed=43, preset="scanner-escritorio")

    assert first.mode == "L"
    assert first.size == image.size
    assert ImageChops.difference(first, second).getbbox() is None
    assert ImageChops.difference(first, other).getbbox() is not None


def test_scanify_does_not_mutate_input_and_rejects_unknown_preset():
    image = _synthetic_page()
    original = image.copy()

    scanify(image, seed=7, preset="limpo")

    assert ImageChops.difference(image, original).getbbox() is None
    with pytest.raises(ValueError, match="preset"):
        scanify(image, seed=7, preset="unknown")
