from pathlib import Path
import pikepdf
import pdf_escolar.pdf_engine as pdf_engine
import pytest
from pdf_escolar.pdf_engine import (
    PdfPageRef, PdfSource, combine_pages_in_order, combine_selected_pages, inspect_pdf
)


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


def test_export_supports_an_explicit_order_across_multiple_pdfs(tmp_path):
    first, second, output = (
        tmp_path / "math.pdf",
        tmp_path / "science.pdf",
        tmp_path / "ordered.pdf",
    )
    make_pdf(first, [100, 200, 300])
    make_pdf(second, [400, 500])

    count = combine_pages_in_order(
        [
            PdfPageRef(str(second), 1),
            PdfPageRef(str(first), 2),
            PdfPageRef(str(second), 0),
            PdfPageRef(str(first), 0),
        ],
        str(output),
    )

    assert count == 4
    assert page_widths(output) == [500, 300, 400, 100]
    assert page_widths(first) == [100, 200, 300]
    assert page_widths(second) == [400, 500]


def test_invalid_explicit_page_reference_preserves_existing_output(tmp_path):
    source, output = tmp_path / "source.pdf", tmp_path / "existing.pdf"
    make_pdf(source, [200, 300])
    make_pdf(output, [800])

    with pytest.raises(ValueError, match="no existe la página 3"):
        combine_pages_in_order([PdfPageRef(str(source), 2)], str(output))

    assert page_widths(output) == [800]
    assert not list(tmp_path.glob(".existing_*.tmp.pdf"))

def test_export_reuses_open_pdfs_when_pages_are_interleaved(tmp_path, monkeypatch):
    first, second, output = (
        tmp_path / "first.pdf",
        tmp_path / "second.pdf",
        tmp_path / "interleaved.pdf",
    )
    make_pdf(first, [100, 200])
    make_pdf(second, [400, 500])
    source_paths = {first.resolve(), second.resolve()}
    open_calls = []
    real_open = pdf_engine.pikepdf.open

    def tracked_open(path, *args, **kwargs):
        candidate = Path(path).resolve()
        if candidate in source_paths:
            open_calls.append(candidate)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(pdf_engine.pikepdf, "open", tracked_open)
    references = [
        PdfPageRef(str(source), 0)
        for _ in range(10)
        for source in (first, second)
    ]

    count = combine_pages_in_order(references, str(output))

    assert count == 20
    assert page_widths(output) == [width for _ in range(10) for width in (100, 400)]
    # Each unique PDF opens once for validation and once for export, rather than
    # reopening on every A/B/A/B transition.
    assert len(open_calls) == 4
