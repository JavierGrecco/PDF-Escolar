"""Paginated, thumbnail-based page picker for large PDFs."""
from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium
from PySide6.QtCore import QObject, QRunnable, QSize, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListView, QListWidget, QListWidgetItem,
    QProgressBar, QPushButton, QVBoxLayout, QWidget, QMessageBox
)

from pdf_escolar.page_ranges import format_page_ranges, parse_page_ranges
from pdf_escolar.pdf_preview import render_page_thumbnail


PAGES_PER_VIEW = 30


class ThumbnailSignals(QObject):
    ready = Signal(int, bytes)
    failed = Signal(int, str)
    finished = Signal(int)


class ThumbnailTask(QRunnable):
    """Render only the visible page batch, off the GUI thread."""

    def __init__(self, pdf_path: str, page_indexes: list[int]):
        super().__init__()
        self.pdf_path = pdf_path
        self.page_indexes = page_indexes
        self.signals = ThumbnailSignals()

    @Slot()
    def run(self) -> None:
        document = None
        try:
            document = pdfium.PdfDocument(self.pdf_path)
            for page_index in self.page_indexes:
                try:
                    self.signals.ready.emit(page_index, render_page_thumbnail(document, page_index))
                except Exception as exc:
                    self.signals.failed.emit(page_index, str(exc))
        except Exception as exc:
            for page_index in self.page_indexes:
                self.signals.failed.emit(page_index, str(exc))
        finally:
            try:
                if document is not None:
                    document.close()
            finally:
                self.signals.finished.emit(id(self))


