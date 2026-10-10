"""Dialog for visually reordering selected pages across multiple PDFs."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pypdfium2 as pdfium
from PySide6.QtCore import QObject, QRunnable, QSize, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdf_escolar.pdf_engine import PdfPageRef
from pdf_escolar.pdf_preview import render_page_thumbnail


class PageOrderSignals(QObject):
    ready = Signal(int, bytes)
    failed = Signal(int, str)
    finished = Signal()


class PageOrderThumbnailTask(QRunnable):
    """Render only visible page thumbnails, grouped by source PDF."""

    def __init__(self, requests: list[tuple[int, PdfPageRef]]):
        super().__init__()
        self.requests = requests
        self.signals = PageOrderSignals()

    @Slot()
    def run(self) -> None:
        grouped: dict[str, list[tuple[int, PdfPageRef]]] = defaultdict(list)
        for item_id, reference in self.requests:
            grouped[str(Path(reference.path).expanduser().resolve())].append((item_id, reference))

        for path, entries in grouped.items():
            document = None
            try:
                document = pdfium.PdfDocument(path)
                for item_id, reference in entries:
                    try:
                        image_bytes = render_page_thumbnail(document, reference.page_index)
                        self.signals.ready.emit(item_id, image_bytes)
                    except Exception as exc:
                        self.signals.failed.emit(item_id, str(exc))
            except Exception as exc:
                for item_id, _reference in entries:
                    self.signals.failed.emit(item_id, str(exc))
            finally:
                if document is not None:
                    document.close()

        self.signals.finished.emit()


class PageOrderDialog(QDialog):
    """Arrange selected pages across source PDFs using drag-and-drop or buttons."""

    def __init__(self, pages: list[PdfPageRef], parent: QWidget | None = None):
        super().__init__(parent)
        self.pages = list(pages)
        self.tasks: set[QRunnable] = set()
        self.requested_thumbnails: set[int] = set()
        self.items_by_id: dict[int, QListWidgetItem] = {}

        self.setWindowTitle("Ordenar páginas")
        self.setMinimumSize(780, 620)
        self.resize(980, 760)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(12)

        title = QLabel("Ordená las páginas del PDF final")
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            "Arrastrá las miniaturas con el mouse o el touchpad. "
            "También podés seleccionar una página y usar Subir o Bajar. "
            "El orden de esta ventana será el del documento final."
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
        self.list_widget.setIconSize(QSize(108, 140))
        self.list_widget.setGridSize(QSize(164, 188))
        self.list_widget.setSpacing(6)
        self.list_widget.verticalScrollBar().valueChanged.connect(
            self._queue_visible_thumbnails
        )
        root.addWidget(self.list_widget, 1)

        self.loading_bar = QProgressBar()
        self.loading_bar.setObjectName("loadingBar")
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setRange(0, 0)
        self.loading_bar.hide()
        root.addWidget(self.loading_bar)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Aplicar orden")
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
            item.setSizeHint(QSize(158, 182))
            self.list_widget.addItem(item)
            self.items_by_id[item_id] = item

        if self.pages:
            self.list_widget.setCurrentRow(0)

        self.setStyleSheet("""
            QDialog { background:#F5F7FB; color:#1F2937; }
            QLabel#dialogTitle { font-size:20px; font-weight:750; color:#172554; }
            QLabel#mutedText { color:#53627A; font-size:13px; }
            QLabel#selectionCount { color:#3157C8; font-weight:700; }
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
            QPushButton { border:0; border-radius:8px; padding:9px 13px; font-weight:600; }
            QPushButton#primaryButton { background:#3157C8; color:white; padding:10px 16px; }
            QPushButton#secondaryButton { background:#E9EEF8; color:#31466F; }
            QProgressBar#loadingBar {
                background:#E1E7F2; border:0; border-radius:3px;
                min-height:5px; max-height:5px;
            }
            QProgressBar#loadingBar::chunk { background:#3157C8; border-radius:3px; }
        """)

        if self.pages:
            QTimer.singleShot(0, self._queue_visible_thumbnails)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "list_widget"):
            self._queue_visible_thumbnails()

    def _queue_visible_thumbnails(self, *_args) -> None:
        if not self.pages or not self.list_widget.isVisible():
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
        task.signals.ready.connect(self._thumbnail_ready)
        task.signals.failed.connect(self._thumbnail_failed)
        task.signals.finished.connect(self._thumbnails_finished)
        task.signals.finished.connect(
            lambda *args, current=task: self.tasks.discard(current)
        )
        self.tasks.add(task)
        from PySide6.QtCore import QThreadPool

        QThreadPool.globalInstance().start(task)

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
            item.setToolTip(f"{item.toolTip()}\nVista previa no disponible: {detail}")

    @Slot()
    def _thumbnails_finished(self) -> None:
        if not self.tasks:
            self.loading_bar.hide()

    def move_selected_up(self) -> None:
        row = self.list_widget.currentRow()
        if row <= 0:
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(row - 1, item)
        self.list_widget.setCurrentItem(item)
        self._queue_visible_thumbnails()

    def move_selected_down(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or row >= self.list_widget.count() - 1:
            return
        item = self.list_widget.takeItem(row)
        self.list_widget.insertItem(row + 1, item)
        self.list_widget.setCurrentItem(item)
        self._queue_visible_thumbnails()

    def restore_initial_order(self) -> None:
        items = sorted(
            (self.list_widget.item(row) for row in range(self.list_widget.count())),
            key=lambda item: int(item.data(Qt.ItemDataRole.UserRole)),
        )
        current_id = (
            int(self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole))
            if self.list_widget.currentItem() is not None
            else None
        )
        self.list_widget.clear()
        for item in items:
            self.list_widget.addItem(item)
        if current_id is not None:
            self.list_widget.setCurrentItem(self.items_by_id[current_id])
        self._queue_visible_thumbnails()

    def ordered_pages(self) -> list[PdfPageRef]:
        return [
            self.pages[int(self.list_widget.item(row).data(Qt.ItemDataRole.UserRole))]
            for row in range(self.list_widget.count())
        ]
