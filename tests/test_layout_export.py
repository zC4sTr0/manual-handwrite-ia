from pathlib import Path

from PIL import Image

from manual_handwrite.export import export_pdf, export_png
from manual_handwrite.layout import PageSpec, layout_text, wrap_text


class FixedFont:
    def getlength(self, text: str) -> float:
        return len(text) * 10


def test_a4_geometry_is_deterministic_at_300_dpi():
    spec = PageSpec(dpi=300)

    assert spec.pixel_size == (2480, 3508)
    assert spec.content_box == (236, 236, 2244, 3272)
    assert spec.line_height_px > 0


def test_wrap_text_uses_measured_character_widths_and_keeps_words():
    lines = wrap_text("aa bbbb cc", max_width=55, font=FixedFont())

    assert lines == ["aa", "bbbb", "cc"]
    assert all(sum(FixedFont().getlength(char) for char in line) <= 55 for line in lines)


def test_layout_applies_paragraph_indent_and_page_breaks():
    spec = PageSpec(
        width_px=240,
        height_px=100,
        margin_left_px=10,
        margin_right_px=10,
        margin_top_px=10,
        margin_bottom_px=10,
        line_height_px=20,
        paragraph_indent_px=15,
    )

    result = layout_text(
        (
            "one two three four five six seven eight nine ten "
            "eleven twelve thirteen fourteen fifteen sixteen"
        ),
        spec=spec,
        font=FixedFont(),
    )

    assert len(result.pages) == 2
    assert result.pages[0][0].x == 25
    assert result.pages[0][0].y == 10
    assert result.pages[1][0].y == 10
    assert all(
        line.x + line.width <= spec.width_px - spec.margin_right_px
        for page in result.pages
        for line in page
    )


def test_export_png_preserves_generator_metadata(tmp_path: Path):
    path = tmp_path / "page.png"
    export_png(Image.new("RGB", (20, 20), "white"), path, metadata={"author": "test"})

    with Image.open(path) as image:
        assert image.info["generator"] == "manual-handwrite-ia"
        assert image.info["author"] == "test"


def test_export_pdf_preserves_generator_metadata(tmp_path: Path):
    path = tmp_path / "page.pdf"
    export_pdf(Image.new("RGB", (20, 20), "white"), path)

    pdf = path.read_bytes().decode("latin-1")
    assert "/Producer" in pdf
    assert "manual-handwrite-ia".encode("utf-16-be") in pdf.encode("latin-1")
