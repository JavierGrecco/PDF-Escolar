"""Paginated, thumbnail-based page picker for large PDFs."""
from __future__ import annotations

from pathlib import Path
from threading import Event

import pypdfium2 as pdfium
from PySide6.QtCore import QObject, QRunnable, QSize, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QListView, QListWidget,
    QListWidgetItem, QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSplitter,
    QVBoxLayout, QWidget, QMessageBox
)

from pdf_escolar.page_ranges import format_page_ranges, parse_page_ranges
from pdf_escolar.pdf_preview import render_page_preview, render_page_thumbnail
from pdf_escolar.ui.messages import safe_exception_detail, show_notice
from pdf_escolar.ui.window_geometry import fit_window_to_screen


PAGES_PER_VIEW = 30


class ThumbnailSignals(QObject):
    ready = Signal(int, bytes)
    failed = Signal(int, str)
    finished = Signal(str)


class ThumbnailTask(QRunnable):
    """Render only the visible page batch, off the GUI thread."""

    def __init__(self, pdf_path: str, page_indexes: list[int]):
        super().__init__()
        self.pdf_path = pdf_path
        self.page_indexes = page_indexes
        self.signals = ThumbnailSignals()
        self._cancelled = Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @Slot()
    def run(self) -> None:
        document = None
        try:
            if self._cancelled.is_set():
                return
            document = pdfium.PdfDocument(self.pdf_path)
            for page_index in self.page_indexes:
                if self._cancelled.is_set():
                    break
                try:
                    image = render_page_thumbnail(document, page_index)
                    if not self._cancelled.is_set():
                        self.signals.ready.emit(page_index, image)
                except Exception as exc:
                    if not self._cancelled.is_set():
                        self.signals.failed.emit(page_index, safe_exception_detail(exc))
        except Exception as exc:
            if not self._cancelled.is_set():
                for page_index in self.page_indexes:
                    self.signals.failed.emit(page_index, safe_exception_detail(exc))
        finally:
            try:
                if document is not None:
                    document.close()
            finally:
                self.signals.finished.emit(str(id(self)))

