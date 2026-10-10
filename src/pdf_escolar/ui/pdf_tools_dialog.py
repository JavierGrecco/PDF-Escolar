"""Dialog for native page rotation, cropping and splitting tools."""

from __future__ import annotations

from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QRunnable, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdf_escolar.page_ranges import parse_page_ranges
from pdf_escolar.pdf_engine import inspect_pdf
from pdf_escolar.pdf_tools import crop_pdf_pages, rotate_pdf_pages, split_pdf_by_page
from pdf_escolar.ui.messages import friendly_export_error, safe_exception_detail, show_notice


class PdfToolSignals(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal(str)


class PdfToolTask(QRunnable):
    """Run a single disk operation outside the interface thread."""

    def __init__(
        self,
        operation: str,
        source: str,
        page_indexes: list[int],
        output: str,
        options: dict[str, float | int],
    ):
        super().__init__()
        self.operation = operation
        self.source = source
        self.page_indexes = page_indexes
        self.output = output
        self.options = options
        self.signals = PdfToolSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self) -> None:
        try:
            if self.operation == "rotate":
                count = rotate_pdf_pages(
                    self.source,
                    self.output,
                    self.page_indexes,
                    int(self.options["degrees"]),
                )
                result = {"type": "file", "path": self.output, "count": count}
            elif self.operation == "crop":
                count = crop_pdf_pages(
                    self.source,
                    self.output,
                    self.page_indexes,
                    left_mm=self.options["left_mm"],
                    top_mm=self.options["top_mm"],
                    right_mm=self.options["right_mm"],
                    bottom_mm=self.options["bottom_mm"],
                )
                result = {"type": "file", "path": self.output, "count": count}
            elif self.operation == "split":
                paths = split_pdf_by_page(self.source, self.output, self.page_indexes)
                result = {"type": "files", "paths": [str(path) for path in paths]}
            else:
                raise ValueError("Elegí una herramienta de PDF válida.")
            self.signals.completed.emit(result)
        except Exception as exc:
            self.signals.failed.emit(safe_exception_detail(exc))
        finally:
            self.signals.finished.emit(str(id(self)))


