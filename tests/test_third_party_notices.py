"""Tests for user-accessible third-party license notices."""

import importlib.util
from pathlib import Path, PurePosixPath

from pdf_escolar.third_party_notices import load_third_party_notices


def _load_manifest_generator():
    source = Path(__file__).resolve().parents[1] / "tools" / "generate_third_party_notices.py"
    spec = importlib.util.spec_from_file_location("generate_third_party_notices", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_tree_provides_a_clear_license_notice_template():
    notices = load_third_party_notices()

    assert notices.strip()
    assert "inventario completo se genera durante la compilación" in notices
    assert "revisión manual" in notices


def test_qt_license_files_with_licenses_suffix_are_detected():
    generator = _load_manifest_generator()

    assert generator.is_license_candidate(
        PurePosixPath("PySide6/Qt/lib/qtwebenginecore_licenses.rtf")
    )
    assert generator.is_license_candidate(
        PurePosixPath("PySide6_Essentials-6.12.0.dist-info/LGPL-3.0-only.txt")
    )
    assert generator.is_license_candidate(
        PurePosixPath("PySide6_Essentials-6.12.0.dist-info/GFDL-1.3-no-invariants-only.txt")
    )


def test_generated_manifest_includes_official_qt_license_texts():
    generator = _load_manifest_generator()
    manifest = generator.render_manifest()

    assert "Fuente oficial de PySide" in manifest
    assert "LGPL-3.0-only.txt" in manifest
    assert "GPL-3.0-only.txt" in manifest
    assert "13a4334f8fe46f108ad07536f612d8881ebe476e" in manifest


def test_rtf_license_notice_is_readable():
    generator = _load_manifest_generator()
    rtf = (
        r"{\rtf1\ansi Qt WebEngine License\par "
        r"Copyright Example Corp.\par "
        r"Permission is hereby granted.}"
    )

    plain_text = generator._rtf_to_text(rtf)

    assert "Qt WebEngine License" in plain_text
    assert "Copyright Example Corp." in plain_text
    assert "Permission is hereby granted." in plain_text
    assert r"\par" not in plain_text
