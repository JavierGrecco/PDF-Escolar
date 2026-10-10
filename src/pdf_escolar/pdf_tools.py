"""Native PDF editing operations with validation and atomic output replacement."""

from __future__ import annotations

import math
import os
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TypeVar

import pikepdf

POINTS_PER_MM = 72.0 / 25.4
ResultT = TypeVar("ResultT")


def _normalise_pages(page_indexes: Iterable[int], page_count: int) -> list[int]:
    """Validate zero-based page indexes and preserve the supplied order."""
    indexes = list(page_indexes)
    if not indexes:
        raise ValueError("Seleccioná al menos una página.")
    if any(not isinstance(index, int) or isinstance(index, bool) for index in indexes):
        raise ValueError("La selección contiene un número de página inválido.")
    if len(set(indexes)) != len(indexes):
        raise ValueError("La selección contiene páginas repetidas.")
    if any(index < 0 or index >= page_count for index in indexes):
        raise ValueError(f"El PDF tiene {page_count} páginas; revisá la selección.")
    return indexes


def _validated_paths(input_path: str | Path, output_path: str | Path) -> tuple[Path, Path]:
    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError("No encontramos el PDF de origen.")
    if source == target:
        raise ValueError("El resultado debe guardarse en un archivo nuevo; el original no se modifica.")
    if target.suffix.lower() != ".pdf":
        raise ValueError("El archivo de salida debe tener extensión .pdf.")
    if not target.parent.is_dir():
        raise ValueError("La carpeta de destino no existe.")
    return source, target


def _write_pdf_atomically(
    input_path: str | Path,
    output_path: str | Path,
    transform: Callable[[pikepdf.Pdf], ResultT],
) -> ResultT:
    """Transform to a temporary PDF, validate it, and atomically publish it."""
    source, target = _validated_paths(input_path, output_path)
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{target.stem}_",
        suffix=".tmp.pdf",
        dir=str(target.parent),
        delete=False,
    )
    temporary = Path(handle.name)
    handle.close()

    try:
        with pikepdf.open(source) as pdf:
            source_page_count = len(pdf.pages)
            if source_page_count == 0:
                raise ValueError("El PDF no contiene páginas.")
            result = transform(pdf)
            pdf.save(str(temporary))

        with pikepdf.open(temporary) as verified:
            if len(verified.pages) != source_page_count:
                raise ValueError("La cantidad de páginas del resultado no coincide con el original.")
        os.replace(temporary, target)
        return result
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def rotate_pdf_pages(
    input_path: str | Path,
    output_path: str | Path,
    page_indexes: Iterable[int],
    degrees: int,
) -> int:
    """Rotate selected zero-based pages clockwise, saving to a new PDF.

    Accepted angles are +/-90, 180, and +/-270 degrees. The visible page content
    is preserved: this updates the PDF page rotation rather than rasterizing it.
    """
    if not isinstance(degrees, int) or isinstance(degrees, bool) or degrees not in {
        -270, -180, -90, 90, 180, 270
    }:
        raise ValueError("Elegí un giro de 90°, 180° o 270°.")
    delta = degrees % 360
    if delta == 0:
        raise ValueError("El giro debe ser de 90°, 180° o 270°.")

    def transform(pdf: pikepdf.Pdf) -> int:
        selected = _normalise_pages(page_indexes, len(pdf.pages))
        for index in selected:
            pdf.pages[index].rotate(delta, relative=True)
        return len(selected)

    return _write_pdf_atomically(input_path, output_path, transform)


