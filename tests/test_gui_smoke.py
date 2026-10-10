"""Smoke test for the desktop window on systems with Qt GUI libraries."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication, QLabel, QAbstractItemView
    from pdf_escolar.pdf_engine import PdfPageRef
    from pdf_escolar.ui.main_window import DocumentCard, DocumentInfo, MainWindow
    from pdf_escolar.ui.page_order import PageOrderDialog
except ImportError as exc:
    # Some Linux runners lack system libraries needed by Qt. Skip only those
    # known runtime-library errors; application import regressions must fail CI.
    detail = str(exc)
    missing_qt_system_library = any(
        library in detail
        for library in (
            "libEGL.so",
            "libGL.so",
            "libxkbcommon.so",
            "libxcb",
            "libX11.so",
            "libXrender.so",
        )
    )
    if sys.platform.startswith("linux") and missing_qt_system_library:
        pytest.skip(
            f"Qt requires a system library unavailable on this Linux runner: {exc}",
            allow_module_level=True,
        )
    raise


@pytest.fixture(scope="session")
def application():
    return QApplication.instance() or QApplication([])


def test_main_window_starts_in_a_safe_empty_state(application):
    window = MainWindow()
    try:
        assert window.windowTitle() == "PDF Escolar"
        assert not window.export_button.isEnabled()
        assert "Todavía no agregaste archivos" in window.file_count.text()
    finally:
        window.close()

def test_document_card_displays_the_full_pdf_name_and_page_count(application):
    card = DocumentCard(
        DocumentInfo("/tmp/Material de matemática - 4.º grado.pdf", 145, 1024 * 1024)
    )
    try:
        card.resize(720, 300)
        card.show()
        application.processEvents()
        name = card.findChild(QLabel, "fileName")
        metadata = card.findChild(QLabel, "fileMetadata")
        assert name is not None
        assert name.text() == "Material de matemática - 4.º grado.pdf"
        assert name.isVisible()
        assert name.width() > 200
        assert metadata is not None
        assert "145 páginas" in metadata.text()
        assert name.wordWrap()
    finally:
        card.close()


def test_page_order_dialog_supports_drag_and_button_reordering(application):
    references = [
        PdfPageRef("/tmp/first.pdf", 0),
        PdfPageRef("/tmp/second.pdf", 2),
        PdfPageRef("/tmp/third.pdf", 1),
    ]
    dialog = PageOrderDialog(references)
    try:
        assert (
            dialog.list_widget.dragDropMode()
            == QAbstractItemView.DragDropMode.InternalMove
        )
        assert dialog.list_widget.acceptDrops()
        dialog.list_widget.setCurrentRow(2)
        dialog.move_selected_up()
        assert dialog.ordered_pages() == [
            references[0],
            references[2],
            references[1],
        ]
    finally:
        dialog.close()

def test_last_open_directory_uses_a_saved_existing_folder(application, tmp_path):
    settings = QSettings()
    old_value = settings.value("last_open_directory", None)
    settings.setValue("last_open_directory", str(tmp_path))
    window = MainWindow()
    try:
        assert window._last_open_directory() == str(tmp_path)
    finally:
        window.close()
        if old_value is None:
            settings.remove("last_open_directory")
        else:
            settings.setValue("last_open_directory", old_value)
