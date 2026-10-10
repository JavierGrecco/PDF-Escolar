"""Comprobaciones para que las excepciones nunca se muestren tal cual en la interfaz."""
from __future__ import annotations

import pytest

from pdf_escolar.ui.messages import (
    friendly_export_error,
    friendly_pdf_load_error,
    safe_exception_detail,
)


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("Password required to open document", "protegido con contraseña"),
        ("PermissionError: [Errno 13] Permission denied", "No tenés permiso"),
        ("[WinError 5] Access is denied", "No tenés permiso"),
        ("FileNotFoundError: [Errno 2] No such file or directory", "No encontramos el archivo"),
        ("invalid PDF: malformed object stream", "dañado"),
        (
            "RuntimeError: stream ended unexpectedly at object offset 54321",
            "No pudimos abrir",
        ),
        ("RuntimeError: unexpected internal parser code 54321", "No pudimos abrir"),
    ],
)
def test_pdf_load_errors_are_friendly_and_never_echo_diagnostics(detail, expected):
    message = friendly_pdf_load_error(detail)
    assert expected in message
    assert detail not in message
    assert "Traceback" not in message
    assert "RuntimeError" not in message
    assert "PermissionError" not in message


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("OSError: No space left on device", "No hay suficiente espacio"),
        ("[WinError 112] There is not enough space on the disk", "No hay suficiente espacio"),
        ("PermissionError: [WinError 5] Access is denied", "No tenés permiso"),
        ("FileNotFoundError: [Errno 2] No such file or directory", "La carpeta elegida"),
        ("RuntimeError: internal object 54321", "Revisá que los archivos originales"),
    ],
)
def test_export_errors_are_friendly_and_never_echo_diagnostics(detail, expected):
    message = friendly_export_error(detail)
    assert expected in message
    assert detail not in message
    assert "Traceback" not in message
    assert "RuntimeError" not in message
    assert "PermissionError" not in message


@pytest.mark.parametrize("detail", [None, 123, object()])
def test_unexpected_error_values_fall_back_to_spanish_messages(detail):
    assert "No pudimos abrir este archivo" in friendly_pdf_load_error(detail)
    assert "Revisá que los archivos originales" in friendly_export_error(detail)


def test_a_broken_exception_formatter_cannot_break_error_handling():
    class UnprintableError(Exception):
        def __str__(self):
            raise RuntimeError("diagnóstico interno")

    assert safe_exception_detail(UnprintableError()) == ""
