import numpy as np
from PIL import Image, ImageDraw

from manual_handwrite.data import LineRegion
from manual_handwrite.ingest import normalize_page, segment_lines


def test_normalize_page_returns_deterministic_grayscale_with_contrast():
    image = Image.new("RGB", (8, 4), (120, 120, 120))
    ImageDraw.Draw(image).rectangle((2, 1, 5, 2), fill=(80, 80, 80))
    original = np.asarray(image).copy()

    first = normalize_page(image)
    second = normalize_page(image)

    assert first.dtype == np.uint8
    assert first.shape == (4, 8)
    assert np.array_equal(first, second)
    assert int(first.min()) == 0
    assert int(first.max()) == 255
    assert np.array_equal(np.asarray(image), original)


def test_normalize_page_applies_exif_orientation():
    image = Image.new("L", (3, 2), 255)
    image.putpixel((0, 0), 0)
    exif = image.getexif()
    exif[274] = 6
    image.info["exif"] = exif.tobytes()

    normalized = normalize_page(image)

    assert normalized.shape == (3, 2)
    assert normalized[0, 1] == 0


def test_segment_lines_returns_ordered_line_regions_for_dark_bands():
    page = np.full((40, 32), 255, dtype=np.uint8)
    page[4:7, 3:29] = 30
    page[15:19, 1:31] = 30
    page[29:31, 5:27] = 30

    regions = segment_lines(page)

    assert regions == [
        LineRegion(x=0, y=4, width=32, height=3, line_index=0),
        LineRegion(x=0, y=15, width=32, height=4, line_index=1),
        LineRegion(x=0, y=29, width=32, height=2, line_index=2),
    ]


def test_segment_lines_empty_page_returns_no_regions():
    page = np.full((24, 18), 255, dtype=np.uint8)

    assert segment_lines(page) == []
