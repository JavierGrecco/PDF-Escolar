"""Load the third-party notices shipped with this PDF Escolar build."""

from __future__ import annotations

import sys
from pathlib import Path


NOTICE_FILENAME = "THIRD-PARTY-NOTICES.txt"


def load_third_party_notices() -> str:
    """Return the generated notices, falling back to the source-tree template."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        bundled = Path(bundle_root) / "pdf_escolar" / NOTICE_FILENAME
        try:
            return bundled.read_text(encoding="utf-8")
        except OSError:
            pass

    template = (
        Path(__file__).resolve().parents[2]
        / "packaging"
        / "app"
        / "THIRD-PARTY-NOTICES.md"
    )
    try:
        return template.read_text(encoding="utf-8")
    except OSError:
        return (
            "No se encontró el inventario de licencias en esta ejecución. "
            "Consultá la documentación del proyecto o descargá una versión "
            "oficial de PDF Escolar."
        )
