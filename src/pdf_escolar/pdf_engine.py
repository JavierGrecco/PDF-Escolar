"""PDF operations kept separate from the graphical interface."""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import pikepdf

from pdf_escolar.page_ranges import parse_page_ranges


@dataclass(frozen=True)
class PdfSource:
    """One source PDF and its one-based page selection."""

    path: str
    page_ranges: str


def inspect_pdf(path: str) -> int:
    """Open a PDF and return its number of pages."""
    with pikepdf.open(path) as pdf:
        return len(pdf.pages)


def combine_selected_pages(
    sources: Iterable[PdfSource],
    output_path: str,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> int:
    """Combine selections into a verified temporary PDF before publishing it.

    Every selection is validated before writing starts. Input documents are
    opened one at a time; the original files are never modified. Output is
    atomically moved into the destination only after it can be reopened and
    its page count matches the planned export.
    """
    source_list = list(sources)
    if not source_list:
        raise ValueError("Agregá al menos un archivo PDF.")

    target = Path(output_path).expanduser().resolve()
    if target.suffix.lower() != ".pdf":
        raise ValueError("El archivo de salida debe tener extensión .pdf.")

    input_paths = {Path(source.path).expanduser().resolve() for source in source_list}
    if target in input_paths:
        raise ValueError("El archivo de salida no puede reemplazar uno de los PDF originales.")
    if not target.parent.is_dir():
        raise ValueError("La carpeta de destino no existe.")

    # Preflight makes range errors fail before a temporary output is created.
    plan: list[tuple[PdfSource, list[int]]] = []
    total_pages = 0
    for source in source_list:
        with pikepdf.open(source.path) as input_pdf:
            page_indexes = parse_page_ranges(source.page_ranges, len(input_pdf.pages))
        plan.append((source, page_indexes))
        total_pages += len(page_indexes)

    if total_pages == 0:
        raise ValueError("La selección no contiene páginas para exportar.")

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
            for source, page_indexes in plan:
                with pikepdf.open(source.path) as input_pdf:
                    for page_index in page_indexes:
                        output_pdf.pages.append(input_pdf.pages[page_index])
                        exported += 1
                        if progress_callback and (
                            exported % update_step == 0 or exported == total_pages
                        ):
                            progress_callback(
                                exported,
                                total_pages,
                                f"Combinando páginas: {exported:,} de {total_pages:,}…",
                            )
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
