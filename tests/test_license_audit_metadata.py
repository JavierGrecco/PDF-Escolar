"""Tests for build-specific third-party license audit evidence."""

import hashlib
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "write_license_audit_metadata.py"
SPEC = importlib.util.spec_from_file_location("write_license_audit_metadata", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _inputs(tmp_path: Path) -> dict:
    notice = tmp_path / "THIRD-PARTY-NOTICES.txt"
    portable = tmp_path / "PDF-Escolar.exe"
    installer = tmp_path / "PDF-Escolar-Instalador-0.1.0-dev.251-Windows.exe"
    notice.write_text("Avisos de componentes de terceros\n", encoding="utf-8")
    portable.write_bytes(b"portable package")
    installer.write_bytes(b"windows installer")
    return {
        "version": "0.1.0-dev.251",
        "platform_name": "Windows",
        "architecture": "x64",
        "commit": "a" * 40,
        "repository": "JavierGrecco/PDF-Escolar",
        "run_id": "123456",
        "notice_file": notice,
        "output_path": tmp_path / "LICENSE-AUDIT-METADATA.txt",
        "package_paths": [portable, installer],
    }


def test_metadata_records_build_identity_notices_and_package_hashes(tmp_path):
    kwargs = _inputs(tmp_path)
    output = AUDIT.write_metadata(**kwargs)
    text = output.read_text(encoding="utf-8")

    assert output.name == "LICENSE-AUDIT-METADATA.txt"
    assert "Versión: 0.1.0-dev.251" in text
    assert "Plataforma: Windows" in text
    assert "Arquitectura: x64" in text
    assert f"Commit de origen: {'a' * 40}" in text
    assert "https://github.com/JavierGrecco/PDF-Escolar/actions/runs/123456" in text
    notice_hash = hashlib.sha256(kwargs["notice_file"].read_bytes()).hexdigest()
    assert f"SHA-256: {notice_hash}" in text

    for package in kwargs["package_paths"]:
        digest = hashlib.sha256(package.read_bytes()).hexdigest()
        assert f"Archivo: {package.name}" in text
        assert f"Tamaño: {package.stat().st_size} bytes" in text
        assert f"SHA-256: {digest}" in text
    assert "no certifica cumplimiento legal" in text


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("version", "../0.1.0", "Versión inválida"),
        ("platform_name", "Linux", "Combinación de plataforma"),
        ("architecture", "arm64", "Combinación de plataforma"),
        ("commit", "abc123", "SHA completo"),
        ("repository", "PDF-Escolar", "propietario/repositorio"),
        ("run_id", "not-a-number", "numérico"),
    ],
)
def test_invalid_build_identity_is_rejected(tmp_path, field, value, error):
    kwargs = _inputs(tmp_path)
    kwargs[field] = value

    with pytest.raises(ValueError, match=error):
        AUDIT.render_metadata(**kwargs)


def test_empty_notice_file_is_rejected_without_replacing_existing_output(tmp_path):
    kwargs = _inputs(tmp_path)
    kwargs["output_path"].write_text("previous evidence\n", encoding="utf-8")
    kwargs["notice_file"].write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="avisos de terceros está vacío"):
        AUDIT.write_metadata(**kwargs)

    assert kwargs["output_path"].read_text(encoding="utf-8") == "previous evidence\n"
    assert not list(tmp_path.glob(".LICENSE-AUDIT-METADATA.txt.*.tmp"))


def test_missing_or_empty_package_fails_closed(tmp_path):
    kwargs = _inputs(tmp_path)
    kwargs["package_paths"][0].unlink()
    with pytest.raises(ValueError, match="No existe el archivo de paquete distribuible"):
        AUDIT.render_metadata(**kwargs)

    kwargs = _inputs(tmp_path)
    kwargs["package_paths"][0].write_bytes(b"")
    with pytest.raises(ValueError, match="paquete distribuible está vacío"):
        AUDIT.render_metadata(**kwargs)


def test_duplicate_package_paths_or_names_are_rejected(tmp_path):
    kwargs = _inputs(tmp_path)
    kwargs["package_paths"].append(kwargs["package_paths"][0])
    with pytest.raises(ValueError, match="más de una vez"):
        AUDIT.render_metadata(**kwargs)

    kwargs = _inputs(tmp_path)
    duplicate_dir = tmp_path / "another"
    duplicate_dir.mkdir()
    duplicate = duplicate_dir / kwargs["package_paths"][0].name
    duplicate.write_bytes(b"not the same package")
    kwargs["package_paths"].append(duplicate)
    with pytest.raises(ValueError, match="mismo nombre"):
        AUDIT.render_metadata(**kwargs)


def test_platform_architecture_pairs_match_supported_targets(tmp_path):
    kwargs = _inputs(tmp_path)
    kwargs["platform_name"] = "macOS"
    kwargs["architecture"] = "Apple-Silicon"

    metadata = AUDIT.render_metadata(**kwargs)

    assert "Plataforma: macOS" in metadata
    assert "Arquitectura: Apple-Silicon" in metadata


def test_ci_uploads_audit_evidence_as_separate_artifacts():
    workflow = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "build.yml"
    ).read_text(encoding="utf-8")

    assert "name: license-audit-windows" in workflow
    expected_mac_name = "name: license-audit-macos-" + "$" + "{{ matrix.arch_slug }}"
    assert expected_mac_name in workflow
    assert workflow.count("dist/LICENSE-AUDIT-METADATA.txt") >= 2
    assert "name: pdf-escolar-windows" in workflow
    assert "pattern: pdf-escolar-*" in workflow