def crop_pdf_pages(
    input_path: str | Path,
    output_path: str | Path,
    page_indexes: Iterable[int],
    *,
    left_mm: float = 0,
    top_mm: float = 0,
    right_mm: float = 0,
    bottom_mm: float = 0,
) -> int:
    """Crop the visible CropBox of selected pages by margins expressed in mm.

    The page's vector/text content is retained. Cropping changes the visible
    page area; it does not irreversibly erase content outside that area.
    """
    margins = {
        "izquierdo": left_mm,
        "superior": top_mm,
        "derecho": right_mm,
        "inferior": bottom_mm,
    }
    for label, value in margins.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"El margen {label} debe ser un número.")
        if not math.isfinite(value) or value < 0:
            raise ValueError("Los márgenes deben ser números positivos o cero.")

    left_pt = float(left_mm) * POINTS_PER_MM
    top_pt = float(top_mm) * POINTS_PER_MM
    right_pt = float(right_mm) * POINTS_PER_MM
    bottom_pt = float(bottom_mm) * POINTS_PER_MM

    if left_pt + right_pt <= 0 and top_pt + bottom_pt <= 0:
        raise ValueError("Indicá al menos un margen para recortar.")

    def transform(pdf: pikepdf.Pdf) -> int:
        selected = _normalise_pages(page_indexes, len(pdf.pages))
        for index in selected:
            page = pdf.pages[index]
            x0, y0, x1, y1 = (float(value) for value in page.cropbox)
            new_box = (
                x0 + left_pt,
                y0 + bottom_pt,
                x1 - right_pt,
                y1 - top_pt,
            )
            if new_box[2] <= new_box[0] or new_box[3] <= new_box[1]:
                raise ValueError(
                    f"Los márgenes dejan sin área visible la página {index + 1}. "
                    "Reducí los valores e intentá nuevamente."
                )
            page.cropbox = pikepdf.Array(new_box)
        return len(selected)

    return _write_pdf_atomically(input_path, output_path, transform)


def split_pdf_by_page(
    input_path: str | Path,
    output_directory: str | Path,
    page_indexes: Iterable[int] | None = None,
) -> list[Path]:
    """Export each selected page as a separate PDF without overwriting files.

    Files are staged first. Existing output names are never overwritten; if the
    operation fails, files created by this run are removed.
    """
    source = Path(input_path).expanduser().resolve()
    destination = Path(output_directory).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError("No encontramos el PDF de origen.")
    if not destination.is_dir():
        raise ValueError("La carpeta de destino no existe.")

    staged_dir: Path | None = None
    reserved: list[Path] = []
    published: list[Path] = []
    try:
        with pikepdf.open(source) as pdf:
            selected = (
                list(range(len(pdf.pages)))
                if page_indexes is None
                else _normalise_pages(page_indexes, len(pdf.pages))
            )
            if not pdf.pages:
                raise ValueError("El PDF no contiene páginas.")
            outputs = [
                destination / f"{source.stem}_pagina_{sequence:03d}.pdf"
                for sequence, _index in enumerate(selected, start=1)
            ]
            if any(path.exists() for path in outputs):
                raise FileExistsError(
                    "Ya existen archivos con esos nombres en la carpeta elegida. "
                    "Elegí otra carpeta para no reemplazarlos."
                )

            staged_dir = Path(
                tempfile.mkdtemp(prefix=".pdf-escolar-split-", dir=str(destination))
            )
            for sequence, index in enumerate(selected, start=1):
                page_pdf = pikepdf.Pdf.new()
                page_pdf.pages.append(pdf.pages[index])
                page_pdf.save(str(staged_dir / f"{sequence:03d}.pdf"))
                page_pdf.close()

        # Reserve names with exclusive creation so a concurrent file is never
        # overwritten by os.replace on POSIX systems.
        for path in outputs:
            with path.open("xb"):
                pass
            reserved.append(path)

        for sequence, path in enumerate(outputs, start=1):
            os.replace(staged_dir / f"{sequence:03d}.pdf", path)
            published.append(path)
        return outputs
    except Exception:
        for path in published + [path for path in reserved if path not in published]:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    finally:
        if staged_dir is not None:
            try:
                for item in staged_dir.iterdir():
                    item.unlink(missing_ok=True)
                staged_dir.rmdir()
            except OSError:
                pass
