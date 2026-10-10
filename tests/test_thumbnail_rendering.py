from io import BytesIO
from pathlib import Path

import pikepdf
import pypdfium2 as pdfium
from PIL import Image

from pdf_escolar.pdf_preview import THUMBNAIL_MAX_SIZE, render_page_thumbnail


def test_thumbnail_renderer_returns_compact_image(tmp_path: Path):
    source = tmp_path / "book.pdf"
    with pikepdf.Pdf.new() as pdf:
        pdf.add_blank_page(page_size=(612, 792))
        pdf.save(source)

    document = pdfium.PdfDocument(str(source))
    try:
        rendered = render_page_thumbnail(document, 0)
    finally:
        document.close()

    with Image.open(BytesIO(rendered)) as image:
        assert image.format == "JPEG"
        assert max(image.size) <= THUMBNAIL_MAX_SIZE
        assert min(image.size) > 0
