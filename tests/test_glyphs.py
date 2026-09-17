from PIL import Image, ImageDraw

from manual_handwrite.style.glyphs import harvest_critical_glyphs


def _line_image(text: str) -> Image.Image:
    image = Image.new("L", (len(text) * 14 + 4, 20), 255)
    draw = ImageDraw.Draw(image)
    for index, char in enumerate(text):
        x = 2 + index * 14
        if char in "()[]{}":
            draw.rectangle((x + 4, 3, x + 8, 16), fill=0)
        else:
            draw.rectangle((x + 3, 5, x + 9, 14), fill=0)
    return image


def test_harvest_returns_provenance_bearing_critical_candidates():
    result = harvest_critical_glyphs(_line_image("a+b"), "a+b")

    assert [candidate.symbol for candidate in result.candidates] == ["+"]
    candidate = result.candidates[0]
    assert candidate.bbox == (19, 5, 26, 15)
    assert candidate.provenance.source_text == "a+b"
    assert candidate.provenance.character_index == 1
    assert candidate.provenance.bbox == candidate.bbox
    assert result.unresolved == ()


def test_harvest_reports_alignment_mismatch_without_guessing():
    result = harvest_critical_glyphs(_line_image("a+b"), "a++b")

    assert result.candidates == ()
    assert len(result.unresolved) == 1
    assert result.unresolved[0].reason == "component_count_mismatch"
    assert result.unresolved[0].character_index is None


def test_harvest_ignores_noncritical_characters_and_is_deterministic():
    image = _line_image("[]x")
    first = harvest_critical_glyphs(image, "[]x")
    second = harvest_critical_glyphs(image, "[]x")

    assert [candidate.symbol for candidate in first.candidates] == ["[", "]"]
    assert [candidate.bbox for candidate in first.candidates] == [
        (6, 3, 11, 17),
        (20, 3, 25, 17),
    ]
    assert [(c.symbol, c.bbox) for c in first.candidates] == [
        (c.symbol, c.bbox) for c in second.candidates
    ]
