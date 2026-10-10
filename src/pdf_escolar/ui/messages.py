"""Mensajes en español claro para acompañar las acciones de la interfaz."""
from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def show_notice(
    parent: QWidget,
    title: str,
    message: str,
    *,
    icon: QMessageBox.Icon = QMessageBox.Icon.Information,
) -> None:
    """Show a simple notice with an explicitly Spanish confirmation button."""
    dialog = QMessageBox(parent)
    dialog.setIcon(icon)
    dialog.setWindowTitle(title)
    dialog.setText(message)
    dialog.addButton("Entendido", QMessageBox.ButtonRole.AcceptRole)
    dialog.exec()


def safe_exception_detail(error: object) -> str:
    """Safely extract a bounded diagnostic for internal error classification."""
    try:
        return str(error)[:2000]
    except Exception:
        # A broken exception formatter must not break the GUI error path too.
        return ""


def _error_reason(detail: object) -> str:
    """Return a safe classifier input without trusting arbitrary exception values."""
    if not isinstance(detail, str):
        return ""
    try:
        return str.casefold(detail)
    except Exception:
        # Error translation must never become a second error shown to the user.
        return ""


def friendly_pdf_load_error(detail: object) -> str:
    """Translate common PDF open failures without exposing library diagnostics."""
    reason = _error_reason(detail)

    if any(term in reason for term in ("password", "encrypted", "encryption", "contraseña")):
        return "Este PDF está protegido con contraseña. Usá una copia sin contraseña."

    if any(
        term in reason
        for term in (
            "permission denied",
            "access denied",
            "access is denied",
            "permissionerror",
            "errno 13",
            "winerror 5",
        )
    ):
        return "No tenés permiso para abrir este archivo. Revisá sus permisos o elegí otra copia."

    if any(
        term in reason
        for term in (
            "no such file",
            "file not found",
            "filenotfounderror",
            "does not exist",
            "errno 2",
            "winerror 2",
        )
    ):
        return "No encontramos el archivo. Puede haberse movido o eliminado."

    if any(
        term in reason
        for term in (
            "invalid pdf",
            "damaged",
            "malformed",
            "syntax error",
            "stream has ended",
            "unexpected eof",
            "end of file",
            "eof marker",
        )
    ):
        return "El archivo parece estar dañado o no tiene un formato PDF válido."

    return (
        "No pudimos abrir este archivo. Comprobá que sea un PDF válido "
        "y que no esté protegido con contraseña."
    )


def friendly_export_error(detail: object) -> str:
    """Offer a practical next step instead of displaying raw exception text."""
    reason = _error_reason(detail)

    if any(
        term in reason
        for term in (
            "no space left",
            "disk full",
            "not enough space",
            "errno 28",
            "winerror 112",
        )
    ):
        return (
            "No hay suficiente espacio para guardar el PDF. Liberá espacio "
            "o elegí otra carpeta."
        )

    if any(
        term in reason
        for term in (
            "permission denied",
            "access denied",
            "access is denied",
            "permissionerror",
            "errno 13",
            "winerror 5",
        )
    ):
        return (
            "No tenés permiso para guardar en esa carpeta. Elegí otra carpeta "
            "y volvé a intentarlo."
        )

    if any(
        term in reason
        for term in (
            "no such file",
            "file not found",
            "filenotfounderror",
            "does not exist",
            "errno 2",
            "winerror 2",
        )
    ):
        return "La carpeta elegida ya no está disponible. Elegí otra ubicación para guardar el PDF."

    return (
        "Revisá que los archivos originales sigan disponibles y que tengas espacio "
        "y permiso para guardar en la carpeta elegida."
    )


def friendly_pdf_tool_error(detail: object) -> str:
    """Explain common native-tool failures without echoing raw diagnostics."""
    reason = _error_reason(detail)

    if "ya existen archivos con esos nombres" in reason:
        return (
            "Ya hay archivos con esos nombres en la carpeta elegida. "
            "Elegí otra carpeta para no reemplazar documentos anteriores."
        )

    if "no puede reemplazar uno de los pdf originales" in reason or (
        "resultado debe guardarse en un archivo nuevo" in reason
    ):
        return "Elegí un nombre o una ubicación distintos del PDF original."

    if "sin área visible" in reason:
        return (
            "Los márgenes son demasiado grandes para una o más páginas. "
            "Reducí los valores y volvé a intentarlo."
        )

    if "debe tener extensión .pdf" in reason:
        return "Guardá el resultado con la extensión .pdf."

    if "no encontramos el pdf de origen" in reason:
        return friendly_pdf_load_error(detail)

    return friendly_export_error(detail)
