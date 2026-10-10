"""Thumbnail rendering service, independent from Qt widgets."""
from __future__ import annotations

from io import BytesIO

import pypdfium2 as pdfium

THUMBNAIL_MAX_SIZE = 240


def render_page_thumbnail(document: pdfium.PdfDocument, page_index: int) -> bytes:
    """Render a readable JPEG thumbnail for a page grid."""
    return render_page_preview(
        document, page_index, max_size=THUMBNAIL_MAX_SIZE, quality=76
    )


def render_page_preview(
    document: pdfium.PdfDocument,
    page_index: int,
    *,
    max_size: int = 1400,
    quality: int = 86,
) -> bytes:
    """Render one PDF page for a detailed on-screen preview.

    Callers own the PdfDocument; this function closes the temporary page and bitmap.
    """
    if max_size < 1:
        raise ValueError("max_size debe ser un entero positivo.")
    if not 1 <= quality <= 95:
        raise ValueError("quality debe estar entre 1 y 95.")

    page = None
    bitmap = None
    try:
        page = document[page_index]
        width, height = page.get_size()
        scale = max_size / max(width, height, 1)
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil().convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()
    finally:
        if bitmap is not None:
            bitmap.close()
        if page is not None:
            page.close()
