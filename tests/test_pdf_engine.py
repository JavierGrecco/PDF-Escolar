from pathlib import Path
import pikepdf
import pytest
from pdf_escolar.pdf_engine import PdfSource, combine_selected_pages, inspect_pdf


def make_pdf(path: Path, widths: list[float]) -> None:
    with pikepdf.Pdf.new() as pdf:
        for width in widths:
            pdf.add_blank_page(page_size=(width, 792))
        pdf.save(path)


def page_widths(path: Path) -> list[float]:
    with pikepdf.open(path) as pdf:
        return [float(p.mediabox[2]) - float(p.mediabox[0]) for p in pdf.pages]


def test_inspect_pdf_returns_page_count(tmp_path):
    source = tmp_path / "book.pdf"
    make_pdf(source, [200, 300, 400])
    assert inspect_pdf(str(source)) == 3


def test_export_keeps_source_and_range_order(tmp_path):
    first, second, output = tmp_path / "math.pdf", tmp_path / "science.pdf", tmp_path / "out.pdf"
    make_pdf(first, [100, 200, 300])
    make_pdf(second, [400, 500])
    progress = []
    count = combine_selected_pages(
        [PdfSource(str(first), "3, 1"), PdfSource(str(second), "2")],
        str(output),
        lambda done, total, message: progress.append((done, total, message)),
    )
    assert count == 3
    assert any(message.startswith("Combinando páginas:") for _, _, message in progress)
    assert progress[-1] == (3, 3, "PDF creado correctamente.")
    assert page_widths(output) == [300, 100, 500]
    assert page_widths(first) == [100, 200, 300]
    assert page_widths(second) == [400, 500]


def test_output_cannot_overwrite_an_input(tmp_path):
    source = tmp_path / "original.pdf"
    make_pdf(source, [200, 300])
    with pytest.raises(ValueError, match="no puede reemplazar"):
        combine_selected_pages([PdfSource(str(source), "1")], str(source))
    assert page_widths(source) == [200, 300]


def test_invalid_ranges_leave_no_partial_output(tmp_path):
    source, output = tmp_path / "original.pdf", tmp_path / "result.pdf"
    make_pdf(source, [200, 300])
    with pytest.raises(ValueError, match="supera ese límite"):
        combine_selected_pages([PdfSource(str(source), "1-20")], str(output))
    assert not output.exists()
    assert not list(tmp_path.glob(".result_*.tmp.pdf"))


def test_requires_at_least_one_source(tmp_path):
    with pytest.raises(ValueError, match="Agregá al menos un archivo"):
        combine_selected_pages([], str(tmp_path / "out.pdf"))


def test_output_requires_pdf_extension(tmp_path):
    source = tmp_path / "original.pdf"
    make_pdf(source, [200])
    with pytest.raises(ValueError, match="extensión .pdf"):
        combine_selected_pages([PdfSource(str(source), "1")], str(tmp_path / "result.txt"))


def test_inspect_pdf_rejects_a_document_without_pages(tmp_path):
    source = tmp_path / "empty.pdf"
    with pikepdf.Pdf.new() as pdf:
        pdf.save(source)
    with pytest.raises(ValueError, match="no contiene páginas"):
        inspect_pdf(str(source))

def test_invalid_ranges_preserve_an_existing_output(tmp_path):
    source, output = tmp_path / "source.pdf", tmp_path / "existing.pdf"
    make_pdf(source, [200, 300])
    make_pdf(output, [800])

    with pytest.raises(ValueError, match="supera ese límite"):
        combine_selected_pages([PdfSource(str(source), "1-20")], str(output))

    assert page_widths(output) == [800]
    assert not list(tmp_path.glob(".existing_*.tmp.pdf"))


def test_successful_export_replaces_an_existing_output(tmp_path):
    source, output = tmp_path / "source.pdf", tmp_path / "existing.pdf"
    make_pdf(source, [200, 300])
    make_pdf(output, [800])

    count = combine_selected_pages([PdfSource(str(source), "2")], str(output))

    assert count == 1
    assert page_widths(output) == [300]
    assert page_widths(source) == [200, 300]


def test_inspect_pdf_rejects_a_password_protected_document(tmp_path):
    source = tmp_path / "protected.pdf"
    with pikepdf.Pdf.new() as pdf:
        pdf.add_blank_page()
        pdf.save(
            source,
            encryption=pikepdf.Encryption(owner="owner", user="reader", R=4),
        )

    with pytest.raises(pikepdf.PasswordError):
        inspect_pdf(str(source))

