"""Dialog for visually reordering selected pages across multiple PDFs."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from threading import Event

import pypdfium2 as pdfium
from PySide6.QtCore import QObject, QRunnable, QSize, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from pdf_escolar.pdf_engine import PdfPageRef
from pdf_escolar.pdf_preview import render_page_preview, render_page_thumbnail
from pdf_escolar.ui.messages import safe_exception_detail
from pdf_escolar.ui.window_geometry import fit_window_to_screen


class PageOrderSignals(QObject):
    ready = Signal(int, bytes)
    failed = Signal(int, str)
    finished = Signal(str)


class PageOrderThumbnailTask(QRunnable):
    """Render only visible page thumbnails, grouped by source PDF."""

    def __init__(self, requests: list[tuple[int, PdfPageRef]]):
        super().__init__()
        self.requests = requests
        self.signals = PageOrderSignals()
        self._cancelled = Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @Slot()
    def run(self) -> None:
        try:
            grouped: dict[str, list[tuple[int, PdfPageRef]]] = defaultdict(list)
            for item_id, reference in self.requests:
                grouped[str(Path(reference.path).expanduser().resolve())].append(
                    (item_id, reference)
                )

            for path, entries in grouped.items():
                if self._cancelled.is_set():
                    break
                document = None
                try:
                    document = pdfium.PdfDocument(path)
                    for item_id, reference in entries:
                        if self._cancelled.is_set():
                            break
                        try:
                            image_bytes = render_page_thumbnail(document, reference.page_index)
                            if not self._cancelled.is_set():
                                self.signals.ready.emit(item_id, image_bytes)
                        except Exception as exc:
                            if not self._cancelled.is_set():
                                self.signals.failed.emit(item_id, safe_exception_detail(exc))
                except Exception as exc:
                    if not self._cancelled.is_set():
                        for item_id, _reference in entries:
                            self.signals.failed.emit(item_id, safe_exception_detail(exc))
                finally:
                    if document is not None:
                        document.close()
        except Exception as exc:
            if not self._cancelled.is_set():
                for item_id, _reference in self.requests:
                    self.signals.failed.emit(item_id, safe_exception_detail(exc))
        finally:
            self.signals.finished.emit(str(id(self)))

class PageOrderPreviewTask(QRunnable):
    """Render a selected page at detail-preview resolution off the GUI thread."""

    def __init__(self, item_id: int, reference: PdfPageRef):
        super().__init__()
        self.item_id = item_id
        self.reference = reference
        self.signals = PageOrderSignals()
        self._cancelled = Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @Slot()
    def run(self) -> None:
        document = None
        try:
            if self._cancelled.is_set():
                return
            path = str(Path(self.reference.path).expanduser().resolve())
            document = pdfium.PdfDocument(path)
            image_bytes = render_page_preview(
                document, self.reference.page_index, max_size=1600, quality=88
            )
            if not self._cancelled.is_set():
                self.signals.ready.emit(self.item_id, image_bytes)
        except Exception as exc:
            if not self._cancelled.is_set():
                self.signals.failed.emit(self.item_id, safe_exception_detail(exc))
        finally:
            try:
                if document is not None:
                    document.close()
            finally:
                self.signals.finished.emit(str(id(self)))

class PageOrderDialog(QDialog):
    """Arrange selected pages across source PDFs using drag-and-drop or buttons."""

    def __init__(
        self,
        pages: list[PdfPageRef],
        parent: QWidget | None = None,
        *,
        confirm_label: str = "Aplicar orden",
    ):
        super().__init__(parent)
        self.pages = list(pages)
        self.confirm_label = confirm_label
        self.tasks: set[QRunnable] = set()
        self.preview_task: PageOrderPreviewTask | None = None
        self.current_preview_id: int | None = None
        self.preview_pixmap = QPixmap()
        self.thumbnail_pool = QThreadPool(self)
        self.requested_thumbnails: set[int] = set()
        self.items_by_id: dict[int, QListWidgetItem] = {}

        self.setWindowTitle(
            "Revisá el PDF antes de guardarlo"
            if confirm_label == "Continuar a guardar"
            else "Ordenar páginas"
        )
        self.compact_layout = fit_window_to_screen(
            self,
            preferred_size=(1180, 760),
            minimum_size=(880, 620),
            parent=parent,
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(
            12 if self.compact_layout else 22,
            10 if self.compact_layout else 20,
            12 if self.compact_layout else 22,
            10 if self.compact_layout else 18,
        )
        root.setSpacing(6 if self.compact_layout else 12)

        title = QLabel(
            "Revisá el PDF antes de guardarlo"
            if confirm_label == "Continuar a guardar"
            else "Ordená las páginas del PDF final"
        )
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            "Arrastrá las miniaturas con el mouse o el panel táctil. "
            "Elegí Pequeñas, Medianas o Grandes para reconocer mejor cada hoja; "
            "seleccioná una página para verla ampliada a un lado. " 
            "El orden de esta ventana será el del documento final."
            + (
                " Al continuar, vas a elegir dónde guardar el PDF."
                if confirm_label == "Continuar a guardar"
                else ""
            )
        )
        subtitle.setObjectName("mutedText")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        controls = QHBoxLayout()
        self.up_button = QPushButton("↑ Subir")
        self.up_button.setObjectName("secondaryButton")
        self.up_button.setToolTip("Mover la página seleccionada una posición hacia arriba")
        self.up_button.clicked.connect(self.move_selected_up)
        controls.addWidget(self.up_button)

        self.down_button = QPushButton("↓ Bajar")
        self.down_button.setObjectName("secondaryButton")
        self.down_button.setToolTip("Mover la página seleccionada una posición hacia abajo")
        self.down_button.clicked.connect(self.move_selected_down)
        controls.addWidget(self.down_button)

        self.reset_button = QPushButton("Restablecer orden inicial")
        self.reset_button.setObjectName("secondaryButton")
        self.reset_button.setToolTip("Volver al orden que tenían las páginas al abrir esta ventana")
        self.reset_button.clicked.connect(self.restore_initial_order)
        controls.addWidget(self.reset_button)

        size_label = QLabel("Miniaturas")
        size_label.setObjectName("mutedText")
        controls.addWidget(size_label)
        self.thumbnail_size_selector = QComboBox()
        self.thumbnail_size_selector.addItem("Pequeñas", "small")
        self.thumbnail_size_selector.addItem("Medianas", "medium")
        self.thumbnail_size_selector.addItem("Grandes", "large")
        self.thumbnail_size_selector.setCurrentIndex(1)
        self.thumbnail_size_selector.setToolTip(
            "Elegí el tamaño de las miniaturas para reconocer mejor las páginas."
        )
        controls.addWidget(self.thumbnail_size_selector)
        controls.addStretch(1)

        self.count_label = QLabel(f"{len(self.pages):,} páginas")
        self.count_label.setObjectName("selectionCount")
        controls.addWidget(self.count_label)
        root.addLayout(controls)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("pageOrderGrid")
        self.list_widget.setViewMode(QListView.ViewMode.IconMode)
        self.list_widget.setFlow(QListView.Flow.LeftToRight)
        self.list_widget.setWrapping(True)
        self.list_widget.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_widget.setMovement(QListView.Movement.Snap)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDropIndicatorShown(True)
        self.list_widget.setDragDropOverwriteMode(False)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.setIconSize(QSize(112, 144))
        self.list_widget.setGridSize(QSize(158, 194))
        self.list_widget.setSpacing(6)
        self.list_widget.verticalScrollBar().valueChanged.connect(
            self._queue_visible_thumbnails
        )
        self.thumbnail_size_selector.currentIndexChanged.connect(self._apply_thumbnail_size)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("pageOrderSplitter")
        grid_frame = QFrame()
        grid_frame.setObjectName("pageOrderGridFrame")
        grid_layout = QVBoxLayout(grid_frame)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.addWidget(self.list_widget)
        splitter.addWidget(grid_frame)

        self.preview_panel = QFrame()
        self.preview_panel.setObjectName("pagePreviewPanel")
        preview_layout = QVBoxLayout(self.preview_panel)
        preview_layout.setContentsMargins(
            8 if self.compact_layout else 14,
            8 if self.compact_layout else 14,
            8 if self.compact_layout else 14,
            8 if self.compact_layout else 12,
        )
        preview_layout.setSpacing(5 if self.compact_layout else 9)
        self.preview_title = QLabel("Vista previa de la página")
        self.preview_title.setObjectName("pagePreviewTitle")
        self.preview_title.setWordWrap(True)
        preview_layout.addWidget(self.preview_title)

        self.preview_source = QLabel("Seleccioná una miniatura para inspeccionarla.")
        self.preview_source.setObjectName("pagePreviewSource")
        self.preview_source.setWordWrap(True)
        preview_layout.addWidget(self.preview_source)

        self.preview_image = QLabel("Seleccioná una página para ver su contenido.")
        self.preview_image.setObjectName("pagePreviewImage")
        self.preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image.setMinimumSize(
            QSize(180, 110) if self.compact_layout else QSize(250, 330)
        )
        self.preview_image.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.preview_image.setWordWrap(True)
        preview_layout.addWidget(self.preview_image, 1)

        self.preview_hint = QLabel(
            "La página se actualiza al seleccionarla. Podés ampliarla para revisar los detalles."
        )
        self.preview_hint.setObjectName("mutedText")
        self.preview_hint.setWordWrap(True)
        preview_layout.addWidget(self.preview_hint)

        self.enlarge_button = QPushButton("Ampliar página…")
        self.enlarge_button.setObjectName("secondaryButton")
        self.enlarge_button.setToolTip("Abrir la vista detallada de la página seleccionada")
        self.enlarge_button.clicked.connect(self.open_large_preview)
        preview_layout.addWidget(self.enlarge_button)
        splitter.addWidget(self.preview_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([720, 420])
        root.addWidget(splitter, 1)

        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loadingBar")
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        root.addWidget(self.loading_bar)

        self.thumbnail_timer = QTimer(self)
        self.thumbnail_timer.setSingleShot(True)
        self.thumbnail_timer.timeout.connect(self._queue_visible_thumbnails)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.confirm_label)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primaryButton")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setObjectName("secondaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        for item_id, reference in enumerate(self.pages):
            item = QListWidgetItem(
                f"{Path(reference.path).name}\nPágina {reference.page_index + 1}"
            )
            item.setData(Qt.ItemDataRole.UserRole, item_id)
            item.setToolTip(f"{Path(reference.path)}\nPágina {reference.page_index + 1}")
            item.setSizeHint(QSize(158, 194))
            self.list_widget.addItem(item)
            self.items_by_id[item_id] = item

        self.list_widget.currentItemChanged.connect(self._current_item_changed)
        self.list_widget.model().rowsMoved.connect(self._items_reordered)
        if self.pages:
            self.list_widget.setCurrentRow(0)
        else:
            self._load_current_preview()
        self._apply_thumbnail_size()

        self.setStyleSheet("""
            QDialog { background:#F5F7FB; color:#1F2937; }
            QLabel#dialogTitle { font-size:20px; font-weight:750; color:#172554; }
            QLabel#mutedText { color:#53627A; font-size:12px; }
            QLabel#selectionCount { color:#3157C8; font-weight:700; }
            QFrame#pageOrderGridFrame { background:transparent; }
            QListWidget#pageOrderGrid {
                background:white; border:1px solid #E3E8F1;
                border-radius:12px; padding:8px;
            }
            QListWidget#pageOrderGrid::item {
                background:#F8FAFE; border:1px solid #E3E8F1;
                border-radius:8px; padding:4px; color:#263754;
            }
            QListWidget#pageOrderGrid::item:hover {
                border:1px solid #8DA4E8; background:#F0F4FF;
            }
            QListWidget#pageOrderGrid::item:selected {
                border:2px solid #3157C8; background:#E8EEFF;
            }
            QFrame#pagePreviewPanel {
                background:white; border:1px solid #E0E6F1; border-radius:12px;
            }
            QLabel#pagePreviewTitle { color:#172554; font-size:16px; font-weight:750; }
            QLabel#pagePreviewSource { color:#53627A; font-size:12px; }
            QLabel#pagePreviewImage {
                background:#F8FAFE; color:#53627A; border:1px solid #E3E8F1;
                border-radius:8px; padding:6px;
            }
            QComboBox {
                background:white; color:#263754; border:1px solid #D7DFEC;
                border-radius:7px; padding:6px 9px; min-width:85px;
            }
            QPushButton { border:0; border-radius:8px; padding:9px 13px; font-weight:600; }
            QPushButton#primaryButton { background:#3157C8; color:white; padding:10px 16px; }
            QPushButton#secondaryButton { background:#E9EEF8; color:#31466F; }
            QPushButton#secondaryButton:hover { background:#DEE6F5; }
            QProgressBar#loadingBar {
                background:#E1E7F2; border:0; border-radius:3px;
                min-height:5px; max-height:5px;
            }
            QProgressBar#loadingBar::chunk { background:#3157C8; border-radius:3px; }
            QScrollArea#largePageScroll { background:#EEF2F8; border:0; }
        """)

    def _apply_thumbnail_size(self, *_args) -> None:
        """Change the grid density without changing the page order."""
        if not hasattr(self, "list_widget"):
            return
        size = self.thumbnail_size_selector.currentData()
        dimensions = {
            "small": (QSize(82, 106), QSize(126, 154)),
            "medium": (QSize(112, 144), QSize(158, 194)),
            "large": (QSize(150, 192), QSize(204, 244)),
        }
        icon_size, grid_size = dimensions.get(size, dimensions["medium"])
        self.list_widget.setIconSize(icon_size)
        self.list_widget.setGridSize(grid_size)
        for row in range(self.list_widget.count()):
            self.list_widget.item(row).setSizeHint(
                QSize(grid_size.width() - 4, grid_size.height() - 4)
            )
        self.list_widget.doItemsLayout()
        self._queue_visible_thumbnails()

    def _current_item_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        self._load_current_preview()

    def _items_reordered(self, *_args) -> None:
        self._refresh_preview_metadata()
        self._queue_visible_thumbnails()

    def _refresh_preview_metadata(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        item_id = int(item.data(Qt.ItemDataRole.UserRole))
        reference = self.pages[item_id]
        position = self.list_widget.row(item) + 1
        self.preview_title.setText(
            f"Página {position} de {self.list_widget.count()} del PDF final"
        )
        self.preview_source.setText(
            f"Origen: {Path(reference.path).name} · página {reference.page_index + 1}"
        )
        self.preview_source.setToolTip(str(Path(reference.path).expanduser()))
        self.preview_source.setAccessibleName(
            f"Archivo de origen {Path(reference.path).name}, página {reference.page_index + 1}"
        )

    def _load_current_preview(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            self.current_preview_id = None
            self.preview_pixmap = QPixmap()
            self.preview_image.setPixmap(QPixmap())
            self.preview_image.setText("Seleccioná una página para ver su contenido.")
            self.enlarge_button.setEnabled(False)
            return

        item_id = int(item.data(Qt.ItemDataRole.UserRole))
        self._refresh_preview_metadata()
        if not self.isVisible():
            # Do not start workers from a dialog that has not been shown yet.
            # This keeps construction cheap and avoids racing modal cleanup.
            self.preview_image.setPixmap(QPixmap())
            self.preview_image.setText("La vista previa se cargará al abrir el organizador.")
            self.enlarge_button.setEnabled(False)
            return
        if self.current_preview_id == item_id:
            if not self.preview_pixmap.isNull():
                self._refresh_preview_pixmap()
                return
            if self.preview_task is not None and self.preview_task.item_id == item_id:
                return

        self.current_preview_id = item_id
        self.preview_pixmap = QPixmap()
        self.preview_image.setPixmap(QPixmap())
        self.preview_image.setText("Cargando vista previa…")
        self.enlarge_button.setEnabled(False)
        if self.preview_task is not None:
            self.preview_task.cancel()

        task = PageOrderPreviewTask(item_id, self.pages[item_id])
        task.setAutoDelete(False)
        task.signals.ready.connect(self._preview_ready)
        task.signals.failed.connect(self._preview_failed)
        task.signals.finished.connect(self._task_finished)
        self.preview_task = task
        self.tasks.add(task)
        self.thumbnail_pool.start(task)

    @Slot(int, bytes)
    def _preview_ready(self, item_id: int, image_bytes: bytes) -> None:
        current = self.list_widget.currentItem()
        if (
            current is None
            or int(current.data(Qt.ItemDataRole.UserRole)) != item_id
            or self.current_preview_id != item_id
        ):
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(image_bytes):
            self.preview_image.setText("No pudimos interpretar la vista previa.")
            return
        self.preview_pixmap = pixmap
        self._refresh_preview_pixmap()
        self.enlarge_button.setEnabled(True)

    @Slot(int, str)
    def _preview_failed(self, item_id: int, _detail: str) -> None:
        if self.current_preview_id != item_id:
            return
        self.preview_pixmap = QPixmap()
        self.preview_image.setPixmap(QPixmap())
        self.preview_image.setText(
            "Esta página no se pudo previsualizar. Sigue incluida en el orden."
        )
        self.enlarge_button.setEnabled(False)

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
        if self.preview_pixmap.isNull():
            return
        item = self.list_widget.currentItem()
        if item is None:
            return
        item_id = int(item.data(Qt.ItemDataRole.UserRole))
        reference = self.pages[item_id]
        viewer = QDialog(self)
        viewer.setWindowTitle(
            f"{Path(reference.path).name} · página {reference.page_index + 1}"
        )
        fit_window_to_screen(
            viewer,
            preferred_size=(1180, 920),
            minimum_size=(640, 480),
            parent=self,
        )
        layout = QVBoxLayout(viewer)
        heading = QLabel(
            f"Página {self.list_widget.row(item) + 1} del documento final · "
            f"Página {reference.page_index + 1} de {Path(reference.path).name}"
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
        close_button = QPushButton("Volver al ordenamiento")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(viewer.accept)
        layout.addWidget(close_button)
        viewer.exec()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.pages:
            self.thumbnail_timer.start(0)
            self._load_current_preview()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "list_widget"):
            self._queue_visible_thumbnails()
            self._refresh_preview_pixmap()

    def _queue_visible_thumbnails(self, *_args) -> None:
        if not self.pages or not self.isVisible() or not self.list_widget.isVisible():
            return
        viewport = self.list_widget.viewport().rect()
        requests: list[tuple[int, PdfPageRef]] = []
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            item_id = int(item.data(Qt.ItemDataRole.UserRole))
            if item_id in self.requested_thumbnails:
                continue
            if self.list_widget.visualItemRect(item).intersects(viewport):
                self.requested_thumbnails.add(item_id)
                requests.append((item_id, self.pages[item_id]))

        if not requests:
            return
        self.loading_bar.show()
        task = PageOrderThumbnailTask(requests)
        # QRunnable auto-deletion is unsafe while Python still retains the
        # wrapper in self.tasks. Let the completed callback release it instead.
        task.setAutoDelete(False)
        task.signals.ready.connect(self._thumbnail_ready)
        task.signals.failed.connect(self._thumbnail_failed)
        task.signals.finished.connect(self._task_finished)
        self.tasks.add(task)
        self.thumbnail_pool.start(task)

    @Slot(int, bytes)
    def _thumbnail_ready(self, item_id: int, image_bytes: bytes) -> None:
        item = self.items_by_id.get(item_id)
        if item is None:
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(image_bytes):
            item.setIcon(QIcon(pixmap))

    @Slot(int, str)
    def _thumbnail_failed(self, item_id: int, detail: str) -> None:
        item = self.items_by_id.get(item_id)
        if item is not None:
            item.setToolTip(
                f"{item.toolTip()}\n"
                "Vista previa no disponible. La página sigue incluida en el orden."
            )

    @Slot(str)
    def _task_finished(self, finished_token: str) -> None:
        # This is a bound QObject slot, so Qt queues the callback to the GUI
        # thread. QRunnable auto-deletion stays disabled while the Python
        # wrapper is retained in self.tasks.
        task = next((item for item in self.tasks if str(id(item)) == finished_token), None)
        if task is None:
            return
        if isinstance(task, PageOrderPreviewTask):
            slots = (
                (task.signals.ready, self._preview_ready),
                (task.signals.failed, self._preview_failed),
                (task.signals.finished, self._task_finished),
            )
            if self.preview_task is task:
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
        if not self.tasks:
            self.loading_bar.hide()

    def move_selected_up(self) -> None:
        row = self.list_widget.currentRow()
        if row <= 0:
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(row - 1, item)
        self.list_widget.setCurrentItem(item)
        self._refresh_preview_metadata()
        self._queue_visible_thumbnails()

    def move_selected_down(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= self.list_widget.count() - 1:
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(row + 1, item)
        self.list_widget.setCurrentItem(item)
        self._refresh_preview_metadata()
        self._queue_visible_thumbnails()

    def restore_initial_order(self) -> None:
        current_item = self.list_widget.currentItem()
        current_id = (
            int(current_item.data(Qt.ItemDataRole.UserRole))
            if current_item is not None
            else None
        )
        items = [self.list_widget.takeItem(0) for _ in range(self.list_widget.count())]
        items.sort(key=lambda item: int(item.data(Qt.ItemDataRole.UserRole)))
        for item in items:
            self.list_widget.addItem(item)
        if current_id is not None:
            self.list_widget.setCurrentItem(self.items_by_id[current_id])
        self._refresh_preview_metadata()
        self._queue_visible_thumbnails()

    def ordered_pages(self) -> list[PdfPageRef]:
        return [
            self.pages[int(self.list_widget.item(row).data(Qt.ItemDataRole.UserRole))]
            for row in range(self.list_widget.count())
        ]