class PdfToolsDialog(QDialog):
    """Present focused tools that preserve the original PDF."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Herramientas PDF")
        self.setMinimumWidth(560)
        self.resize(640, 520)
        self.tasks: set[PdfToolTask] = set()
        self._busy = False
        self._close_requested = False

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        title = QLabel("Herramientas para tus PDF")
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            "Girás, recortás márgenes o separás páginas. Cada operación crea archivos nuevos; "
            "los documentos originales no se modifican."
        )
        subtitle.setObjectName("mutedText")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        source_row = QHBoxLayout()
        self.source_path = QLineEdit()
        self.source_path.setReadOnly(True)
        self.source_path.setPlaceholderText("Elegí un archivo PDF…")
        self.source_path.setAccessibleName("PDF de origen")
        source_row.addWidget(self.source_path, 1)
        self.choose_source_button = QPushButton("Elegir PDF…")
        self.choose_source_button.setObjectName("secondaryButton")
        self.choose_source_button.clicked.connect(self.choose_source)
        source_row.addWidget(self.choose_source_button)
        root.addLayout(source_row)

        operation_form = QFormLayout()
        operation_form.setSpacing(12)
        self.operation_selector = QComboBox()
        self.operation_selector.addItem("Rotar páginas", "rotate")
        self.operation_selector.addItem("Recortar márgenes", "crop")
        self.operation_selector.addItem("Separar páginas en PDF individuales", "split")
        self.operation_selector.currentIndexChanged.connect(self._update_operation_fields)
        operation_form.addRow("Qué querés hacer", self.operation_selector)
        root.addLayout(operation_form)

        self.pages_input = QLineEdit()
        self.pages_input.setPlaceholderText("Vacío = todas. Ej.: 1-4, 7, 9-12")
        self.pages_input.setToolTip(
            "Usá números y rangos separados por comas. Dejalo vacío para aplicar a todas las páginas."
        )
        pages_form = QFormLayout()
        pages_form.addRow("Páginas", self.pages_input)
        root.addLayout(pages_form)

        self.rotate_panel = QWidget()
        rotate_form = QFormLayout(self.rotate_panel)
        self.degrees_selector = QComboBox()
        self.degrees_selector.addItem("90° a la derecha", 90)
        self.degrees_selector.addItem("90° a la izquierda", -90)
        self.degrees_selector.addItem("180°", 180)
        rotate_form.addRow("Giro", self.degrees_selector)
        root.addWidget(self.rotate_panel)

        self.crop_panel = QWidget()
        crop_form = QFormLayout(self.crop_panel)
        self.margins: dict[str, QDoubleSpinBox] = {}
        for key, label in (
            ("left_mm", "Izquierdo"),
            ("top_mm", "Superior"),
            ("right_mm", "Derecho"),
            ("bottom_mm", "Inferior"),
        ):
            spin = QDoubleSpinBox()
            spin.setRange(0, 1000)
            spin.setDecimals(1)
            spin.setSingleStep(1)
            spin.setSuffix(" mm")
            spin.setToolTip("Cantidad que se oculta desde ese borde, medida en milímetros.")
            self.margins[key] = spin
            crop_form.addRow(label, spin)
        root.addWidget(self.crop_panel)

        self.split_note = QLabel(
            "Se creará un archivo por cada página elegida. Para no perder nada, "
            "la herramienta no reemplaza archivos que ya existan."
        )
        self.split_note.setObjectName("mutedText")
        self.split_note.setWordWrap(True)
        root.addWidget(self.split_note)

        self.status = QLabel("El procesamiento se realiza localmente en esta computadora.")
        self.status.setObjectName("mutedText")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.buttons = QDialogButtonBox()
        self.run_button = self.buttons.addButton(
            "Procesar PDF", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.run_button.setObjectName("primaryButton")
        self.cancel_button = self.buttons.addButton(
            "Cerrar", QDialogButtonBox.ButtonRole.RejectRole
        )
        self.cancel_button.setObjectName("secondaryButton")
        self.run_button.clicked.connect(self.run_operation)
        self.cancel_button.clicked.connect(self.reject)
        root.addWidget(self.buttons)

        self.setStyleSheet("""
            QDialog { background:#F5F7FB; color:#1F2937; }
            QLabel#dialogTitle { font-size:21px; font-weight:750; color:#172554; }
            QLabel#mutedText { color:#53627A; font-size:12px; }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background:white; border:1px solid #DCE3EF; border-radius:7px; padding:8px;
            }
            QPushButton { border:0; border-radius:8px; padding:9px 13px; font-weight:600; }
            QPushButton#primaryButton { background:#3157C8; color:white; }
            QPushButton#primaryButton:disabled { background:#ADB8D7; color:#F5F7FB; }
            QPushButton#secondaryButton { background:#E9EEF8; color:#31466F; }
        """)
        self._update_operation_fields()

    def choose_source(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Elegir PDF de origen",
            str(Path.home()),
            "Documentos PDF (*.pdf)",
        )
        if path:
            self.source_path.setText(str(Path(path).expanduser().resolve()))
            self.status.setText(f"PDF elegido: {Path(path).name}")

    def _update_operation_fields(self, *_args) -> None:
        operation = self.operation_selector.currentData()
        self.rotate_panel.setVisible(operation == "rotate")
        self.crop_panel.setVisible(operation == "crop")
        self.split_note.setVisible(operation == "split")
        self.adjustSize()

    def _selected_pages(self, source: str) -> list[int]:
        total_pages = inspect_pdf(source)
        specification = self.pages_input.text().strip()
        if not specification:
            return list(range(total_pages))
        return parse_page_ranges(specification, total_pages)

    def run_operation(self) -> None:
        if self._busy:
            return
        source = self.source_path.text().strip()
        if not source:
            show_notice(
                self,
                "Falta elegir un PDF",
                "Primero elegí el archivo PDF que querés modificar.",
                icon=QMessageBox.Icon.Warning,
            )
            return

        operation = str(self.operation_selector.currentData())
        try:
            pages = self._selected_pages(source)
            if operation == "crop" and not any(spin.value() > 0 for spin in self.margins.values()):
                raise ValueError("Indicá al menos un margen mayor que cero.")
        except Exception as exc:
            show_notice(
                self,
                "Revisá la selección",
                safe_exception_detail(exc) or "No pudimos validar las páginas.",
                icon=QMessageBox.Icon.Warning,
            )
            return

        source_path = Path(source)
        options: dict[str, float | int] = {}
        if operation == "split":
            output = QFileDialog.getExistingDirectory(
                self, "Dónde guardar las páginas separadas", str(source_path.parent)
            )
            if not output:
                return
        else:
            suffix = "_girado" if operation == "rotate" else "_recortado"
            suggestion = source_path.with_name(f"{source_path.stem}{suffix}.pdf")
            output, _ = QFileDialog.getSaveFileName(
                self, "Guardar PDF nuevo", str(suggestion), "Documento PDF (*.pdf)"
            )
            if not output:
                return
            if not output.lower().endswith(".pdf"):
                output += ".pdf"

        if operation == "rotate":
            options["degrees"] = int(self.degrees_selector.currentData())
        elif operation == "crop":
            options.update({key: spin.value() for key, spin in self.margins.items()})

        task = PdfToolTask(operation, source, pages, output, options)
        task.signals.completed.connect(self._operation_completed)
        task.signals.failed.connect(self._operation_failed)
        task.signals.finished.connect(self._task_finished)
        self.tasks.add(task)
        self._busy = True
        self._set_busy(True)
        self.status.setText("Procesando el PDF…")
        from PySide6.QtCore import QThreadPool

        QThreadPool.globalInstance().start(task)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for widget in (
            self.source_path,
            self.choose_source_button,
            self.operation_selector,
            self.pages_input,
            self.rotate_panel,
            self.crop_panel,
            self.run_button,
        ):
            widget.setEnabled(not busy)
        for spin in self.margins.values():
            spin.setEnabled(not busy)
        self.cancel_button.setEnabled(not busy)
        self.cancel_button.setText("Procesando…" if busy else "Cerrar")

    @Slot(object)
    def _operation_completed(self, result: dict) -> None:
        if result["type"] == "file":
            count = result["count"]
            path = result["path"]
            self.status.setText(f"Listo: se procesaron {count} páginas.")
            dialog_text = (
                f"Se procesaron {count} páginas.

"
                f"El PDF nuevo se guardó en:
{path}

El original sigue sin cambios."
            )
        else:
            paths = result["paths"]
            self.status.setText(f"Listo: se crearon {len(paths)} archivos PDF.")
            dialog_text = (
                f"Se crearon {len(paths)} archivos PDF separados en:
"
                f"{Path(paths[0]).parent}

El original sigue sin cambios."
            )
        show_notice(self, "Operación completada", dialog_text)

    @Slot(str)
    def _operation_failed(self, detail: str) -> None:
        self.status.setText("No pudimos completar la operación.")
        show_notice(
            self,
            "No se pudo procesar el PDF",
            friendly_export_error(detail) + "

El PDF original no se modificó.",
            icon=QMessageBox.Icon.Warning,
        )

    @Slot(str)
    def _task_finished(self, token: str) -> None:
        task = next((task for task in self.tasks if str(id(task)) == token), None)
        if task is None:
            return
        for signal, slot in (
            (task.signals.completed, self._operation_completed),
            (task.signals.failed, self._operation_failed),
            (task.signals.finished, self._task_finished),
        ):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass
        self.tasks.discard(task)
        self._set_busy(False)
        if self._close_requested:
            self.accept()

    def reject(self) -> None:
        if self._busy:
            self._close_requested = True
            self.cancel_button.setEnabled(False)
            self.status.setText("La operación está en curso. La ventana se cerrará al terminar.")
            return
        super().reject()

    def closeEvent(self, event) -> None:
        if self._busy:
            self._close_requested = True
            event.ignore()
            self.status.setText("La operación está en curso. La ventana se cerrará al terminar.")
            return
        super().closeEvent(event)
