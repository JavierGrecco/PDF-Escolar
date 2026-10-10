"""PDF operations kept separate from the graphical interface."""
from __future__ import annotations

import os
from collections import OrderedDict
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import pikepdf

from pdf_escolar.page_ranges import parse_page_ranges


MAX_OPEN_SOURCE_PDFS = 8


@dataclass(frozen=True)
class PdfSource:
    """One source PDF and its one-based page selection."""

    path: str
    page_ranges: str


@dataclass(frozen=True)
class PdfPageRef:
    """A single zero-based page reference in a source PDF."""

    path: str
    page_index: int


def inspect_pdf(path: str) -> int:
    """Open a PDF and return its number of pages."""
    with pikepdf.open(path) as pdf:
        page_count = len(pdf.pages)
    if page_count == 0:
        raise ValueError("El PDF no contiene páginas.")
    return page_count


def combine_selected_pages(
    sources: Iterable[PdfSource],
    output_path: str,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> int:
    """Expand page ranges in source order and write the resulting page sequence."""
    source_list = list(sources)
    if not source_list:
        raise ValueError("Agregá al menos un archivo PDF.")

    references: list[PdfPageRef] = []
    # Validate every range before creating a temporary file or touching the target.
    for source in source_list:
        with pikepdf.open(source.path) as input_pdf:
            page_indexes = parse_page_ranges(source.page_ranges, len(input_pdf.pages))
        references.extend(PdfPageRef(source.path, index) for index in page_indexes)

    return combine_pages_in_order(references, output_path, progress_callback)


def combine_pages_in_order(
    pages: Iterable[PdfPageRef],
    output_path: str,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> int:
    """Combine individual PDF pages in the exact supplied order.

    The selected sequence is validated before a temporary output is created.
    The result is reopened and checked before an atomic replacement publishes it.
    Source documents are never modified.
    """
    references = [
        PdfPageRef(str(Path(page.path).expanduser().resolve()), page.page_index)
        for page in pages
    ]
    if not references:
        raise ValueError("Seleccioná al menos una página para crear el PDF.")

    target = Path(output_path).expanduser().resolve()
    if target.suffix.lower() != ".pdf":
        raise ValueError("El archivo de salida debe tener extensión .pdf.")

    input_paths = {Path(page.path).resolve() for page in references}
    if target in input_paths:
        raise ValueError("El archivo de salida no puede reemplazar uno de los PDF originales.")
    if not target.parent.is_dir():
        raise ValueError("La carpeta de destino no existe.")

    # Preflight all paths and page indexes before creating the temporary output.
    page_counts: dict[str, int] = {}
    for page in references:
        if not isinstance(page.page_index, int) or page.page_index < 0:
            raise ValueError("La referencia contiene un número de página inválido.")
        if page.path not in page_counts:
            with pikepdf.open(page.path) as input_pdf:
                count = len(input_pdf.pages)
            if count == 0:
                raise ValueError(f"El PDF «{Path(page.path).name}» no contiene páginas.")
            page_counts[page.path] = count
        if page.page_index >= page_counts[page.path]:
            raise ValueError(
                f"El PDF «{Path(page.path).name}» tiene {page_counts[page.path]} páginas; "
                f"no existe la página {page.page_index + 1}."
            )

    total_pages = len(references)
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{target.stem}_",
        suffix=".tmp.pdf",
        dir=str(target.parent),
        delete=False,
    )
    temp_path = Path(handle.name)
    handle.close()

    exported = 0
    update_step = max(1, total_pages // 100)
    try:
        with pikepdf.Pdf.new() as output_pdf:
            # Interleaving pages from different PDFs is common in the visual
            # organizer. Keep a small LRU cache so A/B/A/B doesn't reopen each
            # source for every page, while bounding open file handles and memory.
            open_documents: OrderedDict[str, object] = OrderedDict()
            try:
                for page in references:
                    input_pdf = open_documents.pop(page.path, None)
                    if input_pdf is None:
                        if len(open_documents) >= MAX_OPEN_SOURCE_PDFS:
                            _oldest_path, oldest_pdf = open_documents.popitem(last=False)
                            oldest_pdf.close()
                        input_pdf = pikepdf.open(page.path)
                    open_documents[page.path] = input_pdf

                    output_pdf.pages.append(input_pdf.pages[page.page_index])
                    exported += 1
                    if progress_callback and (
                        exported % update_step == 0 or exported == total_pages
                    ):
                        progress_callback(
                            exported,
                            total_pages,
                            f"Combinando páginas: {exported:,} de {total_pages:,}…",
                        )
            finally:
                for input_pdf in open_documents.values():
                    input_pdf.close()
            output_pdf.save(str(temp_path))

        with pikepdf.open(str(temp_path)) as verification:
            if len(verification.pages) != total_pages:
                raise RuntimeError(
                    "La comprobación del PDF final no coincide con las páginas seleccionadas."
                )

        os.replace(temp_path, target)
        if progress_callback:
            progress_callback(total_pages, total_pages, "PDF creado correctamente.")
        return total_pages
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
