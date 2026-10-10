"""Tests for PDF preview rendering helpers."""
from __future__ import annotations

from io import BytesIO

from PIL import Image

from pdf_escolar.pdf_preview import render_page_preview, render_page_thumbnail


class FakeBitmap:
    def __init__(self, image: Image.Image):
        self.image = image
        self.closed = False

    def to_pil(self) -> Image.Image:
        return self.image

    def close(self) -> None:
        self.closed = True


class FakePage:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self.render_scale: float | None = None
        self.bitmap: FakeBitmap | None = None
        self.closed = False

    def get_size(self) -> tuple[int, int]:
        return self.size

    def render(self, *, scale: float) -> FakeBitmap:
        self.render_scale = scale
        width = max(1, round(self.size[0] * scale))
        height = max(1, round(self.size[1] * scale))
        self.bitmap = FakeBitmap(Image.new("RGB", (width, height), "white"))
        return self.bitmap

    def close(self) -> None:
        self.closed = True


class FakeDocument:
    def __init__(self, page: FakePage):
        self.page = page

    def __getitem__(self, index: int) -> FakePage:
        assert index == 0
        return self.page


def test_detail_preview_uses_requested_max_dimension_and_closes_resources() -> None:
    page = FakePage((2400, 1200))
    output = render_page_preview(FakeDocument(page), 0, max_size=600, quality=88)

    image = Image.open(BytesIO(output))
    assert image.size == (600, 300)
    assert image.format == "JPEG"
    assert page.render_scale == 0.25
    assert page.closed
    assert page.bitmap is not None and page.bitmap.closed


def test_thumbnail_wrapper_uses_configured_render_size() -> None:
    page = FakePage((1200, 1800))
    output = render_page_thumbnail(FakeDocument(page), 0)

    image = Image.open(BytesIO(output))
    assert max(image.size) == 240
    assert page.closed
    assert page.bitmap is not None and page.bitmap.closed


def test_detail_preview_rejects_invalid_render_parameters() -> None:
    page = FakePage((1000, 1000))
    try:
        render_page_preview(FakeDocument(page), 0, max_size=0)
    except ValueError as exc:
        assert "max_size" in str(exc)
    else:
        raise AssertionError("Se esperaba un error para max_size=0.")

    try:
        render_page_preview(FakeDocument(page), 0, quality=0)
    except ValueError as exc:
        assert "quality" in str(exc)
    else:
        raise AssertionError("Se esperaba un error para quality=0.")
