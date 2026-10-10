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
    path: str
    page_ranges: str


def inspect_pdf(path: str) -> int:
    with pikepdf.open(path) as pdf:
        return len(pdf.pages)


def combine_selected_pages(
    sources: Iterable[PdfSource],
    output_path: str,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> int:
    """Combine chosen pages, validate a temporary PDF, then publish it."""
    source_list = list(sources)
    if not source_list:
        raise ValueError("Agregá al menos un archivo PDF.")
    target = Path(output_path).expanduser().resolve()
    if target.suffix.lower() != ".pdf":
        raise ValueError("El archivo de salida debe tener extensión .pdf.")
    input_paths = {Path(s.path).expanduser().resolve() for s in source_list}
    if target in input_paths:
        raise ValueError("El archivo de salida no puede reemplazar uno de los PDF originales.")
    if not target.parent.is_dir():
        raise ValueError("La carpeta de destino no existe.")

    handle = tempfile.NamedTemporaryFile(
        prefix=f".{target.stem}_", suffix=".tmp.pdf",
        dir=str(target.parent), delete=False
    )
    temp_path = Path(handle.name)
    handle.close()
    exported = 0
    try:
        with pikepdf.Pdf.new() as output_pdf:
            for index, source in enumerate(source_list, start=1):
                if progress_callback:
                    progress_callback(index - 1, len(source_list), f"Procesando {Path(source.path).name}…")
                with pikepdf.open(source.path) as input_pdf:
                    indexes = parse_page_ranges(source.page_ranges, len(input_pdf.pages))
                    for page_index in indexes:
                        output_pdf.pages.append(input_pdf.pages[page_index])
                        exported += 1
            if exported == 0:
                raise ValueError("La selección no contiene páginas para exportar.")
            output_pdf.save(str(temp_path))
        with pikepdf.open(str(temp_path)) as verification:
            if len(verification.pages) != exported:
                raise RuntimeError("La comprobación del PDF final no coincide con la selección.")
        os.replace(temp_path, target)
        if progress_callback:
            progress_callback(len(source_list), len(source_list), "PDF creado correctamente.")
        return exported
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
