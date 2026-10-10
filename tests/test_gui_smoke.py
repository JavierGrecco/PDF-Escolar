"""Smoke test for the desktop window on systems with Qt GUI libraries."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    from pdf_escolar.ui.main_window import MainWindow
except ImportError as exc:
    # Some Linux runners lack system libraries needed by Qt. Skip only those
    # known runtime-library errors; application import regressions must fail CI.
    detail = str(exc)
    missing_qt_system_library = any(
        library in detail
        for library in (
            "libEGL.so",
            "libGL.so",
            "libxkbcommon.so",
            "libxcb",
            "libX11.so",
            "libXrender.so",
        )
    )
    if sys.platform.startswith("linux") and missing_qt_system_library:
        pytest.skip(
            f"Qt requires a system library unavailable on this Linux runner: {exc}",
            allow_module_level=True,
        )
    raise


@pytest.fixture(scope="session")
def application():
    return QApplication.instance() or QApplication([])


def test_main_window_starts_in_a_safe_empty_state(application):
    window = MainWindow()
    try:
        assert window.windowTitle() == "PDF Escolar"
        assert not window.export_button.isEnabled()
        assert "Todavía no agregaste archivos" in window.file_count.text()
    finally:
        window.close()
