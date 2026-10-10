"""Application entry point."""
import sys
from PySide6.QtWidgets import QApplication
from pdf_escolar import __version__
from pdf_escolar.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Escolar")
    app.setOrganizationName("PDF Escolar")
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    return app.exec()
