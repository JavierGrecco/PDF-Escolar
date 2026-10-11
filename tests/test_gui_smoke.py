"""Smoke test for the desktop window on systems with Qt GUI libraries."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QEvent, QSettings
    from PySide6.QtWidgets import QApplication, QLabel, QAbstractItemView, QScrollArea
    from pdf_escolar.pdf_engine import PdfPageRef
    from pdf_escolar.ui.main_window import DocumentCard, DocumentInfo, MainWindow
    from pdf_escolar.ui.page_order import PageOrderDialog
    from pdf_escolar.ui.pdf_tools_dialog import PdfToolsDialog
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


def _dispose_widget(widget, application):
    """Destroy a top-level Qt widget deterministically during test cleanup."""
    widget.close()
    widget.deleteLater()
    application.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    application.processEvents()


def test_main_window_starts_in_a_safe_empty_state(application):
    window = MainWindow()
    try:
        assert window.windowTitle() == "PDF Escolar"
        assert not window.export_button.isEnabled()
        assert "Todavía no agregaste archivos" in window.file_count.text()
    finally:
        _dispose_widget(window, application)

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
        _dispose_widget(card, application)


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
        assert dialog.preview_title.text() == "Página 2 de 3 del PDF final"

        dialog.move_selected_down()
        assert dialog.ordered_pages() == references
        assert dialog.preview_title.text() == "Página 3 de 3 del PDF final"
    finally:
        _dispose_widget(dialog, application)

def test_page_order_tiles_show_final_position_and_original_page(application):
    references = [
        PdfPageRef("/tmp/matematica.pdf", 2),
        PdfPageRef("/tmp/historia.pdf", 4),
    ]
    dialog = PageOrderDialog(references)
    try:
        first = dialog.list_widget.item(0)
        assert first.text() == "01 · matematica.pdf\nPág. original 3"
        assert "Orden final: 1" in first.toolTip()
        assert "Página original: 3" in first.toolTip()

        dialog.list_widget.setCurrentRow(0)
        dialog.move_selected_down()

        first_after_move = dialog.list_widget.item(0)
        assert first_after_move.text() == "01 · historia.pdf\nPág. original 5"
        assert "Orden final: 1" in first_after_move.toolTip()
        assert "historia.pdf" in first_after_move.toolTip()

        dialog._thumbnail_failed(1, "fallo de renderizado")
        assert "Vista previa no disponible" in first_after_move.toolTip()
        dialog.list_widget.setCurrentRow(0)
        dialog.move_selected_down()
        assert "Vista previa no disponible" in first_after_move.toolTip()
        assert "La página sigue incluida en el orden" in first_after_move.toolTip()
    finally:
        _dispose_widget(dialog, application)


def test_page_order_tiles_disambiguate_duplicate_source_filenames(application):
    references = [
        PdfPageRef("/tmp/grupo-a/material.pdf", 0),
        PdfPageRef("/tmp/grupo-b/material.pdf", 1),
    ]
    dialog = PageOrderDialog(references)
    try:
        first_label = dialog.list_widget.item(0).text().splitlines()[0]
        second_label = dialog.list_widget.item(1).text().splitlines()[0]
        assert first_label == "01 · material.pdf · grupo-a"
        assert second_label == "02 · material.pdf · grupo-b"
        assert first_label != second_label
        source_tooltip = dialog.list_widget.item(0).toolTip()
        assert "grupo-a" in source_tooltip
        assert "material.pdf" in source_tooltip
        assert dialog.preview_source.text() == "Origen: material.pdf · grupo-a · página 1"
    finally:
        _dispose_widget(dialog, application)


def test_pdf_tools_content_scrolls_without_hiding_action_buttons(application):
    dialog = PdfToolsDialog()
    try:
        content_scroll = dialog.findChild(QScrollArea, "toolsContentScroll")
        assert content_scroll is not None
        assert content_scroll.widget() is not None
        assert dialog.buttons.parentWidget() is dialog
        assert dialog.run_button.parentWidget() is dialog.buttons
    finally:
        _dispose_widget(dialog, application)


def test_help_menu_includes_third_party_licenses(application):
    window = MainWindow()
    try:
        menu = window.help_button.menu()
        assert menu is not None
        labels = [action.text() for action in menu.actions()]
        assert "Cómo usar" in labels
        assert "Licencias y componentes" in labels
    finally:
        _dispose_widget(window, application)


def test_last_open_directory_uses_a_saved_existing_folder(application, tmp_path):
    settings = QSettings()
    old_value = settings.value("last_open_directory", None)
    settings.setValue("last_open_directory", str(tmp_path))
    window = MainWindow()
    try:
        assert window._last_open_directory() == str(tmp_path)
    finally:
        _dispose_widget(window, application)
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
        _dispose_widget(window, application)


def test_hidden_page_order_dialog_does_not_start_thumbnail_tasks(application):
    dialog = PageOrderDialog([PdfPageRef("/tmp/not-opened.pdf", 0)])
    try:
        application.processEvents()
        assert not dialog.tasks
    finally:
        _dispose_widget(dialog, application)

def test_page_picker_does_not_start_thumbnail_tasks_before_becoming_visible(application):
    from pdf_escolar.ui.page_picker import PagePickerDialog
    dialog = PagePickerDialog("/tmp/not-opened.pdf", 1, "1")
    try:
        application.processEvents()
        assert not dialog.tasks
        assert dialog.pool.activeThreadCount() == 0
    finally:
        dialog.thumbnail_timer.stop()
        for task in tuple(dialog.tasks):
            task.cancel()
        dialog.pool.waitForDone()
        _dispose_widget(dialog, application)


def test_drop_area_compacts_after_loading_files_and_expands_when_empty(application):
    window = MainWindow()
    path = "/tmp/sample.pdf"
    try:
        assert not window.drop_area.title_label.isHidden()
        assert window.drop_area.choose_button.text() == "Seleccionar archivos PDF"

        window._on_loaded(path, 3, 1024)

        assert window.drop_area.title_label.isHidden()
        assert window.drop_area.hint_label.isHidden()
        assert window.drop_area.choose_button.text() == "Agregar más PDF"

        window.remove_file(path)

        assert not window.drop_area.title_label.isHidden()
        assert window.drop_area.choose_button.text() == "Seleccionar archivos PDF"
    finally:
        _dispose_widget(window, application)


def test_load_errors_are_collected_for_one_clear_summary(application):
    window = MainWindow()
    path = "/tmp/protected.pdf"
    try:
        window.pending.add(path)
        window._on_load_error(path, "password required")
        assert path not in window.pending
        assert window.load_errors == [(path, "password required")]
    finally:
        _dispose_widget(window, application)


def test_editing_page_selection_explains_custom_order_reset(application):
    window = MainWindow()
    path = "/tmp/three-pages.pdf"
    try:
        window._on_loaded(path, 3, 1024)
        window.custom_page_order = [
            PdfPageRef(path, 2),
            PdfPageRef(path, 0),
        ]

        card = window.documents[path][1]
        card.ranges.setText("1-2")

        assert window.custom_page_order is None
        assert "orden manual" in window.status.text().lower()
        assert "Ordenar páginas" in window.status.text()
    finally:
        _dispose_widget(window, application)


def test_preview_errors_are_presented_in_spanish_without_library_details(application):
    from pdf_escolar.ui.page_picker import PagePickerDialog

    dialog = PagePickerDialog("/tmp/not-opened.pdf", 1, "1")
    try:
        item = dialog.page_indexes[0]
        dialog._thumbnail_failed(0, "stream ended unexpectedly at offset 123")

        assert "No pudimos mostrar" in item.toolTip()
        assert "stream ended" not in item.toolTip()
    finally:
        dialog.thumbnail_timer.stop()
        for task in tuple(dialog.tasks):
            task.cancel()
        dialog.pool.waitForDone()
        _dispose_widget(dialog, application)


def test_order_preview_errors_are_presented_in_spanish(application):
    dialog = PageOrderDialog([PdfPageRef("/tmp/not-opened.pdf", 0)])
    try:
        item = dialog.items_by_id[0]
        dialog._thumbnail_failed(0, "invalid object at offset 999")

        assert "Vista previa no disponible" in item.toolTip()
        assert "invalid object" not in item.toolTip()
        assert "La página sigue incluida" in item.toolTip()
    finally:
        _dispose_widget(dialog, application)


def test_main_worker_tasks_disable_qrunnable_auto_deletion(application):
    from pdf_escolar.ui.main_window import ExportTask, InspectTask
    inspect_task = InspectTask([])
    export_task = ExportTask([], "/tmp/not-created.pdf")

    assert not inspect_task.autoDelete()
    assert not export_task.autoDelete()


def test_page_picker_keeps_the_current_page_group_responsive(application):
    from pdf_escolar.ui.page_picker import PagePickerDialog
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
        dialog.thumbnail_timer.stop()
        for task in tuple(dialog.tasks):
            task.cancel()
        dialog.pool.waitForDone()
        _dispose_widget(dialog, application)

def test_cancelled_page_picker_thumbnail_task_finishes_without_opening_a_pdf():
    from pdf_escolar.ui.page_picker import ThumbnailTask
    task = ThumbnailTask("/tmp/not-opened.pdf", [0])
    finished = []
    task.signals.finished.connect(finished.append)

    task.cancel()
    task.run()

    assert finished == [str(id(task))]


def test_cancelled_page_order_thumbnail_task_finishes_without_opening_a_pdf():
    from pdf_escolar.ui.page_order import PageOrderThumbnailTask
    task = PageOrderThumbnailTask(
        [(0, PdfPageRef("/tmp/not-opened.pdf", 0))]
    )
    finished = []
    task.signals.finished.connect(finished.append)

    task.cancel()
    task.run()

    assert finished == [str(id(task))]



def test_pdf_tools_dialog_switches_between_native_operations(application):
    from pdf_escolar.ui.pdf_tools_dialog import PdfToolsDialog

    dialog = PdfToolsDialog()
    try:
        assert dialog.operation_selector.currentData() == "rotate"
        assert not dialog.rotate_panel.isHidden()
        assert dialog.crop_panel.isHidden()
        assert dialog.run_button.text() == "Procesar PDF"

        dialog.operation_selector.setCurrentIndex(1)
        assert dialog.operation_selector.currentData() == "crop"
        assert dialog.rotate_panel.isHidden()
        assert not dialog.crop_panel.isHidden()

        dialog.operation_selector.setCurrentIndex(2)
        assert dialog.operation_selector.currentData() == "split"
        assert dialog.rotate_panel.isHidden()
        assert dialog.crop_panel.isHidden()
        assert not dialog.split_note.isHidden()
    finally:
        _dispose_widget(dialog, application)


def test_pdf_tools_dialog_exposes_optional_local_ocr(application):
    from pdf_escolar.ui.pdf_tools_dialog import PdfToolsDialog

    dialog = PdfToolsDialog()
    try:
        ocr_index = dialog.operation_selector.findData("ocr")
        assert ocr_index >= 0
        dialog.operation_selector.setCurrentIndex(ocr_index)
        assert not dialog.ocr_panel.isHidden()
        assert dialog.run_button.text() == "Crear PDF buscable"
        assert dialog.ocr_language.currentData() == ["spa"]
        assert "OCR" in dialog.install_ocr_button.text()
        assert "Tus PDF nunca se suben" in dialog.ocr_panel.findChild(QLabel, "ocrDisclaimer").text()

        split_index = dialog.operation_selector.findData("split")
        dialog.operation_selector.setCurrentIndex(split_index)
        assert dialog.ocr_panel.isHidden()
    finally:
        _dispose_widget(dialog, application)
