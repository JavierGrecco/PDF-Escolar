"""Tests for strict validation of application release artifacts."""

from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "prepare_release_manifest.py"
SPEC = spec_from_file_location("prepare_release_manifest", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MANIFEST = module_from_spec(SPEC)
SPEC.loader.exec_module(MANIFEST)


def _prepare_dist(dist: Path, version: str = "0.1.0-beta.2") -> list[Path]:
    names = MANIFEST.expected_asset_names(version)
    dist.mkdir(parents=True, exist_ok=True)
    assets = []
    for index, name in enumerate(names, start=1):
        path = dist / name
        path.write_bytes((f"test asset {index}\n" * index).encode("utf-8"))
        assets.append(path)
    return assets


def _write_manifest(dist: Path, version: str = "0.1.0-beta.2") -> Path:
    return MANIFEST.write_release_manifest(
        version=version,
        commit="a" * 40,
        repository="JavierGrecco/PDF-Escolar",
        run_id="12345",
        dist_dir=dist,
    )


def test_release_manifest_contains_sha256_for_every_expected_asset(tmp_path):
    assets = _prepare_dist(tmp_path)
    manifest = _write_manifest(tmp_path)
    text = manifest.read_text(encoding="utf-8")

    assert manifest.name == "SHA256SUMS.txt"
    lines = text.splitlines()
    assert lines[:5] == [
        "# PDF Escolar v0.1.0-beta.2",
        f"# Commit de origen: {'a' * 40}",
        "# Repositorio: JavierGrecco/PDF-Escolar",
        "# Compilación: https://github.com/JavierGrecco/PDF-Escolar/actions/runs/12345",
        "# SHA-256:",
    ]
    checksum_lines = [line for line in lines if len(line) > 66 and line[64:66] == "  "]
    assert len(checksum_lines) == 4
    for asset in assets:
        assert f"{sha256(asset.read_bytes()).hexdigest()}  {asset.name}" in text


def test_release_manifest_hashes_an_optional_audit_evidence_asset(tmp_path):
    assets = _prepare_dist(tmp_path)
    evidence = tmp_path / "LICENSE-AUDIT-EVIDENCE-0.1.0-beta.2.zip"
    evidence.write_bytes(b"verified license evidence bundle")

    manifest = MANIFEST.write_release_manifest(
        version="0.1.0-beta.2",
        commit="a" * 40,
        repository="JavierGrecco/PDF-Escolar",
        run_id="12345",
        dist_dir=tmp_path,
        extra_assets=(evidence.name,),
    )
    text = manifest.read_text(encoding="utf-8")

    assert len(assets) == 4
    assert f"{sha256(evidence.read_bytes()).hexdigest()}  {evidence.name}" in text
    checksum_lines = [line for line in text.splitlines() if len(line) > 66 and line[64:66] == "  "]
    assert len(checksum_lines) == 5


def test_release_manifest_rejects_missing_or_mismatched_version_extra_asset(tmp_path):
    _prepare_dist(tmp_path)
    with pytest.raises(ValueError, match="Falta un artefacto adicional"):
        MANIFEST.write_release_manifest(
            version="0.1.0-beta.2",
            commit="a" * 40,
            repository="JavierGrecco/PDF-Escolar",
            run_id="12345",
            dist_dir=tmp_path,
            extra_assets=("LICENSE-AUDIT-EVIDENCE-0.1.0-beta.2.zip",),
        )

    wrong = tmp_path / "LICENSE-AUDIT-EVIDENCE-0.1.0-beta.1.zip"
    wrong.write_bytes(b"wrong version")
    with pytest.raises(ValueError, match="corresponder a la versión"):
        MANIFEST.write_release_manifest(
            version="0.1.0-beta.2",
            commit="a" * 40,
            repository="JavierGrecco/PDF-Escolar",
            run_id="12345",
            dist_dir=tmp_path,
            extra_assets=(wrong.name,),
        )


def test_release_manifest_rejects_missing_asset(tmp_path):
    assets = _prepare_dist(tmp_path)
    assets[2].unlink()

    with pytest.raises(ValueError, match="Se esperaba exactamente un instalador"):
        _write_manifest(tmp_path)


def test_release_manifest_rejects_a_stale_installer_version(tmp_path):
    _prepare_dist(tmp_path)
    stale = tmp_path / "PDF-Escolar-Instalador-0.1.0-beta.1-Windows.exe"
    stale.write_bytes(b"older version")

    with pytest.raises(ValueError, match="exactamente un instalador de Windows"):
        _write_manifest(tmp_path)


def test_release_manifest_rejects_empty_assets(tmp_path):
    assets = _prepare_dist(tmp_path)
    assets[0].write_bytes(b"")

    with pytest.raises(ValueError, match="está vacío"):
        _write_manifest(tmp_path)


@pytest.mark.parametrize("version", ["", "../beta", "0.1", "v0.1.0-beta.2"])
def test_release_manifest_rejects_invalid_version(tmp_path, version):
    _prepare_dist(tmp_path, "0.1.0-beta.2")

    with pytest.raises(ValueError, match="Versión inválida"):
        _write_manifest(tmp_path, version)


def test_release_manifest_rejects_invalid_repository_and_run_id(tmp_path):
    _prepare_dist(tmp_path)

    with pytest.raises(ValueError, match="repositorio inválido"):
        MANIFEST.write_release_manifest(
            version="0.1.0-beta.2",
            commit="a" * 40,
            repository="not-a-repo",
            run_id="12345",
            dist_dir=tmp_path,
        )

    with pytest.raises(ValueError, match="ejecución inválido"):
        MANIFEST.write_release_manifest(
            version="0.1.0-beta.2",
            commit="a" * 40,
            repository="JavierGrecco/PDF-Escolar",
            run_id="not-a-number",
            dist_dir=tmp_path,
        )
