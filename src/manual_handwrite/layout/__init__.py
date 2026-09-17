"""Deterministic, measurement-based page layout primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from PIL import ImageFont

A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0


class FontLike(Protocol):
    def getlength(self, text: str) -> float: ...


def _measure(font: FontLike, text: str) -> float:
    return float(font.getlength(text))


def _default_font() -> FontLike:
    return ImageFont.load_default()


@dataclass(frozen=True)
class PageSpec:
    """A4 page geometry; dimensions are pixels and default to 300 DPI."""

    dpi: int = 300
    width_px: int | None = None
    height_px: int | None = None
    margin_left_mm: float = 20.0
    margin_right_mm: float = 20.0
    margin_top_mm: float = 20.0
    margin_bottom_mm: float = 20.0
    margin_left_px: int | None = None
    margin_right_px: int | None = None
    margin_top_px: int | None = None
    margin_bottom_px: int | None = None
    line_height_px: int | None = None
    paragraph_indent_px: int = 0

    def __post_init__(self) -> None:
        if self.dpi <= 0:
            raise ValueError("dpi must be positive")
        width = self.width_px if self.width_px is not None else round(A4_WIDTH_MM * self.dpi / 25.4)
        height = (
            self.height_px if self.height_px is not None else round(A4_HEIGHT_MM * self.dpi / 25.4)
        )
        scale = self.dpi / 25.4
        margins = tuple(
            value if value is not None else round(mm * scale)
            for value, mm in (
                (self.margin_left_px, self.margin_left_mm),
                (self.margin_right_px, self.margin_right_mm),
                (self.margin_top_px, self.margin_top_mm),
                (self.margin_bottom_px, self.margin_bottom_mm),
            )
        )
        line_height = self.line_height_px if self.line_height_px is not None else 48
        if width <= 0 or height <= 0 or line_height <= 0:
            raise ValueError("page dimensions and line height must be positive")
        if any(value < 0 for value in margins) or width <= margins[0] + margins[1]:
            raise ValueError("margins must be non-negative and leave content width")
        if self.paragraph_indent_px < 0:
            raise ValueError("paragraph_indent_px must not be negative")
        object.__setattr__(self, "width_px", width)
        object.__setattr__(self, "height_px", height)
        object.__setattr__(self, "margin_left_px", margins[0])
        object.__setattr__(self, "margin_right_px", margins[1])
        object.__setattr__(self, "margin_top_px", margins[2])
        object.__setattr__(self, "margin_bottom_px", margins[3])
        object.__setattr__(self, "line_height_px", line_height)

    @property
    def pixel_size(self) -> tuple[int, int]:
        return (self.width_px, self.height_px)

    @property
    def margins_px(self) -> tuple[int, int, int, int]:
        return (
            self.margin_left_px,
            self.margin_right_px,
            self.margin_top_px,
            self.margin_bottom_px,
        )

    @property
    def content_width_px(self) -> int:
        return self.width_px - self.margin_left_px - self.margin_right_px

    @property
    def content_box(self) -> tuple[int, int, int, int]:
        return (
            self.margin_left_px,
            self.margin_top_px,
            self.width_px - self.margin_right_px,
            self.height_px - self.margin_bottom_px,
        )


@dataclass(frozen=True)
class LayoutLine:
    text: str
    x: int
    y: int
    width: int


@dataclass
class PageLayout:
    pages: list[list[LayoutLine]] = field(default_factory=list)
    spec: PageSpec = field(default_factory=PageSpec)


def wrap_text(text: str, max_width: int, font: FontLike | None = None) -> list[str]:
    """Wrap by measured advances, splitting words wider than the line."""
    if max_width <= 0:
        raise ValueError("max_width must be positive")
    font = font or _default_font()
    if not text:
        return [""]
    result: list[str] = []
    for paragraph in text.splitlines() or [""]:
        if not paragraph:
            result.append("")
            continue
        current = ""
        for word in paragraph.split():
            if _measure(font, word) > max_width:
                if current:
                    result.append(current)
                    current = ""
                chunk = ""
                for char in word:
                    if chunk and _measure(font, chunk + char) > max_width:
                        result.append(chunk)
                        chunk = char
                    else:
                        chunk += char
                current = chunk
                continue
            candidate = word if not current else f"{current} {word}"
            if current and _measure(font, candidate) > max_width:
                result.append(current)
                current = word
            else:
                current = candidate
        if current:
            result.append(current)
    return result


def layout_text(
    text: str, spec: PageSpec | None = None, font: FontLike | None = None
) -> PageLayout:
    """Position wrapped lines, indent paragraphs, and break at page capacity."""
    spec = spec or PageSpec()
    font = font or _default_font()
    if spec.paragraph_indent_px >= spec.content_width_px:
        raise ValueError("paragraph_indent_px must leave content width")
    pages: list[list[LayoutLine]] = [[]]
    capacity = max(
        1, (spec.height_px - spec.margin_top_px - spec.margin_bottom_px) // spec.line_height_px
    )
    for _paragraph_index, paragraph in enumerate(text.split("\n")):
        indent = spec.paragraph_indent_px
        lines = wrap_text(paragraph, spec.content_width_px - indent, font)
        for line_index, line in enumerate(lines):
            if len(pages[-1]) >= capacity:
                pages.append([])
            x = spec.margin_left_px + (indent if line_index == 0 else 0)
            pages[-1].append(
                LayoutLine(
                    line,
                    x,
                    spec.margin_top_px + len(pages[-1]) * spec.line_height_px,
                    round(_measure(font, line)),
                )
            )
    return PageLayout(pages, spec)


A4PageSpec = PageSpec
compose_layout = layout_text