class SelectionPreviewTask(QRunnable):
    """Render a selected page for the detail panel without blocking the interface."""

    def __init__(self, pdf_path: str, page_index: int):
        super().__init__()
        self.pdf_path = pdf_path
        self.page_index = page_index
        self.signals = ThumbnailSignals()
        self._cancelled = Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @Slot()
    def run(self) -> None:
        document = None
        try:
            if self._cancelled.is_set():
                return
            document = pdfium.PdfDocument(self.pdf_path)
            image_bytes = render_page_preview(
                document, self.page_index, max_size=1800, quality=88
            )
            if not self._cancelled.is_set():
                self.signals.ready.emit(self.page_index, image_bytes)
        except Exception as exc:
            if not self._cancelled.is_set():
                self.signals.failed.emit(
                    self.page_index, safe_exception_detail(exc)
                )
        finally:
            try:
                if document is not None:
                    document.close()
            finally:
                self.signals.finished.emit(str(id(self)))


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
        self.current_task: ThumbnailTask | None = None
        self.preview_task: SelectionPreviewTask | None = None
        self.current_preview_page: int | None = None
        self.preview_pixmap = QPixmap()
        self.thumbnail_timer = QTimer(self)
        self.thumbnail_timer.setSingleShot(True)
        self.thumbnail_timer.timeout.connect(self._start_thumbnail_task)
        try:
            self.selected_pages = set(parse_page_ranges(current_ranges, total_pages))
        except ValueError:
            self.selected_pages = set()

        self.setWindowTitle("Elegir páginas")
        self.compact_layout = fit_window_to_screen(
            self,
            preferred_size=(960, 760),
            minimum_size=(780, 620),
            parent=parent,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(
            12 if self.compact_layout else 24,
            10 if self.compact_layout else 22,
            12 if self.compact_layout else 24,
            10 if self.compact_layout else 20,
        )
        root.setSpacing(6 if self.compact_layout else 14)

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
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("pagePickerSplitter")
        grid_frame = QFrame()
        grid_frame.setObjectName("pagePickerGridFrame")
        grid_layout = QVBoxLayout(grid_frame)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self.list_widget)
        splitter.addWidget(grid_frame)

        self.preview_panel = QFrame()
        self.preview_panel.setObjectName("selectionPreviewPanel")
        preview_layout = QVBoxLayout(self.preview_panel)
        preview_layout.setContentsMargins(
            8 if self.compact_layout else 14,
            8 if self.compact_layout else 14,
            8 if self.compact_layout else 14,
            8 if self.compact_layout else 12,
        )
        preview_layout.setSpacing(5 if self.compact_layout else 9)
        self.preview_title = QLabel("Vista previa de la página")
        self.preview_title.setObjectName("selectionPreviewTitle")
        self.preview_title.setWordWrap(True)
        preview_layout.addWidget(self.preview_title)

        self.preview_source = QLabel("Elegí una página para revisar su contenido.")
        self.preview_source.setObjectName("selectionPreviewSource")
        self.preview_source.setWordWrap(True)
        preview_layout.addWidget(self.preview_source)

        self.preview_image = QLabel("Al elegir una página, vas a poder verla ampliada.")
        self.preview_image.setObjectName("selectionPreviewImage")
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image.setMinimumSize(
            QSize(160, 110) if self.compact_layout else QSize(230, 310)
        )
        self.preview_image.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.preview_image.setWordWrap(True)
        preview_layout.addWidget(self.preview_image, 1)

        self.preview_hint = QLabel(
            "La vista ampliada ayuda a distinguir texto, imágenes y páginas parecidas."
        )
        self.preview_hint.setObjectName("mutedText")
        self.preview_hint.setWordWrap(True)
        preview_layout.addWidget(self.preview_hint)

        self.preview_enlarge_button = QPushButton("Ampliar página…")
        self.preview_enlarge_button.setObjectName("secondaryButton")
        self.preview_enlarge_button.setToolTip(
            "Abrir la página seleccionada en una ventana más grande"
        )
        self.preview_enlarge_button.setEnabled(False)
        self.preview_enlarge_button.clicked.connect(self.open_large_preview)
        preview_layout.addWidget(self.preview_enlarge_button)

        splitter.addWidget(self.preview_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([620, 320])
        root.addWidget(splitter, 1)

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
        self.list_widget.currentItemChanged.connect(self._current_item_changed)
        self.setStyleSheet("""
            QDialog { background:#F5F7FB; color:#1F2937; }
            QLabel#dialogTitle { font-size:20px; font-weight:750; color:#172554; }
            QLabel#mutedText { color:#697586; font-size:12px; }
            QLabel#pagerLabel { color:#34466B; font-weight:650; }
            QLabel#selectionCount { color:#3157C8; font-weight:700; }
            QFrame#pagePickerGridFrame { background:transparent; }
            QFrame#selectionPreviewPanel { background:white; border:1px solid #E0E6F1; border-radius:12px; }
            QLabel#selectionPreviewTitle { color:#172554; font-size:16px; font-weight:750; }
            QLabel#selectionPreviewSource { color:#53627A; font-size:12px; }
            QLabel#selectionPreviewImage { background:#F8FAFE; color:#53627A; border:1px solid #E3E8F1; border-radius:8px; padding:6px; }
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
        for task in tuple(self.tasks):
            task.cancel()
        self.current_task = None
        self.preview_task = None
        self.current_preview_page = None
        self.preview_pixmap = QPixmap()
        self.preview_title.setText("Vista previa de la página")
        self.preview_source.setText("Elegí una página para revisar su contenido.")
        self.preview_image.setPixmap(QPixmap())
        self.preview_image.setText("Al elegir una página, vas a poder verla ampliada.")
        self.preview_enlarge_button.setEnabled(False)
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
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)
        self._update_selected_label()
        self.loading_bar.show()

        if self.isVisible():
            self.thumbnail_timer.start(0)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.page_indexes:
            self.thumbnail_timer.start(0)
        current = self.list_widget.currentItem()
        if current is not None:
            self._load_current_preview(
                int(current.data(Qt.ItemDataRole.UserRole))
            )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_preview_pixmap()

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
        self.current_task = task
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
            item.setToolTip(
                "No pudimos mostrar la vista previa de esta página. "
                "Podés seguir trabajando con las demás."
            )

    @Slot(int, bytes)
    def _selection_preview_ready(self, page_index: int, image_bytes: bytes) -> None:
        if self.current_preview_page != page_index:
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(image_bytes):
            self._selection_preview_failed(page_index, "")
            return
        self.preview_pixmap = pixmap
        self.preview_title.setText(f"Página {page_index + 1} de {self.total_pages}")
        self.preview_source.setText(Path(self.pdf_path).name)
        self.preview_source.setToolTip(str(Path(self.pdf_path).expanduser()))
        self._refresh_preview_pixmap()
        self.preview_enlarge_button.setEnabled(True)

    @Slot(int, str)
    def _selection_preview_failed(self, page_index: int, _detail: str) -> None:
        if self.current_preview_page != page_index:
            return
        self.preview_pixmap = QPixmap()
        self.preview_image.setPixmap(QPixmap())
        self.preview_image.setText(
            "No pudimos mostrar esta página en la vista ampliada. "
            "Podés seguir seleccionándola si corresponde."
        )
        self.preview_enlarge_button.setEnabled(False)

    def _load_current_preview(self, page_index: int) -> None:
        if self.current_preview_page == page_index:
            if not self.preview_pixmap.isNull():
                self._refresh_preview_pixmap()
                return
            if self.preview_task is not None and self.preview_task.page_index == page_index:
                return

        self.current_preview_page = page_index
        self.preview_pixmap = QPixmap()
        self.preview_image.setPixmap(QPixmap())
        self.preview_title.setText(f"Página {page_index + 1} de {self.total_pages}")
        self.preview_source.setText(Path(self.pdf_path).name)
        self.preview_source.setToolTip(str(Path(self.pdf_path).expanduser()))
        self.preview_image.setText("Cargando vista ampliada…")
        self.preview_enlarge_button.setEnabled(False)
        if self.preview_task is not None:
            self.preview_task.cancel()

        if not self.isVisible():
            self.preview_image.setText("La vista ampliada se cargará al abrir esta ventana.")
            return

        task = SelectionPreviewTask(self.pdf_path, page_index)
        task.setAutoDelete(False)
        task.signals.ready.connect(self._selection_preview_ready)
        task.signals.failed.connect(self._selection_preview_failed)
        task.signals.finished.connect(self._task_finished)
        self.preview_task = task
        self.tasks.add(task)
        self.pool.start(task)

    @Slot(QListWidgetItem, QListWidgetItem)
    def _current_item_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            self.current_preview_page = None
            self.preview_pixmap = QPixmap()
            self.preview_image.setPixmap(QPixmap())
            self.preview_image.setText("Elegí una página para revisar su contenido.")
            self.preview_enlarge_button.setEnabled(False)
            return
        self._load_current_preview(
            int(current.data(Qt.ItemDataRole.UserRole))
        )

    def _refresh_preview_pixmap(self) -> None:
        if self.preview_pixmap.isNull() or not hasattr(self, "preview_image"):
            return
        available = self.preview_image.size() - QSize(18, 18)
        if available.width() < 1 or available.height() < 1:
            return
        scaled = self.preview_pixmap.scaled(
            available,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_image.setText("")
        self.preview_image.setPixmap(scaled)

    def open_large_preview(self) -> None:
        if self.preview_pixmap.isNull() or self.current_preview_page is None:
            return
        viewer = QDialog(self)
        viewer.setWindowTitle(
            f"Página {self.current_preview_page + 1} · {Path(self.pdf_path).name}"
        )
        fit_window_to_screen(
            viewer,
            preferred_size=(1180, 920),
            minimum_size=(640, 480),
            parent=self,
        )
        layout = QVBoxLayout(viewer)
        heading = QLabel(
            f"Página {self.current_preview_page + 1} de {self.total_pages} · "
            f"{Path(self.pdf_path).name}"
        )
        heading.setWordWrap(True)
        layout.addWidget(heading)
        scroll = QScrollArea(viewer)
        scroll.setObjectName("largePageScroll")
        scroll.setWidgetResizable(False)
        image = QLabel()
        image.setPixmap(self.preview_pixmap)
        image.setFixedSize(self.preview_pixmap.size())
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(image)
        layout.addWidget(scroll, 1)
        close_button = QPushButton("Volver a la selección")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(viewer.accept)
        layout.addWidget(close_button)
        viewer.exec()

    @Slot(str)
    def _task_finished(self, finished_token: str) -> None:
        task = next((item for item in self.tasks if str(id(item)) == finished_token), None)
        if task is None:
            return
        if isinstance(task, SelectionPreviewTask):
            slots = (
                (task.signals.ready, self._selection_preview_ready),
                (task.signals.failed, self._selection_preview_failed),
                (task.signals.finished, self._task_finished),
            )
            if task is self.preview_task:
                self.preview_task = None
        else:
            slots = (
                (task.signals.ready, self._thumbnail_ready),
                (task.signals.failed, self._thumbnail_failed),
                (task.signals.finished, self._task_finished),
            )
        for signal, slot in slots:
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass
        self.tasks.discard(task)
        if task is self.current_task:
            self.loading_bar.hide()

    @Slot(QListWidgetItem)
    def _item_changed(self, item: QListWidgetItem) -> None:
        page_index = int(item.data(Qt.ItemDataRole.UserRole))
        if item.checkState() == Qt.CheckState.Checked:
            self.selected_pages.add(page_index)
        else:
            self.selected_pages.discard(page_index)
        self._update_selected_label()
        self._load_current_preview(page_index)

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
            show_notice(
                self,
                "No hay páginas seleccionadas",
                "Marcá al menos una página para poder continuar.",
                icon=QMessageBox.Icon.Warning,
            )
            return
        super().accept()

    def selected_ranges(self) -> str:
        return format_page_ranges(sorted(index + 1 for index in self.selected_pages))
