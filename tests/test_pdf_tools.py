from __future__ import annotations

from pathlib import Path

import pikepdf
import pytest

from pdf_escolar.pdf_tools import (
    POINTS_PER_MM,
    crop_pdf_pages,
    rotate_pdf_pages,
    split_pdf_by_page,
)


def make_pdf(path: Path, sizes: list[tuple[int, int]]) -> None:
    with pikepdf.Pdf.new() as pdf:
        for width, height in sizes:
            pdf.add_blank_page(page_size=(width, height))
        pdf.save(path)


def boxes(path: Path) -> list[tuple[float, float, float, float]]:
    with pikepdf.open(path) as pdf:
        return [
            tuple(float(value) for value in page.cropbox)
            for page in pdf.pages
        ]


def test_rotate_selected_pages_keeps_unselected_pages_and_original(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    make_pdf(source, [(200, 300), (400, 500), (600, 700)])

    assert rotate_pdf_pages(source, output, [0, 2], 90) == 2

    with pikepdf.open(output) as pdf:
        assert len(pdf.pages) == 3
        assert [page.rotation for page in pdf.pages] == [90, 0, 90]
    with pikepdf.open(source) as pdf:
        assert [page.rotation for page in pdf.pages] == [0, 0, 0]


@pytest.mark.parametrize("degrees", [0, 45, -45, 360, True])
def test_rotate_rejects_invalid_angles_without_output(tmp_path, degrees):
    source = tmp_path / "source.pdf"
    output = tmp_path / "rotated.pdf"
    make_pdf(source, [(200, 300)])

    with pytest.raises(ValueError, match="giro"):
        rotate_pdf_pages(source, output, [0], degrees)

    assert not output.exists()
    assert not list(tmp_path.glob(".rotated_*.tmp.pdf"))


def test_crop_updates_only_selected_crop_boxes_and_preserves_page_count(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "cropped.pdf"
    make_pdf(source, [(200, 300), (400, 500)])

    assert crop_pdf_pages(
        source,
        output,
        [1],
        left_mm=10,
        top_mm=20,
        right_mm=5,
        bottom_mm=4,
    ) == 1

    original = boxes(source)
    cropped = boxes(output)
    assert cropped[0] == original[0]
    assert cropped[1][0] == pytest.approx(original[1][0] + 10 * POINTS_PER_MM)
    assert cropped[1][1] == pytest.approx(original[1][1] + 4 * POINTS_PER_MM)
    assert cropped[1][2] == pytest.approx(original[1][2] - 5 * POINTS_PER_MM)
    assert cropped[1][3] == pytest.approx(original[1][3] - 20 * POINTS_PER_MM)


def test_crop_rejects_margins_that_remove_the_page_and_preserves_existing_output(tmp_path):
    source = tmp_path / "source.pdf"
    output = tmp_path / "existing.pdf"
    make_pdf(source, [(200, 300)])
    make_pdf(output, [(100, 150)])

    with pytest.raises(ValueError, match="sin área visible"):
        crop_pdf_pages(source, output, [0], left_mm=100, right_mm=100)

    assert boxes(output)[0] == (0.0, 0.0, 100.0, 150.0)
    assert not list(tmp_path.glob(".existing_*.tmp.pdf"))


@pytest.mark.parametrize(
    "margins",
    [
        {"left_mm": -1},
        {"top_mm": float("nan")},
        {"right_mm": float("inf")},
        {"bottom_mm": True},
    ],
)
def test_crop_rejects_invalid_margins(tmp_path, margins):
    source = tmp_path / "source.pdf"
    output = tmp_path / "cropped.pdf"
    make_pdf(source, [(200, 300)])

    with pytest.raises(ValueError):
        crop_pdf_pages(source, output, [0], **margins)

    assert not output.exists()


def test_split_exports_selected_pages_in_order_and_keeps_original(tmp_path):
    source = tmp_path / "source.pdf"
    output_dir = tmp_path / "separated"
    output_dir.mkdir()
    make_pdf(source, [(200, 300), (400, 500), (600, 700)])

    outputs = split_pdf_by_page(source, output_dir, [2, 0])

    assert [path.name for path in outputs] == [
        "source_pagina_001.pdf",
        "source_pagina_002.pdf",
    ]
    assert [len(pikepdf.open(path).pages) for path in outputs] == [1, 1]
    assert [boxes(path)[0][2:] for path in outputs] == [(600.0, 700.0), (200.0, 300.0)]
    with pikepdf.open(source) as pdf:
        assert len(pdf.pages) == 3


def test_split_defaults_to_every_page(tmp_path):
    source = tmp_path / "book.pdf"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    make_pdf(source, [(200, 300), (400, 500)])

    outputs = split_pdf_by_page(source, output_dir)

    assert len(outputs) == 2
    assert all(path.is_file() for path in outputs)


def test_split_never_overwrites_existing_files(tmp_path):
    source = tmp_path / "book.pdf"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    existing = output_dir / "book_pagina_001.pdf"
    make_pdf(source, [(200, 300), (400, 500)])
    make_pdf(existing, [(800, 900)])

    with pytest.raises(FileExistsError, match="Ya existen"):
        split_pdf_by_page(source, output_dir)

    assert boxes(existing)[0] == (0.0, 0.0, 800.0, 900.0)
    assert not (output_dir / "book_pagina_002.pdf").exists()
    assert not list(output_dir.glob(".pdf-escolar-split-*"))


def test_invalid_page_indexes_preserve_existing_output(tmp_path):
    source = tmp_path / "book.pdf"
    output = tmp_path / "existing.pdf"
    make_pdf(source, [(200, 300), (400, 500)])
    make_pdf(output, [(800, 900)])

    with pytest.raises(ValueError, match="selección"):
        rotate_pdf_pages(source, output, [4], 90)

    assert boxes(output)[0] == (0.0, 0.0, 800.0, 900.0)


def test_crop_requires_at_least_one_positive_margin(tmp_path):
    source = tmp_path / "book.pdf"
    output = tmp_path / "out.pdf"
    make_pdf(source, [(200, 300)])

    with pytest.raises(ValueError, match="al menos un margen"):
        crop_pdf_pages(source, output, [0])

    assert not output.exists()
