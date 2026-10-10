from __future__ import annotations

import stat
import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pikepdf
import pytest

from pdf_escolar import ocr_companion


def make_pdf(path: Path, width: int = 200) -> None:
    with pikepdf.Pdf.new() as pdf:
        pdf.add_blank_page(page_size=(width, 300))
        pdf.save(path)


def page_width(path: Path) -> float:
    with pikepdf.open(path) as pdf:
        return float(pdf.pages[0].mediabox[2])


def test_platform_asset_selection(monkeypatch):
    monkeypatch.setattr(ocr_companion.sys, "platform", "win32")
    monkeypatch.setattr(ocr_companion.platform, "machine", lambda: "AMD64")
    assert ocr_companion.expected_asset_name() == "PDF-Escolar-OCR-Windows-x64.zip"

    monkeypatch.setattr(ocr_companion.sys, "platform", "darwin")
    monkeypatch.setattr(ocr_companion.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(ocr_companion.platform, "mac_ver", lambda: ("15.0.0", ("", "", ""), ""))
    assert ocr_companion.expected_asset_name() == "PDF-Escolar-OCR-macOS-Apple-Silicon.zip"

    monkeypatch.setattr(ocr_companion.platform, "machine", lambda: "x86_64")
    assert ocr_companion.expected_asset_name() == "PDF-Escolar-OCR-macOS-Intel.zip"


def test_ocr_companion_refuses_unsupported_macos(monkeypatch):
    monkeypatch.setattr(ocr_companion.sys, "platform", "darwin")
    monkeypatch.setattr(ocr_companion.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(ocr_companion.platform, "mac_ver", lambda: ("10.15.7", ("", "", ""), ""))

    message = ocr_companion.platform_support_error()

    assert message is not None
    assert "macOS 14 o posterior" in message
    with pytest.raises(ocr_companion.OCRCompanionError, match="macOS 14"):
        ocr_companion.expected_asset_name()


def test_safe_extract_rejects_zip_slip(tmp_path):
    archive_path = tmp_path / "unsafe.zip"
    destination = tmp_path / "destination"
    destination.mkdir()
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("PDF-Escolar-OCR/helper.txt", "ok")
        archive.writestr("../outside.txt", "malicioso")

    with pytest.raises(ocr_companion.OCRCompanionError, match="ruta no segura"):
        ocr_companion._safe_extract(archive_path, destination)

    assert not (tmp_path / "outside.txt").exists()


def test_safe_extract_preserves_executable_permissions(tmp_path):
    archive_path = tmp_path / "companion.zip"
    destination = tmp_path / "destination"
    destination.mkdir()
    info = zipfile.ZipInfo("PDF-Escolar-OCR/PDF-Escolar-OCR")
    info.external_attr = (stat.S_IFREG | 0o755) << 16
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(info, "binary placeholder")

    ocr_companion._safe_extract(archive_path, destination)

    extracted = destination / "PDF-Escolar-OCR" / "PDF-Escolar-OCR"
    assert extracted.read_text(encoding="utf-8") == "binary placeholder"
    assert extracted.stat().st_mode & stat.S_IXUSR


def test_run_ocr_uses_temporary_output_and_preserves_existing_file_on_failure(
    tmp_path, monkeypatch
):
    source = tmp_path / "scan.pdf"
    destination = tmp_path / "existing.pdf"
    helper = tmp_path / "PDF-Escolar-OCR"
    helper.write_text("not executed by the mocked subprocess", encoding="utf-8")
    make_pdf(source, 200)
    make_pdf(destination, 800)
    original_run = ocr_companion.subprocess.run

    def failed_run(arguments, **kwargs):
        output = Path(arguments[arguments.index("--output") + 1])
        assert output != destination
        output.write_text("not a PDF", encoding="utf-8")
        return SimpleNamespace(returncode=1, stderr="internal error", stdout="")

    monkeypatch.setattr(ocr_companion, "get_installed_ocr_companion", lambda: (helper, "ocr-engine-v1.0.0"))
    monkeypatch.setattr(ocr_companion.subprocess, "run", failed_run)

    with pytest.raises(ocr_companion.OCRCompanionError, match="No pudimos crear el PDF buscable"):
        ocr_companion.run_ocr_with_companion(
            str(source), str(destination), languages=["spa"]
        )

    assert page_width(destination) == 800
    monkeypatch.setattr(ocr_companion.subprocess, "run", original_run)


def test_run_ocr_publishes_valid_result_only_after_verification(tmp_path, monkeypatch):
    source = tmp_path / "scan.pdf"
    destination = tmp_path / "existing.pdf"
    helper = tmp_path / "PDF-Escolar-OCR"
    helper.write_text("not executed by the mocked subprocess", encoding="utf-8")
    make_pdf(source, 200)
    make_pdf(destination, 800)

    def successful_run(arguments, **kwargs):
        output = Path(arguments[arguments.index("--output") + 1])
        assert output != destination
        make_pdf(output, 400)
        return SimpleNamespace(returncode=0, stderr="", stdout="Listo")

    monkeypatch.setattr(ocr_companion, "get_installed_ocr_companion", lambda: (helper, "ocr-engine-v1.0.0"))
    monkeypatch.setattr(ocr_companion.subprocess, "run", successful_run)

    count = ocr_companion.run_ocr_with_companion(
        str(source), str(destination), languages=["spa"], pages="1"
    )

    assert count == 1
    assert page_width(destination) == 400
    assert page_width(source) == 200
