from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdf_escolar.document_model import (
    CompositionPage,
    DocumentModelError,
    DocumentProject,
    NormalizedRect,
    PdfFragment,
    SourceDocument,
    TextElement,
    subtract_rectangles,
)


def assert_non_overlapping(rectangles: tuple[NormalizedRect, ...]) -> None:
    for index, first in enumerate(rectangles):
        for second in rectangles[index + 1 :]:
            assert first.intersection(second) is None


def test_subtract_rectangle_cuts_hole_into_four_non_overlapping_fragments():
    page = NormalizedRect.full_page()
    cut = NormalizedRect(0.25, 0.25, 0.75, 0.75)

    result = page.subtract(cut)

    assert len(result) == 4
    assert sum(rect.area for rect in result) == pytest.approx(0.75)
    assert_non_overlapping(result)
    assert result == (
        NormalizedRect(0, 0, 1, 0.25),
        NormalizedRect(0, 0.75, 1, 1),
        NormalizedRect(0, 0.25, 0.25, 0.75),
        NormalizedRect(0.75, 0.25, 1, 0.75),
    )


def test_subtract_rectangles_can_exclude_multiple_regions_without_overlap():
    page = NormalizedRect.full_page()
    cuts = (
        NormalizedRect(0.1, 0.1, 0.3, 0.3),
        NormalizedRect(0.6, 0.5, 0.9, 0.9),
    )

    result = subtract_rectangles(page, cuts)

    assert sum(rect.area for rect in result) == pytest.approx(
        1.0 - 0.2 * 0.2 - 0.3 * 0.4
    )
    assert_non_overlapping(result)


def test_subtract_non_intersecting_rectangle_leaves_source_unchanged():
    source = NormalizedRect(0.0, 0.0, 0.25, 0.25)
    cut = NormalizedRect(0.75, 0.75, 1.0, 1.0)

    assert source.subtract(cut) == (source,)
    assert subtract_rectangles(source, [cut]) == (source,)


def test_subtract_full_coverage_returns_no_remaining_regions():
    source = NormalizedRect(0.2, 0.2, 0.8, 0.8)
    cut = NormalizedRect.full_page()

    assert source.subtract(cut) == ()
    assert subtract_rectangles(source, [cut]) == ()


@pytest.mark.parametrize(
    "values",
    [
        (-0.1, 0, 1, 1),
        (0, -0.1, 1, 1),
        (0, 0, 1.1, 1),
        (0, 0, 1, float("nan")),
        (0.4, 0, 0.4, 1),
        (0, 0.8, 1, 0.2),
        (False, 0, 1, 1),
    ],
)
def test_normalized_rectangle_rejects_invalid_coordinates(values):
    with pytest.raises(DocumentModelError):
        NormalizedRect(*values)


def make_project() -> DocumentProject:
    source = SourceDocument(path="fuentes/matematica.pdf", source_id="source-1")
    fragment = PdfFragment(
        source_id=source.source_id,
        page_index=3,
        source_region=NormalizedRect(0.1, 0.2, 0.8, 0.9),
        bounds=NormalizedRect(0.0, 0.0, 0.6, 0.8),
        rotation_degrees=-90,
        element_id="fragment-1",
        label="Ejercicio de fracciones",
    )
    text = TextElement(
        html="<h1>Consigna</h1><p><b>Resolvé</b> los ejercicios.</p>",
        bounds=NormalizedRect(0.1, 0.82, 0.9, 0.98),
        element_id="text-1",
        label="Consigna de la docente",
    )
    page = CompositionPage(
        elements=(fragment, text),
        width_mm=210,
        height_mm=297,
        page_id="page-1",
        label="Actividad 1",
    )
    return DocumentProject(
        title="Trabajo práctico de Matemática",
        sources=(source,),
        pages=(page,),
    )


def test_rotation_is_normalized_for_stable_project_serialization():
    source = SourceDocument(path="/tmp/source.pdf", source_id="src")
    a = PdfFragment(source_id="src", page_index=0, rotation_degrees=-90)
    b = PdfFragment(source_id="src", page_index=0, rotation_degrees=270)
    c = PdfFragment(source_id="src", page_index=0, rotation_degrees=360)

    assert a.rotation_degrees == 270
    assert a.rotation_degrees == b.rotation_degrees
    assert c.rotation_degrees == 0


def test_project_round_trip_preserves_fragments_text_and_order():
    project = make_project()

    loaded = DocumentProject.from_dict(project.to_dict())

    assert loaded == project
    assert isinstance(loaded.pages[0].elements[0], PdfFragment)
    assert isinstance(loaded.pages[0].elements[1], TextElement)
    assert loaded.pages[0].elements[0].label == "Ejercicio de fracciones"
    assert loaded.pages[0].elements[1].html.startswith("<h1>Consigna</h1>")


def test_project_rejects_fragments_that_reference_unknown_sources():
    page = CompositionPage(
        elements=(PdfFragment(source_id="missing-source", page_index=0),)
    )

    with pytest.raises(DocumentModelError, match="no está registrado"):
        DocumentProject(title="Incompleto", pages=(page,))


def test_project_rejects_duplicate_identifiers():
    source = SourceDocument(path="/tmp/source.pdf", source_id="source-1")
    one = PdfFragment(source_id="source-1", page_index=0, element_id="duplicate")
    two = TextElement(element_id="duplicate", html="Texto")
    page = CompositionPage(elements=(one, two))

    with pytest.raises(DocumentModelError, match="identificadores de elemento repetidos"):
        DocumentProject(title="Duplicado", sources=(source,), pages=(page,))


def test_project_save_and_load_round_trip_is_atomic(tmp_path):
    project = make_project()
    path = tmp_path / "trabajo.pdfescolar"

    assert project.save(path) == path.resolve()
    assert DocumentProject.load(path) == project
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1
    assert not list(tmp_path.glob(".*.tmp"))


def test_project_save_requires_project_extension(tmp_path):
    with pytest.raises(DocumentModelError, match="extensión .pdfescolar"):
        make_project().save(tmp_path / "trabajo.pdf")


def test_project_load_rejects_malformed_json(tmp_path):
    path = tmp_path / "corrupto.pdfescolar"
    path.write_text("{esto no es json", encoding="utf-8")

    with pytest.raises(DocumentModelError, match="JSON válido"):
        DocumentProject.load(path)


def test_source_paths_resolve_relative_to_the_project_file(tmp_path):
    project_path = tmp_path / "proyecto" / "trabajo.pdfescolar"
    source = SourceDocument(path="../fuentes/original.pdf", source_id="source-1")

    assert source.resolve_path(project_path) == (tmp_path / "fuentes" / "original.pdf").resolve()


def test_project_save_never_replaces_existing_file_if_atomic_publish_fails(
    tmp_path, monkeypatch
):
    import pdf_escolar.document_model as document_model

    path = tmp_path / "trabajo.pdfescolar"
    path.write_text("proyecto anterior", encoding="utf-8")
    original_replace = document_model.os.replace

    def fail_replace(_source, _target):
        raise OSError("simulated write failure")

    monkeypatch.setattr(document_model.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated write failure"):
        make_project().save(path)

    monkeypatch.setattr(document_model.os, "replace", original_replace)
    assert path.read_text(encoding="utf-8") == "proyecto anterior"
    assert not list(tmp_path.glob(".*.tmp"))


def test_project_rejects_unknown_schema_version():
    payload = make_project().to_dict()
    payload["schema_version"] = 999

    with pytest.raises(DocumentModelError, match="no es compatible"):
        DocumentProject.from_dict(payload)
