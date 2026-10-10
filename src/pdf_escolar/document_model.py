"""Serializable, non-destructive model for visual document composition.

This module deliberately does not depend on Qt or a PDF engine. It describes
what the user wants to compose; rendering and PDF export live in separate layers.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

PROJECT_SCHEMA_VERSION = 1
MAX_PROJECT_BYTES = 20 * 1024 * 1024
MAX_PAGES = 10_000
MAX_ELEMENTS = 100_000
MAX_HTML_CHARACTERS = 1_000_000
_GEOMETRY_EPSILON = 1e-12


class DocumentModelError(ValueError):
    """A project or geometry value cannot be represented safely."""


def _new_id() -> str:
    return str(uuid.uuid4())


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DocumentModelError(f"{label} debe ser un número.")
    result = float(value)
    if not math.isfinite(result):
        raise DocumentModelError(f"{label} debe ser un número finito.")
    return result


@dataclass(frozen=True, slots=True)
class NormalizedRect:
    """A rectangle in normalized page coordinates, with origin at top-left.

    Coordinates range from 0 to 1 regardless of the source page's physical
    dimensions. The same representation is used for source clipping and for
    placing an element on a composition page; the containing field determines
    which page its coordinates refer to.
    """

    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        values = {
            "left": _finite_number(self.left, "El borde izquierdo"),
            "top": _finite_number(self.top, "El borde superior"),
            "right": _finite_number(self.right, "El borde derecho"),
            "bottom": _finite_number(self.bottom, "El borde inferior"),
        }
        if any(value < 0 or value > 1 for value in values.values()):
            raise DocumentModelError("Las coordenadas deben estar entre 0 y 1.")
        if values["right"] - values["left"] <= _GEOMETRY_EPSILON:
            raise DocumentModelError("La selección debe tener ancho mayor que cero.")
        if values["bottom"] - values["top"] <= _GEOMETRY_EPSILON:
            raise DocumentModelError("La selección debe tener alto mayor que cero.")
        for name, value in values.items():
            object.__setattr__(self, name, value)

    @classmethod
    def full_page(cls) -> NormalizedRect:
        return cls(0.0, 0.0, 1.0, 1.0)

    @classmethod
    def from_xywh(
        cls, x: float, y: float, width: float, height: float
    ) -> NormalizedRect:
        """Create a rectangle from top-left coordinates and size."""
        return cls(x, y, x + width, y + height)

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def area(self) -> float:
        return self.width * self.height

    def intersection(self, other: NormalizedRect) -> NormalizedRect | None:
        left = max(self.left, other.left)
        top = max(self.top, other.top)
        right = min(self.right, other.right)
        bottom = min(self.bottom, other.bottom)
        if (
            right - left <= _GEOMETRY_EPSILON
            or bottom - top <= _GEOMETRY_EPSILON
        ):
            return None
        return NormalizedRect(left, top, right, bottom)

    def subtract(self, cut: NormalizedRect) -> tuple[NormalizedRect, ...]:
        """Return non-overlapping rectangles that cover this rect minus cut.

        The cut is clipped to this rectangle. The result contains zero to four
        rectangles, ordered top, bottom, left, right. A non-intersecting cut
        leaves the original rectangle unchanged.
        """
        overlap = self.intersection(cut)
        if overlap is None:
            return (self,)

        pieces: list[NormalizedRect] = []
        candidates = (
            (self.left, self.top, self.right, overlap.top),
            (self.left, overlap.bottom, self.right, self.bottom),
            (self.left, overlap.top, overlap.left, overlap.bottom),
            (overlap.right, overlap.top, self.right, overlap.bottom),
        )
        for left, top, right, bottom in candidates:
            if (
                right - left > _GEOMETRY_EPSILON
                and bottom - top > _GEOMETRY_EPSILON
            ):
                pieces.append(NormalizedRect(left, top, right, bottom))
        return tuple(pieces)

    def to_dict(self) -> dict[str, float]:
        return {
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
        }

    @classmethod
    def from_dict(cls, value: object) -> NormalizedRect:
        if not isinstance(value, dict):
            raise DocumentModelError("El rectángulo del proyecto no es válido.")
        try:
            return cls(
                left=value["left"],
                top=value["top"],
                right=value["right"],
                bottom=value["bottom"],
            )
        except KeyError as exc:
            raise DocumentModelError("Faltan coordenadas en un rectángulo.") from exc


def subtract_rectangles(
    source_region: NormalizedRect,
    cuts: list[NormalizedRect] | tuple[NormalizedRect, ...],
) -> tuple[NormalizedRect, ...]:
    """Subtract many independent rectangular exclusions from a source region.

    Every cut is applied to the current fragments. This is useful for the
    future «quitar esta zona y juntar las partes restantes» workflow: the user
    can mark several areas to omit without having to select all the content
    they want to keep.
    """
    remaining: tuple[NormalizedRect, ...] = (source_region,)
    for cut in cuts:
        next_regions: list[NormalizedRect] = []
        for region in remaining:
            next_regions.extend(region.subtract(cut))
        remaining = tuple(next_regions)
        if not remaining:
            break
    return remaining


def _normalise_rotation(value: object) -> float:
    angle = _finite_number(value, "El ángulo de giro")
    # Store one canonical representation so 360° and 0° serialize identically.
    normalised = angle % 360.0
    if math.isclose(normalised, 360.0, abs_tol=_GEOMETRY_EPSILON):
        return 0.0
    if math.isclose(normalised, 0.0, abs_tol=_GEOMETRY_EPSILON):
        return 0.0
    return normalised


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """A PDF file referenced by a project, not copied into the project file."""

    path: str
    source_id: str = field(default_factory=_new_id)
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path.strip():
            raise DocumentModelError("Cada PDF fuente necesita una ruta.")
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise DocumentModelError("Cada PDF fuente necesita un identificador.")
        if self.sha256 is not None:
            if not isinstance(self.sha256, str):
                raise DocumentModelError("La huella SHA-256 de una fuente no es válida.")
            digest = self.sha256.lower()
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise DocumentModelError("La huella SHA-256 de una fuente no es válida.")
            object.__setattr__(self, "sha256", digest)

    def resolve_path(self, project_file: str | Path) -> Path:
        """Resolve a stored relative source path against the project folder."""
        source = Path(self.path).expanduser()
        if not source.is_absolute():
            source = Path(project_file).expanduser().resolve().parent / source
        return source.resolve()

    def to_dict(self) -> dict[str, object]:
        return {"source_id": self.source_id, "path": self.path, "sha256": self.sha256}

    @classmethod
    def from_dict(cls, value: object) -> SourceDocument:
        if not isinstance(value, dict):
            raise DocumentModelError("Una fuente del proyecto no es válida.")
        try:
            return cls(
                path=value["path"],
                source_id=value.get("source_id", _new_id()),
                sha256=value.get("sha256"),
            )
        except KeyError as exc:
            raise DocumentModelError("Falta la ruta de una fuente.") from exc


@dataclass(frozen=True, slots=True)
class PdfFragment:
    """A placed excerpt of a source PDF page."""

    source_id: str
    page_index: int
    source_region: NormalizedRect = field(default_factory=NormalizedRect.full_page)
    bounds: NormalizedRect = field(default_factory=NormalizedRect.full_page)
    rotation_degrees: float = 0.0
    element_id: str = field(default_factory=_new_id)
    label: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise DocumentModelError("Un fragmento debe apuntar a un PDF fuente.")
        if (
            not isinstance(self.page_index, int)
            or isinstance(self.page_index, bool)
            or self.page_index < 0
        ):
            raise DocumentModelError("El número de página de un fragmento no es válido.")
        if not isinstance(self.element_id, str) or not self.element_id.strip():
            raise DocumentModelError("Cada fragmento necesita un identificador.")
        if not isinstance(self.label, str):
            raise DocumentModelError("El nombre del fragmento debe ser texto.")
        object.__setattr__(
            self, "rotation_degrees", _normalise_rotation(self.rotation_degrees)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "pdf_fragment",
            "element_id": self.element_id,
            "source_id": self.source_id,
            "page_index": self.page_index,
            "source_region": self.source_region.to_dict(),
            "bounds": self.bounds.to_dict(),
            "rotation_degrees": self.rotation_degrees,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, value: object) -> PdfFragment:
        if not isinstance(value, dict) or value.get("type") != "pdf_fragment":
            raise DocumentModelError("Un fragmento PDF del proyecto no es válido.")
        try:
            return cls(
                element_id=value.get("element_id", _new_id()),
                source_id=value["source_id"],
                page_index=value["page_index"],
                source_region=NormalizedRect.from_dict(value.get("source_region")),
                bounds=NormalizedRect.from_dict(value.get("bounds")),
                rotation_degrees=value.get("rotation_degrees", 0.0),
                label=value.get("label", ""),
            )
        except KeyError as exc:
            raise DocumentModelError("Faltan datos de un fragmento PDF.") from exc


@dataclass(frozen=True, slots=True)
class TextElement:
    """An editable rich-text block; rendering is performed by the Qt layer."""

    html: str = ""
    bounds: NormalizedRect = field(default_factory=NormalizedRect.full_page)
    rotation_degrees: float = 0.0
    element_id: str = field(default_factory=_new_id)
    label: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.html, str):
            raise DocumentModelError("El contenido de texto debe ser una cadena.")
        if len(self.html) > MAX_HTML_CHARACTERS:
            raise DocumentModelError("El bloque de texto supera el tamaño admitido.")
        if not isinstance(self.element_id, str) or not self.element_id.strip():
            raise DocumentModelError("Cada bloque de texto necesita un identificador.")
        if not isinstance(self.label, str):
            raise DocumentModelError("El nombre del bloque debe ser texto.")
        object.__setattr__(
            self, "rotation_degrees", _normalise_rotation(self.rotation_degrees)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "type": "text",
            "element_id": self.element_id,
            "html": self.html,
            "bounds": self.bounds.to_dict(),
            "rotation_degrees": self.rotation_degrees,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, value: object) -> TextElement:
        if not isinstance(value, dict) or value.get("type") != "text":
            raise DocumentModelError("Un bloque de texto del proyecto no es válido.")
        try:
            return cls(
                element_id=value.get("element_id", _new_id()),
                html=value.get("html", ""),
                bounds=NormalizedRect.from_dict(value.get("bounds")),
                rotation_degrees=value.get("rotation_degrees", 0.0),
                label=value.get("label", ""),
            )
        except KeyError as exc:
            raise DocumentModelError("Faltan datos de un bloque de texto.") from exc


CompositionElement: TypeAlias = PdfFragment | TextElement


@dataclass(frozen=True, slots=True)
class CompositionPage:
    """One output page; several fragments and text blocks can share its canvas."""

    elements: tuple[CompositionElement, ...] = ()
    width_mm: float = 210.0
    height_mm: float = 297.0
    page_id: str = field(default_factory=_new_id)
    label: str = ""

    def __post_init__(self) -> None:
        width = _finite_number(self.width_mm, "El ancho de página")
        height = _finite_number(self.height_mm, "El alto de página")
        if width < 25 or width > 2_000 or height < 25 or height > 2_000:
            raise DocumentModelError("El tamaño de página debe estar entre 25 y 2000 mm.")
        if not isinstance(self.page_id, str) or not self.page_id.strip():
            raise DocumentModelError("Cada página de composición necesita un identificador.")
        if not isinstance(self.label, str):
            raise DocumentModelError("El nombre de la página debe ser texto.")
        elements = tuple(self.elements)
        if not all(isinstance(item, (PdfFragment, TextElement)) for item in elements):
            raise DocumentModelError("La página contiene un elemento no compatible.")
        object.__setattr__(self, "width_mm", width)
        object.__setattr__(self, "height_mm", height)
        object.__setattr__(self, "elements", elements)

    def to_dict(self) -> dict[str, object]:
        return {
            "page_id": self.page_id,
            "label": self.label,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "elements": [element.to_dict() for element in self.elements],
        }

    @classmethod
    def from_dict(cls, value: object) -> CompositionPage:
        if not isinstance(value, dict):
            raise DocumentModelError("Una página de composición no es válida.")
        try:
            raw_elements = value.get("elements", [])
            if not isinstance(raw_elements, list):
                raise DocumentModelError("La lista de elementos de una página no es válida.")
            elements: list[CompositionElement] = []
            for item in raw_elements:
                if not isinstance(item, dict):
                    raise DocumentModelError("Un elemento de página no es válido.")
                element_type = item.get("type")
                if element_type == "pdf_fragment":
                    elements.append(PdfFragment.from_dict(item))
                elif element_type == "text":
                    elements.append(TextElement.from_dict(item))
                else:
                    raise DocumentModelError("El proyecto contiene un tipo de elemento desconocido.")
            return cls(
                page_id=value.get("page_id", _new_id()),
                label=value.get("label", ""),
                width_mm=value.get("width_mm", 210.0),
                height_mm=value.get("height_mm", 297.0),
                elements=tuple(elements),
            )
        except KeyError as exc:
            raise DocumentModelError("Faltan datos de una página de composición.") from exc


@dataclass(frozen=True, slots=True)
class DocumentProject:
    """Editable project manifest, separate from the exported PDF."""

    title: str
    sources: tuple[SourceDocument, ...] = ()
    pages: tuple[CompositionPage, ...] = ()
    schema_version: int = PROJECT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title.strip():
            raise DocumentModelError("El proyecto necesita un título.")
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != PROJECT_SCHEMA_VERSION
        ):
            raise DocumentModelError(
                f"La versión de proyecto {self.schema_version!r} no es compatible."
            )
        sources = tuple(self.sources)
        pages = tuple(self.pages)
        if len(sources) > MAX_ELEMENTS:
            raise DocumentModelError("El proyecto contiene demasiadas fuentes.")
        if len(pages) > MAX_PAGES:
            raise DocumentModelError("El proyecto contiene demasiadas páginas.")
        if not all(isinstance(item, SourceDocument) for item in sources):
            raise DocumentModelError("La lista de fuentes contiene datos no válidos.")
        if not all(isinstance(item, CompositionPage) for item in pages):
            raise DocumentModelError("La lista de páginas contiene datos no válidos.")

        source_ids = [source.source_id for source in sources]
        if len(source_ids) != len(set(source_ids)):
            raise DocumentModelError("El proyecto contiene identificadores de fuente repetidos.")
        page_ids = [page.page_id for page in pages]
        if len(page_ids) != len(set(page_ids)):
            raise DocumentModelError("El proyecto contiene identificadores de página repetidos.")

        element_ids: list[str] = []
        element_count = 0
        known_source_ids = set(source_ids)
        for page in pages:
            for element in page.elements:
                element_count += 1
                element_ids.append(element.element_id)
                if isinstance(element, PdfFragment) and element.source_id not in known_source_ids:
                    raise DocumentModelError(
                        "Un fragmento refiere a un PDF fuente que no está registrado en el proyecto."
                    )
        if element_count > MAX_ELEMENTS:
            raise DocumentModelError("El proyecto contiene demasiados elementos.")
        if len(element_ids) != len(set(element_ids)):
            raise DocumentModelError("El proyecto contiene identificadores de elemento repetidos.")

        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "pages", pages)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "title": self.title,
            "sources": [source.to_dict() for source in self.sources],
            "pages": [page.to_dict() for page in self.pages],
        }

    @classmethod
    def from_dict(cls, value: object) -> DocumentProject:
        if not isinstance(value, dict):
            raise DocumentModelError("El archivo de proyecto no contiene un objeto válido.")
        try:
            schema_version = value.get("schema_version", PROJECT_SCHEMA_VERSION)
            if schema_version != PROJECT_SCHEMA_VERSION:
                raise DocumentModelError(
                    f"La versión de proyecto {schema_version!r} no es compatible."
                )
            raw_sources = value.get("sources", [])
            raw_pages = value.get("pages", [])
            if not isinstance(raw_sources, list) or not isinstance(raw_pages, list):
                raise DocumentModelError("Las fuentes o páginas del proyecto no son válidas.")
            if len(raw_sources) > MAX_ELEMENTS or len(raw_pages) > MAX_PAGES:
                raise DocumentModelError("El archivo de proyecto supera los límites admitidos.")
            return cls(
                title=value["title"],
                sources=tuple(SourceDocument.from_dict(item) for item in raw_sources),
                pages=tuple(CompositionPage.from_dict(item) for item in raw_pages),
                schema_version=schema_version,
            )
        except KeyError as exc:
            raise DocumentModelError("Faltan datos obligatorios del proyecto.") from exc

    def save(self, project_path: str | Path) -> Path:
        """Save atomically without overwriting a source PDF."""
        target = Path(project_path).expanduser().resolve()
        if target.suffix.lower() != ".pdfescolar":
            raise DocumentModelError("El proyecto debe guardarse con extensión .pdfescolar.")
        if not target.parent.is_dir():
            raise DocumentModelError("La carpeta donde guardar el proyecto no existe.")

        payload = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ).encode("utf-8")
        if len(payload) > MAX_PROJECT_BYTES:
            raise DocumentModelError("El archivo de proyecto supera el tamaño admitido.")

        handle = tempfile.NamedTemporaryFile(
            prefix=f".{target.stem}_",
            suffix=".tmp",
            dir=str(target.parent),
            delete=False,
        )
        temporary = Path(handle.name)
        try:
            with handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            # Validate exactly the bytes that will be installed before publishing.
            loaded = self._load_file(temporary)
            if loaded != self:
                raise DocumentModelError("La comprobación del proyecto guardado no coincide.")
            os.replace(temporary, target)
            return target
        except Exception:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    @classmethod
    def _load_file(cls, path: Path) -> DocumentProject:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise DocumentModelError("No pudimos leer el archivo de proyecto.") from exc
        if len(raw) > MAX_PROJECT_BYTES:
            raise DocumentModelError("El archivo de proyecto supera el tamaño admitido.")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DocumentModelError("El archivo de proyecto no es un JSON válido.") from exc
        return cls.from_dict(value)

    @classmethod
    def load(cls, project_path: str | Path) -> DocumentProject:
        """Load a project with size and schema validation."""
        path = Path(project_path).expanduser()
        if not path.is_file():
            raise DocumentModelError("No encontramos el archivo de proyecto.")
        return cls._load_file(path)


__all__ = [
    "CompositionElement",
    "CompositionPage",
    "DocumentModelError",
    "DocumentProject",
    "NormalizedRect",
    "PdfFragment",
    "SourceDocument",
    "TextElement",
    "subtract_rectangles",
]
