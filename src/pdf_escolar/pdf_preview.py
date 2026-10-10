"""Thumbnail rendering service, independent from Qt widgets."""
from __future__ import annotations

from io import BytesIO

import pypdfium2 as pdfium

THUMBNAIL_MAX_SIZE = 150


def render_page_thumbnail(document: pdfium.PdfDocument, page_index: int) -> bytes:
    """Render a single PDF page to a compact JPEG thumbnail."""
    page = None
    bitmap = None
    try:
        page = document[page_index]
        width, height = page.get_size()
        scale = THUMBNAIL_MAX_SIZE / max(width, height, 1)
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil().convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=72, optimize=True)
        return buffer.getvalue()
    finally:
        if bitmap is not None:
            bitmap.close()
        if page is not None:
            page.close()
