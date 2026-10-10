"""Accessible desktop interface for PDF Escolar."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal, Slot, QUrl
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QProgressBar, QScrollArea, QVBoxLayout, QWidget
)
from pdf_escolar import __version__
from pdf_escolar.page_ranges import parse_page_ranges
from pdf_escolar.pdf_engine import PdfSource, combine_selected_pages, inspect_pdf
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


class InspectTask(QRunnable):
    def __init__(self, paths: list[str]):
        super().__init__()
        self.paths = paths
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        for index, path in enumerate(self.paths, start=1):
            try:
                self.signals.loaded.emit(path, inspect_pdf(path), os.path.getsize(path))
            except Exception as exc:
                self.signals.load_error.emit(path, str(exc))
            self.signals.progress.emit(index, len(self.paths), f"Revisando {Path(path).name}…")
        self.signals.batch_finished.emit()


class ExportTask(QRunnable):
    def __init__(self, sources: list[PdfSource], output_path: str):
        super().__init__()
        self.sources, self.output_path = sources, output_path
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            def report(done, total, message):
                self.signals.progress.emit(done, total, message)
            count = combine_selected_pages(self.sources, self.output_path, report)
            self.signals.export_finished.emit(count, self.output_path)
        except Exception as exc:
            self.signals.export_error.emit(str(exc))


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

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        self.files_dropped.emit(paths)
        event.acceptProposedAction()


class DocumentCard(QFrame):
    remove_requested = Signal(str)
    move_requested = Signal(str, int)
    ranges_changed = Signal()

    def __init__(self, document: DocumentInfo):
        super().__init__()
        self.document = document
        self.setObjectName("documentCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        top = QHBoxLayout()
        icon = QLabel("PDF")
        icon.setObjectName("pdfIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(42, 44)
        top.addWidget(icon)
        column = QVBoxLayout()
        name = QLabel(Path(document.path).name)
        name.setObjectName("fileName")
        name.setWordWrap(True)
        name.setToolTip(document.path)
        metadata = QLabel(f"{document.page_count:,} páginas · {human_size(document.file_size)}")
        metadata.setObjectName("mutedText")
        column.addWidget(name)
        column.addWidget(metadata)
        top.addLayout(column, 1)
        order_controls = QHBoxLayout()
        self.move_up_button = QPushButton("↑")
        self.move_up_button.setObjectName("secondaryButton")
        self.move_up_button.setToolTip("Mover este PDF antes")
        self.move_up_button.setAccessibleName("Mover archivo hacia arriba")
        self.move_up_button.setFixedWidth(38)
        self.move_up_button.clicked.connect(lambda: self.move_requested.emit(document.path, -1))
        order_controls.addWidget(self.move_up_button)

        self.move_down_button = QPushButton("↓")
        self.move_down_button.setObjectName("secondaryButton")
        self.move_down_button.setToolTip("Mover este PDF después")
        self.move_down_button.setAccessibleName("Mover archivo hacia abajo")
        self.move_down_button.setFixedWidth(38)
        self.move_down_button.clicked.connect(lambda: self.move_requested.emit(document.path, 1))
        order_controls.addWidget(self.move_down_button)

        remove = QPushButton("Quitar")
        remove.setObjectName("secondaryButton")
        remove.setToolTip("Quitar este archivo de la selección")
        remove.clicked.connect(lambda: self.remove_requested.emit(document.path))
        order_controls.addWidget(remove)
        top.addLayout(order_controls, 0)
        layout.addLayout(top)
        layout.addWidget(QLabel("Páginas que querés incluir"))
        row = QHBoxLayout()
        self.ranges = QLineEdit(f"1-{document.page_count}")
        self.ranges.setObjectName("rangeInput")
        self.ranges.setPlaceholderText("Ej.: 1-8, 12, 20-25")
        self.ranges.setClearButtonEnabled(True)
        self.ranges.setToolTip("Separá páginas y rangos con comas. También podés usar 30- hasta el final.")
        self.ranges.textChanged.connect(self.ranges_changed.emit)
        row.addWidget(self.ranges, 1)
        visual_button = QPushButton("Elegir visualmente")
        visual_button.setObjectName("secondaryButton")
        visual_button.setToolTip("Ver miniaturas y marcar páginas")
        visual_button.clicked.connect(self.open_page_picker)
        row.addWidget(visual_button)
        all_pages = QPushButton("Todas")
        all_pages.setObjectName("textButton")
        all_pages.clicked.connect(lambda: self.ranges.setText(f"1-{document.page_count}"))
        row.addWidget(all_pages)
        layout.addLayout(row)

    def open_page_picker(self) -> None:
        dialog = PagePickerDialog(
            self.document.path, self.document.page_count, self.ranges.text(), self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.ranges.setText(dialog.selected_ranges())

    def selection(self) -> PdfSource:
        return PdfSource(self.document.path, self.ranges.text())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Escolar")
        self.setMinimumSize(720, 600)
        self.resize(920, 780)
        self.pool = QThreadPool.globalInstance()
        self.documents: dict[str, tuple[DocumentInfo, DocumentCard]] = {}
        self.pending: set[str] = set()
        self.tasks: set[QRunnable] = set()
        self.exporting = False

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
        version = QLabel(f"Versión {__version__}")
        version.setObjectName("versionLabel")
        header.addWidget(version, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        self.drop_area = DropArea(self.choose_files)
        self.drop_area.files_dropped.connect(self.add_files)
        root.addWidget(self.drop_area)
        file_header = QHBoxLayout()
        section = QLabel("Tus archivos")
        section.setObjectName("sectionTitle")
        file_header.addWidget(section)
        file_header.addStretch(1)
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
            QFrame#dropArea { background:white; border:1.5px dashed #A9B9E9; border-radius:15px; }
            QLabel#dropTitle { color:#172554; font-size:17px; font-weight:700; }
            QFrame#documentCard { background:white; border:1px solid #E5EAF2; border-radius:12px; }
            QLabel#pdfIcon { background:#FCEBE9; color:#C24136; border-radius:8px; font-size:11px; font-weight:800; }
            QLabel#fileName { font-size:14px; font-weight:700; }
            QLineEdit#rangeInput { background:#F9FAFC; border:1px solid #DCE3EF; border-radius:8px; padding:10px; }
            QPushButton { border:0; border-radius:8px; padding:9px 13px; font-weight:600; }
            QPushButton#primaryButton { background:#3157C8; color:white; font-size:14px; padding:12px 17px; }
            QPushButton#primaryButton:hover { background:#2547AC; }
            QPushButton#primaryButton:disabled { background:#ADB8D7; color:#F5F7FB; }
            QPushButton#secondaryButton { background:#F0F3FA; color:#31466F; }
            QPushButton#textButton { background:transparent; color:#3157C8; }
            QScrollArea#documentsScroll { background:transparent; }
            QProgressBar#progressBar { background:#E1E7F2; border:0; border-radius:3px; min-height:6px; max-height:6px; }
            QProgressBar#progressBar::chunk { background:#3157C8; border-radius:3px; }
        """)

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos PDF", str(Path.home()), "Documentos PDF (*.pdf)")
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
        if not accepted:
            return
        self.pending.update(accepted)
        self._update_summary()
        self.status.setText("Revisando los archivos…")
        self.progress.show()
        self.progress.setRange(0, 0)
        task = InspectTask(accepted)
        task.signals.loaded.connect(self._on_loaded)
        task.signals.load_error.connect(self._on_load_error)
        task.signals.progress.connect(self._on_progress)
        task.signals.batch_finished.connect(self._on_batch_finished)
        self.tasks.add(task)
        task.signals.batch_finished.connect(lambda *args, current=task: self.tasks.discard(current))
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
        card.ranges_changed.connect(self._refresh_export_state)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        self.documents[path] = (info, card)
        self._update_summary()

    @Slot(str, str)
    def _on_load_error(self, path: str, detail: str):
        self.pending.discard(path)
        self.status.setText(f"No se pudo leer {Path(path).name}.")
        QMessageBox.warning(self, "No se pudo leer el PDF",
            f"No pudimos abrir «{Path(path).name}».\n\nComprobá que el archivo no tenga contraseña y que sea legible.\n\nDetalle técnico: {detail}")

    @Slot(int, int, str)
    def _on_progress(self, done: int, total: int, message: str):
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(done)
        self.status.setText(message)

    @Slot()
    def _on_batch_finished(self):
        if not self.pending:
            self.progress.hide()
        self._update_summary()
        if self.documents:
            self.status.setText("Ingresá las páginas de cada archivo y creá el PDF final.")
        elif not self.pending:
            self.status.setText("No hay archivos cargados. Podés volver a intentarlo.")

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

    @Slot(str)
    def remove_file(self, path: str):
        entry = self.documents.pop(path, None)
        if entry:
            _, card = entry
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self._update_summary()

    def _update_summary(self):
        count = len(self.documents)
        if count:
            self.file_count.setText(f"{count} archivo{'s' if count != 1 else ''}")
        elif self.pending:
            self.file_count.setText("Revisando archivos…")
        else:
            self.file_count.setText("Todavía no agregaste archivos")
        self._refresh_order_buttons()
        self._refresh_export_state()

    def _refresh_export_state(self):
        self.export_button.setEnabled(bool(self.documents) and not self.pending and not self.exporting)

    def export_pdf(self):
        if not self.documents or self.pending or self.exporting:
            return
        selections = [card.selection() for _, card in self.documents.values()]
        try:
            for (info, _card), source in zip(self.documents.values(), selections):
                parse_page_ranges(source.page_ranges, info.page_count)
        except ValueError as exc:
            QMessageBox.warning(self, "Revisá las páginas", str(exc))
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
        self.progress.setRange(0, len(selections))
        self.progress.setValue(0)
        task = ExportTask(selections, output)
        task.signals.progress.connect(self._on_progress)
        task.signals.export_finished.connect(self._on_export_finished)
        task.signals.export_error.connect(self._on_export_error)
        self.tasks.add(task)
        task.signals.export_finished.connect(lambda *args, current=task: self.tasks.discard(current))
        task.signals.export_error.connect(lambda *args, current=task: self.tasks.discard(current))
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
        self.status.setText("No se pudo crear el PDF.")
        self._refresh_export_state()
        QMessageBox.critical(self, "No se pudo crear el PDF",
            "No se generó el documento final. Revisá el espacio disponible y que los archivos sean accesibles.\n\n"
            f"Detalle técnico: {detail}")
