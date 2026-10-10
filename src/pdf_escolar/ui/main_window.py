"""Accessible desktop interface for PDF Escolar."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from PySide6.QtCore import (
    QObject, QRunnable, QSettings, QThreadPool, Qt, Signal, Slot, QUrl, QMimeData
)
from PySide6.QtGui import QDesktopServices, QDrag, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QProgressBar, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget
)
from pdf_escolar import __version__
from pdf_escolar.page_ranges import parse_page_ranges
from pdf_escolar.pdf_engine import (
    PdfPageRef, PdfSource, combine_pages_in_order, combine_selected_pages, inspect_pdf
)
from pdf_escolar.ui.messages import (
    friendly_export_error, friendly_pdf_load_error, safe_exception_detail, show_notice
)
from pdf_escolar.ui.page_order import PageOrderDialog
from pdf_escolar.ui.page_picker import PagePickerDialog


@dataclass(frozen=True)
class DocumentInfo:
    path: str
    page_count: int
    file_size: int


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


class WorkerSignals(QObject):
    progress = Signal(int, int, str)
    loaded = Signal(str, int, int)
    load_error = Signal(str, str)
    batch_finished = Signal()
    export_finished = Signal(int, str)
    export_error = Signal(str)
    task_finished = Signal(str)


class InspectTask(QRunnable):
    def __init__(self, paths: list[str]):
        super().__init__()
        self.paths = paths
        self.signals = WorkerSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self):
        try:
            for index, path in enumerate(self.paths, start=1):
                try:
                    self.signals.loaded.emit(path, inspect_pdf(path), os.path.getsize(path))
                except Exception as exc:
                    self.signals.load_error.emit(path, safe_exception_detail(exc))
                self.signals.progress.emit(
                    index, len(self.paths), f"Revisando {Path(path).name}…"
                )
        finally:
            self.signals.batch_finished.emit()
            self.signals.task_finished.emit(str(id(self)))


class ExportTask(QRunnable):
    def __init__(
        self,
        sources: list[PdfSource],
        output_path: str,
        page_order: list[PdfPageRef] | None = None,
    ):
        super().__init__()
        self.sources = sources
        self.output_path = output_path
        self.page_order = page_order
        self.signals = WorkerSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self):
        try:
            def report(done, total, message):
                self.signals.progress.emit(done, total, message)

            if self.page_order is None:
                count = combine_selected_pages(self.sources, self.output_path, report)
            else:
                count = combine_pages_in_order(self.page_order, self.output_path, report)
            self.signals.export_finished.emit(count, self.output_path)
        except Exception as exc:
            self.signals.export_error.emit(safe_exception_detail(exc))
        finally:
            self.signals.task_finished.emit(str(id(self)))


class DropArea(QFrame):
    files_dropped = Signal(list)

    def __init__(self, choose_callback):
        super().__init__()
        self.setObjectName("dropArea")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        title = QLabel("Agregá tus archivos PDF")
        title.setObjectName("dropTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("Arrastralos hasta acá o elegilos desde tu computadora")
        hint.setObjectName("mutedText")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button = QPushButton("Seleccionar archivos PDF")
        button.setObjectName("secondaryButton")
        button.clicked.connect(choose_callback)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.title_label = title
        self.hint_label = hint
        self.choose_button = button
        self.content_layout = layout

    def set_compact(self, compact: bool) -> None:
        """Keep the drop target available without wasting space after loading files."""
        self.title_label.setVisible(not compact)
        self.hint_label.setVisible(not compact)
        self.choose_button.setText(
            "Agregar más PDF" if compact else "Seleccionar archivos PDF"
        )
        if compact:
            self.content_layout.setContentsMargins(12, 8, 12, 8)
            self.content_layout.setSpacing(4)
            self.setToolTip("También podés arrastrar archivos PDF hasta esta zona.")
        else:
            self.content_layout.setContentsMargins(18, 18, 18, 18)
            self.content_layout.setSpacing(10)
            self.setToolTip("")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        self.files_dropped.emit(paths)
        event.acceptProposedAction()


DOCUMENT_MIME_TYPE = "application/x-pdf-escolar-document"


class DragHandle(QLabel):
    """Control visible para arrastrar un archivo con mouse o panel táctil."""

    def __init__(self, path: str, parent: QWidget | None = None):
        super().__init__("↕", parent)
        self.path = path
        self._press_position = None
        self.setObjectName("dragHandle")
        self.setFixedSize(28, 44)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Arrastrá este control con el mouse o el panel táctil para ordenar el PDF")
        self.setAccessibleName("Arrastrar para reordenar archivo")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_position = event.position().toPoint()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (
            self._press_position is None
            or not (event.buttons() & Qt.MouseButton.LeftButton)
        ):
            event.ignore()
            return
        distance = (event.position().toPoint() - self._press_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            event.ignore()
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData(DOCUMENT_MIME_TYPE, self.path.encode("utf-8"))
        drag.setMimeData(mime_data)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._press_position = None
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._press_position = None
        super().mouseReleaseEvent(event)


class DocumentCard(QFrame):
    remove_requested = Signal(str)
    move_requested = Signal(str, int)
    drop_reorder_requested = Signal(str, str, bool)
    ranges_changed = Signal()

    def __init__(self, document: DocumentInfo):
        super().__init__()
        self.document = document
        self.setObjectName("documentCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Keep the filename on a wide, dedicated row for Windows/macOS scaling.
        top = QHBoxLayout()
        self.drag_handle = DragHandle(document.path, self)
        top.addWidget(self.drag_handle)
        icon = QLabel("PDF")
        icon.setObjectName("pdfIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(42, 44)
        top.addWidget(icon)

        column = QVBoxLayout()
        name = QLabel(Path(document.path).name)
        name.setObjectName("fileName")
        name.setWordWrap(True)
        name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        name.setToolTip(document.path)
        metadata = QLabel(f"{document.page_count:,} páginas · {human_size(document.file_size)}")
        metadata.setObjectName("fileMetadata")
        metadata.setToolTip("Cantidad de páginas y tamaño del archivo")
        column.addWidget(name)
        column.addWidget(metadata)
        top.addLayout(column, 1)
        layout.addLayout(top)

        order_controls = QHBoxLayout()
        order_controls.addStretch(1)
        self.move_up_button = QPushButton("↑ Subir")
        self.move_up_button.setObjectName("secondaryButton")
        self.move_up_button.setToolTip("Mover este PDF una posición hacia arriba")
        self.move_up_button.setAccessibleName("Mover archivo hacia arriba")
        self.move_up_button.clicked.connect(lambda: self.move_requested.emit(document.path, -1))
        order_controls.addWidget(self.move_up_button)

        self.move_down_button = QPushButton("↓ Bajar")
        self.move_down_button.setObjectName("secondaryButton")
        self.move_down_button.setToolTip("Mover este PDF una posición hacia abajo")
        self.move_down_button.setAccessibleName("Mover archivo hacia abajo")
        self.move_down_button.clicked.connect(lambda: self.move_requested.emit(document.path, 1))
        order_controls.addWidget(self.move_down_button)

        remove = QPushButton("Quitar")
        remove.setObjectName("secondaryButton")
        remove.setToolTip("Quitar este archivo de la selección")
        remove.clicked.connect(lambda: self.remove_requested.emit(document.path))
        order_controls.addWidget(remove)
        layout.addLayout(order_controls)

        layout.addWidget(QLabel("Páginas que querés incluir"))
        row = QHBoxLayout()
        self.ranges = QLineEdit(f"1-{document.page_count}")
        self.ranges.setObjectName("rangeInput")
        self.ranges.setPlaceholderText("Ej.: 1-8, 12, 20-25")
        self.ranges.setClearButtonEnabled(True)
        self.ranges.setToolTip("Separá páginas y rangos con comas. También podés usar 30- hasta el final.")
        self.ranges.textChanged.connect(self._ranges_edited)
        row.addWidget(self.ranges, 1)
        visual_button = QPushButton("Elegir visualmente")
        visual_button.setObjectName("choosePagesButton")
        visual_button.setToolTip("Ver miniaturas y marcar páginas")
        visual_button.clicked.connect(self.open_page_picker)
        row.addWidget(visual_button)
        all_pages = QPushButton("Todas")
        all_pages.setObjectName("textButton")
        all_pages.clicked.connect(lambda: self.ranges.setText(f"1-{document.page_count}"))
        row.addWidget(all_pages)
        layout.addLayout(row)

        self.selection_summary = QLabel("")
        self.selection_summary.setObjectName("selectionSummary")
        layout.addWidget(self.selection_summary)
        self._update_selection_summary()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat(DOCUMENT_MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat(DOCUMENT_MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        if not event.mimeData().hasFormat(DOCUMENT_MIME_TYPE):
            super().dropEvent(event)
            return
        try:
            source_path = bytes(event.mimeData().data(DOCUMENT_MIME_TYPE)).decode("utf-8")
        except UnicodeDecodeError:
            event.ignore()
            return
        if source_path != self.document.path:
            drop_below = event.position().toPoint().y() >= self.height() // 2
            self.drop_reorder_requested.emit(source_path, self.document.path, drop_below)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _ranges_edited(self) -> None:
        self._update_selection_summary()
        self.ranges_changed.emit()

    def _update_selection_summary(self) -> None:
        try:
            count = len(parse_page_ranges(self.ranges.text(), self.document.page_count))
            label = f"{count:,} páginas seleccionadas"
            self.selection_summary.setStyleSheet("color:#64748B; font-size:12px;")
        except ValueError:
            label = "Revisá los rangos de páginas"
            self.selection_summary.setStyleSheet("color:#B42318; font-size:12px;")
        self.selection_summary.setText(label)

    def open_page_picker(self) -> None:
        dialog = PagePickerDialog(
            self.document.path, self.document.page_count, self.ranges.text(), self
        )
        result = dialog.exec()
        # Cancel queued/ongoing previews after the modal loop has returned;
        # drain the dialog-owned pool before releasing the dialog wrapper.
        dialog.thumbnail_timer.stop()
        for task in tuple(dialog.tasks):
            task.cancel()
        dialog.pool.waitForDone()
        selected_ranges = (
            dialog.selected_ranges()
            if result == QDialog.DialogCode.Accepted
            else None
        )
        dialog.deleteLater()
        if selected_ranges is not None:
            self.ranges.setText(selected_ranges)

    def selection(self) -> PdfSource:
        return PdfSource(self.document.path, self.ranges.text())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Escolar")
        self.setMinimumSize(720, 600)
        self.resize(920, 780)
        self.pool = QThreadPool(self)
        self.documents: dict[str, tuple[DocumentInfo, DocumentCard]] = {}
        self.pending: set[str] = set()
        self.tasks: set[QRunnable] = set()
        self.exporting = False
        self.custom_page_order: list[PdfPageRef] | None = None
        self.load_errors: list[tuple[str, str]] = []
        self.pending_order_notice: str | None = None

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(26, 22, 26, 20)
        root.setSpacing(15)
        header = QHBoxLayout()
        mark = QLabel("PE")
        mark.setObjectName("brandMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(44, 44)
        header.addWidget(mark)
        titles = QVBoxLayout()
        title = QLabel("PDF Escolar")
        title.setObjectName("appTitle")
        subtitle = QLabel("Elegí páginas de tus libros y reunilas en un solo PDF.")
        subtitle.setObjectName("mutedText")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)
        self.help_button = QPushButton("Cómo usar")
        self.help_button.setObjectName("secondaryButton")
        self.help_button.clicked.connect(self.show_help)
        header.addWidget(self.help_button, 0, Qt.AlignmentFlag.AlignTop)
        version = QLabel(f"Versión {__version__}")
        version.setObjectName("versionLabel")
        header.addWidget(version, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        guide = QLabel("PASO 1  Agregá tus PDF     →     PASO 2  Elegí las páginas     →     PASO 3  Creá tu PDF final")
        guide.setObjectName("guideBanner")
        guide.setWordWrap(True)
        root.addWidget(guide)

        self.drop_area = DropArea(self.choose_files)
        self.drop_area.files_dropped.connect(self.add_files)
        root.addWidget(self.drop_area)
        file_header = QHBoxLayout()
        section = QLabel("Tus archivos")
        section.setObjectName("sectionTitle")
        file_header.addWidget(section)
        file_header.addStretch(1)
        self.organize_pages_button = QPushButton("Ordenar páginas…")
        self.organize_pages_button.setObjectName("choosePagesButton")
        self.organize_pages_button.setToolTip(
            "Organizar visualmente las páginas seleccionadas de todos los PDF"
        )
        self.organize_pages_button.clicked.connect(self.organize_pages)
        self.organize_pages_button.setEnabled(False)
        file_header.addWidget(self.organize_pages_button)
        self.file_count = QLabel("Todavía no agregaste archivos")
        self.file_count.setObjectName("mutedText")
        file_header.addWidget(self.file_count)
        root.addLayout(file_header)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("documentsScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        self.cards_layout = QVBoxLayout(host)
        self.cards_layout.setContentsMargins(1, 1, 7, 1)
        self.cards_layout.setSpacing(11)
        self.cards_layout.addStretch(1)
        self.scroll.setWidget(host)
        root.addWidget(self.scroll, 1)

        footer = QFrame()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        self.progress = QProgressBar()
        self.progress.setObjectName("progressBar")
        self.progress.setTextVisible(False)
        self.progress.hide()
        footer_layout.addWidget(self.progress)
        action_row = QHBoxLayout()
        self.status = QLabel("Tus documentos se procesan en tu computadora.")
        self.status.setObjectName("mutedText")
        self.status.setWordWrap(True)
        action_row.addWidget(self.status, 1)
        self.export_button = QPushButton("Crear PDF final  →")
        self.export_button.setObjectName("primaryButton")
        self.export_button.setMinimumHeight(46)
        self.export_button.clicked.connect(self.export_pdf)
        self.export_button.setEnabled(False)
        action_row.addWidget(self.export_button)
        footer_layout.addLayout(action_row)
        root.addWidget(footer)
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget#central { background:#F5F7FB; color:#1F2937; }
            QLabel#brandMark { background:#3157C8; color:white; border-radius:12px; font-weight:800; }
            QLabel#appTitle { font-size:25px; font-weight:750; color:#172554; }
            QLabel#sectionTitle { font-size:16px; font-weight:700; color:#172554; }
            QLabel#mutedText { color:#697586; font-size:12px; }
            QLabel#versionLabel { background:#E9EEFC; color:#3554A4; border-radius:9px; padding:6px 10px; }
            QLabel#guideBanner { background:#E8EEFF; color:#2B498F; border:1px solid #D5DFFF; border-radius:10px; padding:11px 14px; font-size:13px; font-weight:650; }
            QFrame#dropArea { background:white; border:1.5px dashed #A9B9E9; border-radius:15px; }
            QLabel#dropTitle { color:#172554; font-size:17px; font-weight:700; }
            QFrame#documentCard { background:white; border:1px solid #E5EAF2; border-radius:12px; }
            QLabel#selectionSummary { padding-left: 2px; }
            QLabel#pdfIcon { background:#FCEBE9; color:#C24136; border-radius:8px; font-size:11px; font-weight:800; }
            QLabel#fileName { font-size:16px; font-weight:750; color:#172554; }
            QLabel#dragHandle { background:#F0F3FA; color:#405477; border-radius:8px; font-size:20px; font-weight:700; }
            QLabel#fileMetadata { color:#53627A; font-size:12px; }
            QLineEdit#rangeInput { background:#F9FAFC; border:1px solid #DCE3EF; border-radius:8px; padding:10px; }
            QPushButton { border:0; border-radius:8px; padding:9px 13px; font-weight:600; }
            QPushButton#primaryButton { background:#3157C8; color:white; font-size:14px; padding:12px 17px; }
            QPushButton#primaryButton:hover { background:#2547AC; }
            QPushButton#primaryButton:disabled { background:#ADB8D7; color:#F5F7FB; }
            QPushButton#secondaryButton { background:#F0F3FA; color:#31466F; }
            QPushButton#choosePagesButton { background:#E7EDFF; color:#2B4EBA; border:1px solid #CCD8FF; padding:10px 13px; }
            QPushButton#choosePagesButton:hover { background:#DCE5FF; border-color:#AEBFFF; }
            QPushButton#textButton { background:transparent; color:#3157C8; }
            QScrollArea#documentsScroll { background:transparent; }
            QProgressBar#progressBar { background:#E1E7F2; border:0; border-radius:3px; min-height:6px; max-height:6px; }
            QProgressBar#progressBar::chunk { background:#3157C8; border-radius:3px; }
        """)

    def show_help(self) -> None:
        show_notice(
            self,
            "Cómo usar PDF Escolar",
            "1. Agregá uno o varios archivos PDF con el botón o arrastrándolos a la ventana.\n\n"
            "2. En cada libro, pulsá «Elegir visualmente» para marcar las páginas que necesitás. "
            "También podés escribir números o rangos, por ejemplo 1-8, 12, 20-25.\n\n"
            "3. Ordená los libros con las flechas o arrastrando el control ↕ con el mouse o el panel táctil. "
            "Usá «Ordenar páginas…» para acomodar páginas individuales de todos los libros.\n\n"
            "4. Elegí dónde guardar el documento nuevo. Los PDF originales no se modifican "
            "y el contenido se procesa en esta computadora.",
            icon=QMessageBox.Icon.Information,
        )

    def _last_open_directory(self) -> str:
        """Return the last folder used to add PDFs, falling back to the home folder."""
        settings = QSettings()
        saved = settings.value("last_open_directory", "", type=str)
        if saved and Path(saved).is_dir():
            return saved
        return str(Path.home())

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos PDF",
            self._last_open_directory(),
            "Documentos PDF (*.pdf)",
        )
        if paths:
            self.add_files(paths)

    @Slot(list)
    def add_files(self, paths: list[str]):
        accepted = []
        for raw in paths:
            path = Path(raw).expanduser()
            if not path.is_file() or path.suffix.lower() != ".pdf":
                continue
            resolved = str(path.resolve())
            if resolved not in self.documents and resolved not in self.pending and resolved not in accepted:
                accepted.append(resolved)
        valid_pdf_paths = [
            Path(raw).expanduser().resolve()
            for raw in paths
            if Path(raw).expanduser().is_file()
            and Path(raw).expanduser().suffix.lower() == ".pdf"
        ]
        # Remember the last usable folder even if the PDFs were already loaded.
        if valid_pdf_paths:
            QSettings().setValue("last_open_directory", str(valid_pdf_paths[-1].parent))
        if not accepted:
            return
        self.pending.update(accepted)
        order_was_reset = self._invalidate_custom_page_order(
            "agregaste archivos nuevos", defer_until_loaded=True
        )
        self._refresh_drop_area_mode()
        self._update_summary()
        self.status.setText(
            "Revisando archivos… (se reinició el orden manual)."
            if order_was_reset
            else "Revisando los archivos…"
        )
        self.progress.show()
        self.progress.setRange(0, 0)
        task = InspectTask(accepted)
        task.signals.loaded.connect(self._on_loaded)
        task.signals.load_error.connect(self._on_load_error)
        task.signals.progress.connect(self._on_progress)
        task.signals.batch_finished.connect(self._on_batch_finished)
        task.signals.task_finished.connect(self._task_finished)
        self.tasks.add(task)
        self.pool.start(task)

    @Slot(str, int, int)
    def _on_loaded(self, path: str, page_count: int, size: int):
        self.pending.discard(path)
        if path in self.documents:
            return
        info = DocumentInfo(path, page_count, size)
        card = DocumentCard(info)
        card.remove_requested.connect(self.remove_file)
        card.move_requested.connect(self.move_file)
        card.drop_reorder_requested.connect(self.reorder_file_by_drop)
        card.ranges_changed.connect(self._on_page_selection_changed)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        self.documents[path] = (info, card)
        self._refresh_drop_area_mode()
        self._update_summary()

    @Slot(str, str)
    def _on_load_error(self, path: str, detail: str):
        self.pending.discard(path)
        self.load_errors.append((path, detail))
        self.status.setText(f"No se pudo agregar «{Path(path).name}».")

    @Slot(int, int, str)
    def _on_progress(self, done: int, total: int, message: str):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(done)
        self.status.setText(message)

    @Slot(str)
    def _task_finished(self, finished_token: str) -> None:
        task = next((item for item in self.tasks if str(id(item)) == finished_token), None)
        if task is None:
            return
        for signal_name in (
            "loaded",
            "load_error",
            "progress",
            "batch_finished",
            "export_finished",
            "export_error",
            "task_finished",
        ):
            signal = getattr(task.signals, signal_name)
            try:
                signal.disconnect()
            except (RuntimeError, TypeError):
                pass
        self.tasks.discard(task)

    @Slot()
    def _on_batch_finished(self):
        if not self.pending:
            self.progress.hide()
            self._refresh_drop_area_mode()
        self._update_summary()
        if self.documents:
            self.status.setText("Ingresá las páginas de cada archivo y creá el PDF final.")
        elif not self.pending:
            self.status.setText("No hay archivos cargados. Podés volver a intentarlo.")

        if not self.pending and self.pending_order_notice:
            self.status.setText(self.pending_order_notice)
            self.pending_order_notice = None

        # Avoid a chain of modal alerts when several files cannot be opened.
        if not self.pending and self.load_errors:
            errors, self.load_errors = self.load_errors, []
            count = len(errors)
            noun = "archivo" if count == 1 else "archivos"
            error_lines = [
                f"• {Path(path).name}: {friendly_pdf_load_error(detail)}"
                for path, detail in errors[:5]
            ]
            remaining = count - len(error_lines)
            if remaining:
                extra_noun = "archivo" if remaining == 1 else "archivos"
                error_lines.append(f"• Y {remaining} {extra_noun} más.")
            dialog = QMessageBox(self)
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setWindowTitle("Algunos PDF no se pudieron agregar")
            dialog.setText(f"No se pudieron agregar {count} {noun}.")
            dialog.setInformativeText(
                "Revisá estos archivos:\n"
                + "\n".join(error_lines)
                + "\n\nLos PDF que se pudieron abrir siguen disponibles."
            )
            dialog.addButton("Entendido", QMessageBox.ButtonRole.AcceptRole)
            dialog.exec()

    @Slot(str, int)
    def move_file(self, path: str, offset: int):
        ordered = list(self.documents.items())
        current_index = next((i for i, (key, _) in enumerate(ordered) if key == path), None)
        if current_index is None:
            return
        target_index = current_index + offset
        if target_index < 0 or target_index >= len(ordered):
            return
        ordered[current_index], ordered[target_index] = ordered[target_index], ordered[current_index]
        self.documents = dict(ordered)
        self._invalidate_custom_page_order("cambiaste el orden de los archivos")
        self._relayout_cards()
        self._update_summary()

    @Slot(str, str, bool)
    def reorder_file_by_drop(self, source_path: str, target_path: str, drop_below: bool):
        if source_path == target_path:
            return
        ordered = list(self.documents.items())
        source_entry = next((entry for entry in ordered if entry[0] == source_path), None)
        if source_entry is None or not any(key == target_path for key, _value in ordered):
            return
        ordered.remove(source_entry)
        target_index = next(i for i, (key, _value) in enumerate(ordered) if key == target_path)
        ordered.insert(target_index + (1 if drop_below else 0), source_entry)
        if [key for key, _value in ordered] == list(self.documents.keys()):
            return
        self.documents = dict(ordered)
        self._invalidate_custom_page_order("cambiaste el orden de los archivos")
        self._relayout_cards()
        self._update_summary()

    def _relayout_cards(self) -> None:
        for index, (_key, (_info, card)) in enumerate(self.documents.items()):
            self.cards_layout.removeWidget(card)
            self.cards_layout.insertWidget(index, card)
        self._refresh_order_buttons()

    def _refresh_order_buttons(self):
        ordered_cards = list(self.documents.values())
        last_index = len(ordered_cards) - 1
        for index, (_info, card) in enumerate(ordered_cards):
            card.move_up_button.setEnabled(index > 0)
            card.move_down_button.setEnabled(index < last_index)

    def _on_page_selection_changed(self) -> None:
        # A custom sequence represents an exact selection. Explain why it was
        # cleared instead of silently changing the export order.
        self._invalidate_custom_page_order("cambiaste la selección de páginas")
        self._update_summary()

    def _invalidate_custom_page_order(
        self, reason: str, *, defer_until_loaded: bool = False
    ) -> bool:
        if self.custom_page_order is None:
            return False
        self.custom_page_order = None
        notice = (
            f"Se quitó el orden manual porque {reason}. "
            "Podés volver a «Ordenar páginas…» para definirlo."
        )
        if defer_until_loaded and self.pending:
            self.pending_order_notice = notice
        else:
            self.status.setText(notice)
        return True

    def _refresh_drop_area_mode(self) -> None:
        self.drop_area.set_compact(bool(self.documents or self.pending))

    @Slot(str)
    def remove_file(self, path: str):
        entry = self.documents.pop(path, None)
        if entry:
            _, card = entry
            self.cards_layout.removeWidget(card)
            card.deleteLater()
            self._invalidate_custom_page_order("quitaste un archivo")
        self._refresh_drop_area_mode()
        self._update_summary()

    def _update_summary(self):
        count = len(self.documents)
        if count:
            selected_count = 0
            has_invalid_ranges = False
            for info, card in self.documents.values():
                try:
                    selected_count += len(parse_page_ranges(card.ranges.text(), info.page_count))
                except ValueError:
                    has_invalid_ranges = True
            summary = f"{count} archivo{'s' if count != 1 else ''}"
            if has_invalid_ranges:
                summary += " · Revisá las páginas"
            else:
                summary += f" · {selected_count:,} páginas seleccionadas"
            if self.custom_page_order is not None and not has_invalid_ranges:
                summary += " · orden personalizado"
            if self.pending:
                summary += " · Cargando más…"
            self.file_count.setText(summary)
        elif self.pending:
            self.file_count.setText("Revisando archivos…")
        else:
            self.file_count.setText("Todavía no agregaste archivos")
        self._refresh_order_buttons()
        self._refresh_export_state()

    def _refresh_export_state(self):
        valid_selection = bool(self.documents)
        selected_count = 0
        for info, card in self.documents.values():
            try:
                selected_count += len(parse_page_ranges(card.ranges.text(), info.page_count))
            except ValueError:
                valid_selection = False
        can_continue = (
            bool(self.documents)
            and not self.pending
            and not self.exporting
            and valid_selection
            and selected_count > 0
        )
        self.export_button.setEnabled(can_continue)
        self.organize_pages_button.setEnabled(can_continue)

    def _current_selected_pages(self) -> list[PdfPageRef]:
        pages: list[PdfPageRef] = []
        for info, card in self.documents.values():
            indexes = parse_page_ranges(card.ranges.text(), info.page_count)
            pages.extend(PdfPageRef(info.path, index) for index in indexes)
        return pages

    def organize_pages(self) -> None:
        if not self.documents or self.pending or self.exporting:
            return
        try:
            pages = (
                list(self.custom_page_order)
                if self.custom_page_order is not None
                else self._current_selected_pages()
            )
            if not pages:
                raise ValueError("Seleccioná al menos una página para poder ordenarlas.")
        except ValueError as exc:
            show_notice(
                self, "Revisá las páginas", str(exc), icon=QMessageBox.Icon.Warning
            )
            return

        dialog = PageOrderDialog(pages, self)
        result = dialog.exec()
        # Drain outstanding previews explicitly after exec() returns instead
        # of overriding QDialog.done() or adding slots to its finished signal.
        dialog.thumbnail_timer.stop()
        for task in tuple(dialog.tasks):
            task.cancel()
        dialog.thumbnail_pool.waitForDone()
        ordered_pages = (
            dialog.ordered_pages()
            if result == QDialog.DialogCode.Accepted
            else None
        )
        dialog.deleteLater()
        if ordered_pages is not None:
            self.custom_page_order = ordered_pages
            self.status.setText(
                "Orden personalizado aplicado. El PDF final respetará esta secuencia."
            )
            self._update_summary()

    def export_pdf(self):
        if not self.documents or self.pending or self.exporting:
            return

        selections: list[PdfSource] = []
        page_order: list[PdfPageRef] | None = (
            list(self.custom_page_order) if self.custom_page_order is not None else None
        )
        try:
            if page_order is not None:
                total_selected_pages = len(page_order)
                if total_selected_pages == 0:
                    raise ValueError("Seleccioná al menos una página para crear el PDF.")
            else:
                selections = [card.selection() for _, card in self.documents.values()]
                total_selected_pages = sum(
                    len(parse_page_ranges(source.page_ranges, info.page_count))
                    for (info, _card), source in zip(self.documents.values(), selections)
                )
                if total_selected_pages == 0:
                    raise ValueError("Seleccioná al menos una página para crear el PDF.")
        except ValueError as exc:
            show_notice(
                self, "Revisá las páginas", str(exc), icon=QMessageBox.Icon.Warning
            )
            return
        default = Path.home() / "Documents" / "Material_escolar.pdf"
        if not default.parent.is_dir():
            default = Path.home() / "Material_escolar.pdf"
        output, _ = QFileDialog.getSaveFileName(self, "Guardar PDF final", str(default), "Documento PDF (*.pdf)")
        if not output:
            return
        if not output.lower().endswith(".pdf"):
            output += ".pdf"
        self.exporting = True
        self._refresh_export_state()
        self.status.setText("Preparando el documento final…")
        self.progress.show()
        self.progress.setRange(0, total_selected_pages)
        self.progress.setValue(0)
        task = ExportTask(selections, output, page_order=page_order)
        task.signals.progress.connect(self._on_progress)
        task.signals.export_finished.connect(self._on_export_finished)
        task.signals.export_error.connect(self._on_export_error)
        task.signals.task_finished.connect(self._task_finished)
        self.tasks.add(task)
        self.pool.start(task)

    @Slot(int, str)
    def _on_export_finished(self, count: int, output: str):
        self.exporting = False
        self.progress.hide()
        self.status.setText(f"PDF creado correctamente: {count} páginas.")
        self._refresh_export_state()
        dialog = QMessageBox(self)
        dialog.setWindowTitle("PDF creado")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText("¡Listo! El documento PDF se guardó correctamente.")
        dialog.setInformativeText(f"{count} páginas\n{output}")
        open_folder = dialog.addButton("Abrir carpeta", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton("Cerrar", QMessageBox.ButtonRole.AcceptRole)
        dialog.exec()
        if dialog.clickedButton() == open_folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(output).parent)))

    @Slot(str)
    def _on_export_error(self, detail: str):
        self.exporting = False
        self.progress.hide()
        self.status.setText("No se pudo crear el PDF. Tus documentos originales no se modificaron.")
        self._refresh_export_state()
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle("No se pudo crear el PDF")
        dialog.setText("No pudimos crear el PDF final.")
        dialog.setInformativeText(
            friendly_export_error(detail) + "\n\nTus PDF originales no se modificaron."
        )
        dialog.addButton("Entendido", QMessageBox.ButtonRole.AcceptRole)
        dialog.exec()


