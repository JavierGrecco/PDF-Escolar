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
    from pdf_escolar.ui.main_window import (
        DocumentCard, DocumentInfo, ExportTask, InspectTask, MainWindow
    )
    from pdf_escolar.ui.page_order import PageOrderDialog, PageOrderThumbnailTask
    from pdf_escolar.ui.page_picker import PagePickerDialog, ThumbnailTask
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
    app = QApplication.instance() or QApplication([])
    app.setOrganizationName("PDF Escolar")
    app.setApplicationName("PDF Escolar")
    return app


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

def test_document_cards_can_be_reordered_by_drop_and_buttons(application):
    window = MainWindow()
    paths = ["/tmp/order-a.pdf", "/tmp/order-b.pdf", "/tmp/order-c.pdf"]
    try:
        for page_count, path in enumerate(paths, start=1):
            window._on_loaded(path, page_count, 1024)

        window.reorder_file_by_drop(paths[0], paths[2], False)
        assert list(window.documents) == [paths[1], paths[0], paths[2]]

        window.move_file(paths[2], -1)
        assert list(window.documents) == [paths[1], paths[2], paths[0]]
    finally:
        window.close()


def test_hidden_page_order_dialog_does_not_start_thumbnail_tasks(application):
    dialog = PageOrderDialog([PdfPageRef("/tmp/not-opened.pdf", 0)])
    try:
        application.processEvents()
        assert not dialog.tasks
    finally:
        dialog.close()

def test_page_picker_does_not_start_thumbnail_tasks_before_becoming_visible(application):
    dialog = PagePickerDialog("/tmp/not-opened.pdf", 1, "1")
    try:
        application.processEvents()
        assert not dialog.tasks
        assert dialog.pool.activeThreadCount() == 0
    finally:
        dialog.close()
        dialog.pool.waitForDone()


def test_main_worker_tasks_disable_qrunnable_auto_deletion(application):
    inspect_task = InspectTask([])
    export_task = ExportTask([], "/tmp/not-created.pdf")

    assert not inspect_task.autoDelete()
    assert not export_task.autoDelete()


def test_page_picker_keeps_the_current_page_group_responsive(application):
    dialog = PagePickerDialog("/tmp/not-opened.pdf", 65, "1, 35")
    try:
        assert dialog.next_button.isEnabled()
        dialog.next_page()
        assert dialog.page_start == 30
        assert dialog.page_label.text() == "Páginas 31–60 de 65"
        assert not dialog.tasks
        dialog.previous_page()
        assert dialog.page_start == 0
        assert dialog.selected_pages == {0, 34}
    finally:
        dialog.close()
        dialog.pool.waitForDone()

def test_cancelled_page_picker_thumbnail_task_finishes_without_opening_a_pdf():
    task = ThumbnailTask("/tmp/not-opened.pdf", [0])
    finished = []
    task.signals.finished.connect(finished.append)

    task.cancel()
    task.run()

    assert finished == [str(id(task))]


def test_cancelled_page_order_thumbnail_task_finishes_without_opening_a_pdf():
    task = PageOrderThumbnailTask(
        [(0, PdfPageRef("/tmp/not-opened.pdf", 0))]
    )
    finished = []
    task.signals.finished.connect(finished.append)

    task.cancel()
    task.run()

    assert finished == [str(id(task))]
