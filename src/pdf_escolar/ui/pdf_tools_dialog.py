"""Dialog for native PDF tools and optional local OCR."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot, QTimer
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
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdf_escolar.ocr_companion import (
    OCRCompanionError,
    get_installed_ocr_companion,
    install_ocr_companion,
    platform_support_error,
    run_ocr_with_companion,
)
from pdf_escolar.page_ranges import parse_page_ranges
from pdf_escolar.pdf_engine import inspect_pdf
from pdf_escolar.pdf_tools import crop_pdf_pages, rotate_pdf_pages, split_pdf_by_page
from pdf_escolar.ui.messages import friendly_pdf_tool_error, safe_exception_detail, show_notice


class PdfToolSignals(QObject):
    completed = Signal(object)
    failed = Signal(str)
    progress = Signal(int, int, str)
    finished = Signal(str)


class PdfToolTask(QRunnable):
    """Run one disk operation outside the interface thread."""

    def __init__(
        self,
        operation: str,
        source: str,
        page_indexes: list[int],
        output: str,
        options: dict[str, object],
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
                    left_mm=float(self.options["left_mm"]),
                    top_mm=float(self.options["top_mm"]),
                    right_mm=float(self.options["right_mm"]),
                    bottom_mm=float(self.options["bottom_mm"]),
                )
                result = {"type": "file", "path": self.output, "count": count}
            elif self.operation == "split":
                paths = split_pdf_by_page(self.source, self.output, self.page_indexes)
                result = {"type": "files", "paths": [str(path) for path in paths]}
            elif self.operation == "ocr":
                languages = self.options["languages"]
                if not isinstance(languages, list) or not all(
                    isinstance(language, str) for language in languages
                ):
                    raise OCRCompanionError("Elegí español, inglés o ambos idiomas.")
                count = run_ocr_with_companion(
                    self.source,
                    self.output,
                    languages=languages,
                    pages=str(self.options.get("pages_spec", "")) or None,
                )
                result = {"type": "ocr", "path": self.output, "count": count}
            else:
                raise ValueError("Elegí una herramienta de PDF válida.")
            self.signals.completed.emit(result)
        except Exception as exc:
            self.signals.failed.emit(safe_exception_detail(exc))
        finally:
            self.signals.finished.emit(str(id(self)))


class OcrCompanionInstallTask(QRunnable):
    """Download and verify the optional OCR companion without blocking the UI."""

    def __init__(self):
        super().__init__()
        self.signals = PdfToolSignals()
        self.setAutoDelete(False)

    @Slot()
    def run(self) -> None:
        try:
            helper, tag = install_ocr_companion(
                lambda done, total, message: self.signals.progress.emit(
                    done, total, message
                )
            )
            self.signals.completed.emit(
                {"type": "installed", "path": str(helper), "tag": tag}
            )
        except OCRCompanionError as exc:
            self.signals.failed.emit(str(exc))
        except Exception:
            self.signals.failed.emit(
                "No pudimos instalar el complemento OCR. Intentá nuevamente."
            )
        finally:
            self.signals.finished.emit(str(id(self)))


class PdfToolsDialog(QDialog):
    """Present focused PDF tools and the optional searchable-PDF workflow."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Herramientas PDF")
        self.setMinimumWidth(580)
        self.resize(660, 620)
        self.tasks: set[QRunnable] = set()
        self._busy = False
        self._close_requested = False
        self._current_operation_kind = "process"
        self._install_succeeded = False
        self._pending_ocr: dict[str, object] | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(13)

        title = QLabel("Herramientas para tus PDF")
        title.setObjectName("dialogTitle")
        subtitle = QLabel(
            "Girás, recortás márgenes o separás páginas. Cada operación crea archivos nuevos; "
            "los documentos originales no se modifican. El recorte oculta los bordes, pero no "
            "borra definitivamente los datos que quedan fuera del área visible."
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
        self.operation_selector.addItem("Crear PDF buscable (OCR)", "ocr")
        self.operation_selector.currentIndexChanged.connect(self._update_operation_fields)
        operation_form.addRow("Qué querés hacer", self.operation_selector)
        root.addLayout(operation_form)

        self.pages_input = QLineEdit()
        self.pages_input.setPlaceholderText("Vacío = todas. Ej.: 1-4, 7, 9-12")
        self.pages_input.setToolTip(
            "Usá números y rangos separados por comas. Dejalo vacío para aplicar a todas las páginas."
        )
        self.pages_label = QLabel("Páginas")
        pages_form = QFormLayout()
        pages_form.addRow(self.pages_label, self.pages_input)
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

        self.ocr_panel = QWidget()
        ocr_layout = QVBoxLayout(self.ocr_panel)
        ocr_layout.setContentsMargins(0, 0, 0, 0)
        ocr_layout.setSpacing(8)
        ocr_form = QFormLayout()
        self.ocr_language = QComboBox()
        self.ocr_language.addItem("Español", ["spa"])
        self.ocr_language.addItem("Español e inglés", ["spa", "eng"])
        ocr_form.addRow("Idioma del documento", self.ocr_language)
        ocr_layout.addLayout(ocr_form)
        self.ocr_status = QLabel("")
        self.ocr_status.setObjectName("mutedText")
        self.ocr_status.setWordWrap(True)
        ocr_layout.addWidget(self.ocr_status)
        self.install_ocr_button = QPushButton("Instalar complemento OCR")
        self.install_ocr_button.setObjectName("secondaryButton")
        self.install_ocr_button.clicked.connect(self.start_ocr_installation)
        ocr_layout.addWidget(self.install_ocr_button, 0)
        ocr_disclaimer = QLabel(
            "El complemento se descarga una vez desde GitHub. Tus PDF nunca se suben: "
            "el reconocimiento se hace en esta computadora y funciona sin conexión "
            "después de instalarlo."
        )
        ocr_disclaimer.setObjectName("ocrDisclaimer")
        ocr_disclaimer.setWordWrap(True)
        ocr_layout.addWidget(ocr_disclaimer)
        root.addWidget(self.ocr_panel)

        self.status = QLabel("El procesamiento se realiza localmente en esta computadora.")
        self.status.setObjectName("mutedText")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        root.addWidget(self.progress_bar)

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
            QProgressBar { background:#E1E7F2; border:0; border-radius:3px; min-height:5px; max-height:5px; }
            QProgressBar::chunk { background:#3157C8; border-radius:3px; }
        """)
        self._refresh_ocr_status()
        self._update_operation_fields()

    def _refresh_ocr_status(self) -> None:
        problem = platform_support_error()
        helper, tag = get_installed_ocr_companion()
        if problem:
            self.ocr_status.setText(problem)
            self.install_ocr_button.setEnabled(False)
            self.install_ocr_button.setText("OCR no disponible en este equipo")
        elif helper is not None and tag:
            self.ocr_status.setText(
                f"Complemento instalado ({tag}). El OCR se ejecuta localmente."
            )
            self.install_ocr_button.setEnabled(not self._busy)
            self.install_ocr_button.setText("Actualizar complemento OCR")
        else:
            self.ocr_status.setText(
                "El OCR es opcional y requiere descargar un complemento adicional la primera vez."
            )
            self.install_ocr_button.setEnabled(not self._busy)
            self.install_ocr_button.setText("Instalar complemento OCR")

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
        self.ocr_panel.setVisible(operation == "ocr")
        self.pages_label.setText("Páginas a reconocer" if operation == "ocr" else "Páginas")
        self.run_button.setText("Crear PDF buscable" if operation == "ocr" else "Procesar PDF")
        if operation == "ocr":
            self._refresh_ocr_status()
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
        if operation == "ocr":
            support_problem = platform_support_error()
            if support_problem:
                show_notice(self, "OCR no disponible", support_problem, icon=QMessageBox.Icon.Warning)
                return
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
        options: dict[str, object] = {}
        if operation == "split":
            output = QFileDialog.getExistingDirectory(
                self, "Dónde guardar las páginas separadas", str(source_path.parent)
            )
            if not output:
                return
        else:
            suffix = {
                "rotate": "_girado",
                "crop": "_recortado",
                "ocr": "_buscable",
            }.get(operation, "_nuevo")
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
        elif operation == "ocr":
            options["languages"] = list(self.ocr_language.currentData())
            options["pages_spec"] = self.pages_input.text().strip()

        pending = {
            "operation": operation,
            "source": source,
            "pages": pages,
            "output": output,
            "options": options,
        }
        if operation == "ocr" and get_installed_ocr_companion()[0] is None:
            answer = QMessageBox.question(
                self,
                "Instalar complemento OCR",
                "Para crear PDF buscables necesitamos descargar un complemento adicional desde GitHub. "
                "Puede ser una descarga grande y requiere Internet. Se instala solo para tu usuario; "
                "el contenido de tus PDF no se sube. Después podrás usar OCR sin conexión.\n\n"
                "¿Descargar e instalar el complemento ahora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._pending_ocr = pending
                self._start_ocr_installation(confirm=False)
            return

        self._start_pdf_task(pending)

    def start_ocr_installation(self) -> None:
        self._start_ocr_installation(confirm=True)

    def _start_ocr_installation(self, *, confirm: bool) -> None:
        if self._busy:
            return
        problem = platform_support_error()
        if problem:
            show_notice(self, "OCR no disponible", problem, icon=QMessageBox.Icon.Warning)
            return
        if confirm:
            answer = QMessageBox.question(
                self,
                "Instalar complemento OCR",
                "Se descargará desde GitHub el complemento de reconocimiento de texto. "
                "El paquete puede ser grande y requiere Internet; se guarda solo en tu perfil "
                "de usuario. Tus PDF permanecen en tu computadora y no se envían a Internet.\n\n"
                "¿Continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self._current_operation_kind = "install"
        self._install_succeeded = False
        task = OcrCompanionInstallTask()
        self._connect_task(task)
        self.tasks.add(task)
        self._busy = True
        self._set_busy(True)
        self.progress_bar.setRange(0, 0)
        self.status.setText("Consultando la versión del complemento OCR…")
        QThreadPool.globalInstance().start(task)

    def _start_pdf_task(self, pending: dict[str, object]) -> None:
        task = PdfToolTask(
            str(pending["operation"]),
            str(pending["source"]),
            list(pending["pages"]),  # type: ignore[arg-type]
            str(pending["output"]),
            dict(pending["options"]),  # type: ignore[arg-type]
        )
        self._current_operation_kind = "process"
        self._connect_task(task)
        self.tasks.add(task)
        self._busy = True
        self._set_busy(True)
        operation = str(pending["operation"])
        self.status.setText(
            "Reconociendo texto en el PDF. Esto puede tardar según la cantidad y calidad de las páginas…"
            if operation == "ocr"
            else "Procesando el PDF…"
        )
        if operation == "ocr":
            self.progress_bar.setRange(0, 0)
        QThreadPool.globalInstance().start(task)

    def _connect_task(self, task: QRunnable) -> None:
        task.signals.completed.connect(self._operation_completed)  # type: ignore[attr-defined]
        task.signals.failed.connect(self._operation_failed)  # type: ignore[attr-defined]
        task.signals.progress.connect(self._task_progress)  # type: ignore[attr-defined]
        task.signals.finished.connect(self._task_finished)  # type: ignore[attr-defined]

    @Slot(int, int, str)
    def _task_progress(self, done: int, total: int, message: str) -> None:
        self.status.setText(message)
        if total > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(min(100, int(done * 100 / total)))
        else:
            self.progress_bar.setRange(0, 0)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for widget in (
            self.source_path,
            self.choose_source_button,
            self.operation_selector,
            self.pages_input,
            self.rotate_panel,
            self.crop_panel,
            self.ocr_panel,
            self.run_button,
            self.install_ocr_button,
        ):
            widget.setEnabled(not busy)
        for spin in self.margins.values():
            spin.setEnabled(not busy)
        self.cancel_button.setEnabled(not busy)
        self.cancel_button.setText("Procesando…" if busy else "Cerrar")
        self.progress_bar.setVisible(busy)
        if not busy:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        self._refresh_ocr_status()

    @Slot(object)
    def _operation_completed(self, result: dict) -> None:
        result_type = result.get("type")
        if result_type == "installed":
            self._install_succeeded = True
            self._refresh_ocr_status()
            self.status.setText(f"Complemento OCR instalado ({result['tag']}).")
            if self._pending_ocr is None:
                show_notice(
                    self,
                    "Complemento OCR listo",
                    "Ya podés elegir «Crear PDF buscable (OCR)» para reconocer texto en tus escaneos.",
                )
            return

        if result_type == "ocr":
            count = int(result["count"])
            path = str(result["path"])
            self.status.setText("PDF buscable creado correctamente.")
            dialog_text = (
                f"Se creó el PDF buscable con {count} páginas.\n\n"
                f"Guardado en:\n{path}\n\nEl original sigue sin cambios."
            )
            show_notice(self, "PDF buscable creado", dialog_text)
            return

        if result_type == "file":
            count = int(result["count"])
            path = str(result["path"])
            self.status.setText(f"Listo: se procesaron {count} páginas.")
            dialog_text = (
                f"Se procesaron {count} páginas.\n\n"
                f"El PDF nuevo se guardó en:\n{path}\n\nEl original sigue sin cambios."
            )
        else:
            paths = result["paths"]
            self.status.setText(f"Listo: se crearon {len(paths)} archivos PDF.")
            dialog_text = (
                f"Se crearon {len(paths)} archivos PDF separados en:\n"
                f"{Path(paths[0]).parent}\n\nEl original sigue sin cambios."
            )
        show_notice(self, "Operación completada", dialog_text)

    @Slot(str)
    def _operation_failed(self, detail: str) -> None:
        self._install_succeeded = False
        self.status.setText("No pudimos completar la operación.")
        if self._current_operation_kind == "install":
            self._pending_ocr = None
            message = detail or "No pudimos instalar el complemento OCR. Intentá nuevamente."
            title = "No se pudo instalar el complemento OCR"
        else:
            message = friendly_pdf_tool_error(detail) + "\n\nEl PDF original no se modificó."
            title = "No se pudo procesar el PDF"
        show_notice(self, title, message, icon=QMessageBox.Icon.Warning)

    @Slot(str)
    def _task_finished(self, token: str) -> None:
        task = next((task for task in self.tasks if str(id(task)) == token), None)
        if task is None:
            return
        for signal, slot in (
            (task.signals.completed, self._operation_completed),  # type: ignore[attr-defined]
            (task.signals.failed, self._operation_failed),  # type: ignore[attr-defined]
            (task.signals.progress, self._task_progress),  # type: ignore[attr-defined]
            (task.signals.finished, self._task_finished),  # type: ignore[attr-defined]
        ):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass
        was_install = self._current_operation_kind == "install"
        self.tasks.discard(task)
        self._set_busy(False)
        if self._close_requested:
            self._pending_ocr = None
            self.accept()
            return
        if was_install:
            pending = self._pending_ocr if self._install_succeeded else None
            self._pending_ocr = None
            self._install_succeeded = False
            if pending is not None:
                QTimer.singleShot(0, lambda pending=pending: self._start_pdf_task(pending))
            return

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