class PagePickerDialog(QDialog):
    """Select pages visually, rendering only 30 thumbnails at a time."""

    def __init__(
        self,
        pdf_path: str,
        total_pages: int,
        current_ranges: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.total_pages = total_pages
        self.page_start = 0
        self.page_indexes: dict[int, QListWidgetItem] = {}
        self.tasks: set[QRunnable] = set()
        self.pool = QThreadPool(self)
        self.current_task_id: int | None = None
        self.thumbnail_timer = QTimer(self)
        self.thumbnail_timer.setSingleShot(True)
        self.thumbnail_timer.timeout.connect(self._start_thumbnail_task)
        try:
            self.selected_pages = set(parse_page_ranges(current_ranges, total_pages))
        except ValueError:
            self.selected_pages = set()

        self.setWindowTitle("Elegir páginas")
        self.setMinimumSize(780, 620)
        self.resize(960, 760)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        title = QLabel(f"Elegí las páginas de {Path(pdf_path).name}")
        title.setObjectName("dialogTitle")
        title.setWordWrap(True)
        subtitle = QLabel(
            "Marcá las páginas que querés incluir. La selección se conserva al cambiar de grupo."
        )
        subtitle.setObjectName("mutedText")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        pager = QHBoxLayout()
        self.previous_button = QPushButton("← Anteriores")
        self.previous_button.setObjectName("secondaryButton")
        self.previous_button.clicked.connect(self.previous_page)
        pager.addWidget(self.previous_button)
        self.page_label = QLabel("")
        self.page_label.setObjectName("pagerLabel")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pager.addWidget(self.page_label, 1)
        self.next_button = QPushButton("Siguientes →")
        self.next_button.setObjectName("secondaryButton")
        self.next_button.clicked.connect(self.next_page)
        pager.addWidget(self.next_button)
        root.addLayout(pager)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("thumbnailGrid")
        self.list_widget.setViewMode(QListView.ViewMode.IconMode)
        self.list_widget.setFlow(QListView.Flow.LeftToRight)
        self.list_widget.setWrapping(True)
        self.list_widget.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_widget.setMovement(QListView.Movement.Static)
        self.list_widget.setIconSize(QSize(116, 148))
        self.list_widget.setGridSize(QSize(136, 184))
        self.list_widget.setSpacing(7)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        root.addWidget(self.list_widget, 1)

        toolbar = QHBoxLayout()
        self.mark_all_button = QPushButton("Marcar todas")
        self.mark_all_button.setObjectName("secondaryButton")
        self.mark_all_button.setToolTip("Incluir todas las páginas de este PDF")
        self.mark_all_button.clicked.connect(lambda: self.set_all_checked(True))
        toolbar.addWidget(self.mark_all_button)
        self.clear_all_button = QPushButton("Desmarcar todas")
        self.clear_all_button.setObjectName("secondaryButton")
        self.clear_all_button.setToolTip("Empezar una selección nueva para este PDF")
        self.clear_all_button.clicked.connect(lambda: self.set_all_checked(False))
        toolbar.addWidget(self.clear_all_button)
        self.mark_button = QPushButton("Marcar este grupo")
        self.mark_button.setObjectName("secondaryButton")
        self.mark_button.clicked.connect(lambda: self.set_visible_checked(True))
        toolbar.addWidget(self.mark_button)
        self.clear_button = QPushButton("Desmarcar este grupo")
        self.clear_button.setObjectName("secondaryButton")
        self.clear_button.clicked.connect(lambda: self.set_visible_checked(False))
        toolbar.addWidget(self.clear_button)
        toolbar.addStretch(1)
        self.selected_label = QLabel("")
        self.selected_label.setObjectName("selectionCount")
        toolbar.addWidget(self.selected_label)
        root.addLayout(toolbar)

        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loadingBar")
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        root.addWidget(self.loading_bar)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar selección")
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primaryButton")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setObjectName("secondaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.list_widget.itemChanged.connect(self._item_changed)
        self.setStyleSheet("""
            QDialog { background:#F5F7FB; color:#1F2937; }
            QLabel#dialogTitle { font-size:20px; font-weight:750; color:#172554; }
            QLabel#mutedText { color:#697586; font-size:12px; }
            QLabel#pagerLabel { color:#34466B; font-weight:650; }
            QLabel#selectionCount { color:#3157C8; font-weight:700; }
            QListWidget#thumbnailGrid { background:white; border:1px solid #E3E8F1; border-radius:12px; padding:8px; }
            QListWidget#thumbnailGrid::item { background:#F8FAFE; border:1px solid #E3E8F1; border-radius:8px; padding:4px; color:#263754; }
            QListWidget#thumbnailGrid::item:hover { border:1px solid #8DA4E8; background:#F0F4FF; }
            QPushButton { border:0; border-radius:8px; padding:9px 13px; font-weight:600; }
            QPushButton#primaryButton { background:#3157C8; color:white; padding:10px 16px; }
            QPushButton#secondaryButton { background:#E9EEF8; color:#31466F; }
            QProgressBar#loadingBar { background:#E1E7F2; border:0; border-radius:3px; min-height:5px; max-height:5px; }
            QProgressBar#loadingBar::chunk { background:#3157C8; border-radius:3px; }
        """)
        self._show_page_group()

    def _show_page_group(self) -> None:
        self.thumbnail_timer.stop()
        self.current_task_id = None
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        self.page_indexes.clear()
        end = min(self.page_start + PAGES_PER_VIEW, self.total_pages)
        self.page_label.setText(f"Páginas {self.page_start + 1}–{end} de {self.total_pages}")
        self.previous_button.setEnabled(self.page_start > 0)
        self.next_button.setEnabled(end < self.total_pages)

        for page_index in range(self.page_start, end):
            item = QListWidgetItem(f"Página {page_index + 1}\nCargando vista previa…")
            item.setData(Qt.ItemDataRole.UserRole, page_index)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setCheckState(
                Qt.CheckState.Checked if page_index in self.selected_pages else Qt.CheckState.Unchecked
            )
            self.list_widget.addItem(item)
            self.page_indexes[page_index] = item

        self.list_widget.blockSignals(False)
        self._update_selected_label()
        self.loading_bar.show()

        self.current_task_id = None
        if self.isVisible():
            self.thumbnail_timer.start(0)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.page_indexes:
            self.thumbnail_timer.start(0)

    def _start_thumbnail_task(self) -> None:
        if not self.isVisible():
            return
        indexes = list(self.page_indexes)
        if not indexes:
            self.loading_bar.hide()
            return
        task = ThumbnailTask(self.pdf_path, indexes)
        # Keep the Python wrapper alive until completion is handled on the GUI thread.
        task.setAutoDelete(False)
        task.signals.ready.connect(self._thumbnail_ready)
        task.signals.failed.connect(self._thumbnail_failed)
        task.signals.finished.connect(self._task_finished)
        self.tasks.add(task)
        self.current_task_id = id(task)
        self.pool.start(task)

    @Slot(int, bytes)
    def _thumbnail_ready(self, page_index: int, image_bytes: bytes) -> None:
        item = self.page_indexes.get(page_index)
        if item is None:
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(image_bytes):
            item.setIcon(QIcon(pixmap))
            item.setText(f"Página {page_index + 1}")

    @Slot(int, str)
    def _thumbnail_failed(self, page_index: int, detail: str) -> None:
        item = self.page_indexes.get(page_index)
        if item is not None:
            item.setText(f"Página {page_index + 1}\nVista previa no disponible")
            item.setToolTip(detail)

    @Slot(int)
    def _task_finished(self, task_id: int) -> None:
        task = next((item for item in self.tasks if id(item) == task_id), None)
        if task is None:
            return
        for signal, slot in (
            (task.signals.ready, self._thumbnail_ready),
            (task.signals.failed, self._thumbnail_failed),
            (task.signals.finished, self._task_finished),
        ):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass
        self.tasks.discard(task)
        if task_id == self.current_task_id:
            self.loading_bar.hide()

    @Slot(QListWidgetItem)
    def _item_changed(self, item: QListWidgetItem) -> None:
        page_index = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            self.selected_pages.add(page_index)
        else:
            self.selected_pages.discard(page_index)
        self._update_selected_label()

    def _update_selected_label(self) -> None:
        count = len(self.selected_pages)
        self.selected_label.setText(f"{count} página{'s' if count != 1 else ''} seleccionada{'s' if count != 1 else ''}")

    def set_all_checked(self, checked: bool) -> None:
        self.selected_pages = set(range(self.total_pages)) if checked else set()
        self.list_widget.blockSignals(True)
        for page_index, item in self.page_indexes.items():
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.list_widget.blockSignals(False)
        self._update_selected_label()

    def set_visible_checked(self, checked: bool) -> None:
        self.list_widget.blockSignals(True)
        for page_index, item in self.page_indexes.items():
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            if checked:
                self.selected_pages.add(page_index)
            else:
                self.selected_pages.discard(page_index)
        self.list_widget.blockSignals(False)
        self._update_selected_label()

    def previous_page(self) -> None:
        if self.page_start > 0:
            self.page_start = max(0, self.page_start - PAGES_PER_VIEW)
            self._show_page_group()

    def next_page(self) -> None:
        if self.page_start + PAGES_PER_VIEW < self.total_pages:
            self.page_start = min(
                self.total_pages - 1,
                self.page_start + PAGES_PER_VIEW,
            )
            self._show_page_group()

    def accept(self) -> None:
        if not self.selected_pages:
            QMessageBox.warning(
                self,
                "No hay páginas seleccionadas",
                "Marcá al menos una página para poder continuar.",
            )
            return
        super().accept()

    def done(self, result: int) -> None:
        self.thumbnail_timer.stop()
        # Finish the current 30-page batch before the owning card releases this dialog.
        self.pool.waitForDone()
        super().done(result)

    def selected_ranges(self) -> str:
        return format_page_ranges(sorted(index + 1 for index in self.selected_pages))
