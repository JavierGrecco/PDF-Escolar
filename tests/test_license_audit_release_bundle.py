"""Tests for assembling permanent license evidence into a Release asset."""

import importlib.util
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUNDLE = _load_module(
    "prepare_license_audit_release_bundle",
    ROOT / "tools" / "prepare_license_audit_release_bundle.py",
)
METADATA = _load_module(
    "write_license_audit_metadata",
    ROOT / "tools" / "write_license_audit_metadata.py",
)


def _inputs(tmp_path: Path):
    version = "0.1.0-beta.2"
    commit = "a" * 40
    repository = "JavierGrecco/PDF-Escolar"
    run_id = "123456"
    dist = tmp_path / "dist"
    evidence = tmp_path / "evidence"
    dist.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)

    for artifact_name, platform_name, architecture, _folder in BUNDLE.PLATFORMS:
        if platform_name == "Windows":
            package_names = [
                "PDF-Escolar.exe",
                f"PDF-Escolar-Instalador-{version}-Windows.exe",
            ]
        else:
            package_names = [
                f"PDF-Escolar-Instalador-{version}-macOS-{architecture}.dmg",
                f"PDF-Escolar-macOS-{version}-{architecture}.zip",
            ]
        packages = []
        for index, name in enumerate(package_names, start=1):
            path = dist / name
            path.write_bytes(f"{artifact_name} package {index}\n".encode("utf-8"))
            packages.append(path)

        artifact_dir = evidence / artifact_name
        artifact_dir.mkdir(parents=True, exist_ok=True)
        notice_path = artifact_dir / "THIRD-PARTY-NOTICES.txt"
        notice_path.write_text(
            f"Generated notice for {platform_name}/{architecture}\n",
            encoding="utf-8",
        )
        metadata_path = artifact_dir / "LICENSE-AUDIT-METADATA.txt"
        metadata_text = METADATA.render_metadata(
            version=version,
            platform_name=platform_name,
            architecture=architecture,
            commit=commit,
            repository=repository,
            run_id=run_id,
            notice_file=notice_path,
            output_path=metadata_path,
            package_paths=packages,
        )
        metadata_path.write_text(metadata_text, encoding="utf-8")

    return {
        "version": version,
        "commit": commit,
        "repository": repository,
        "run_id": run_id,
        "dist_dir": dist,
        "evidence_dir": evidence,
    }


def test_release_bundle_contains_all_six_notices_and_metadata_files(tmp_path):
    kwargs = _inputs(tmp_path)
    output = BUNDLE.create_release_bundle(**kwargs)

    assert output.name == "LICENSE-AUDIT-EVIDENCE-0.1.0-beta.2.zip"
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert names == {
            "Windows-x64/THIRD-PARTY-NOTICES.txt",
            "Windows-x64/LICENSE-AUDIT-METADATA.txt",
            "macOS-Intel/THIRD-PARTY-NOTICES.txt",
            "macOS-Intel/LICENSE-AUDIT-METADATA.txt",
            "macOS-Apple-Silicon/THIRD-PARTY-NOTICES.txt",
            "macOS-Apple-Silicon/LICENSE-AUDIT-METADATA.txt",
        }
        windows = archive.read("Windows-x64/LICENSE-AUDIT-METADATA.txt").decode("utf-8")
        assert "Versión: 0.1.0-beta.2" in windows
        assert f"Commit de origen: {'a' * 40}" in windows
        assert "Archivo: PDF-Escolar.exe" in windows
        assert all(not name.endswith((".exe", ".dmg", ".zip")) for name in names)


def test_release_bundle_rejects_a_modified_package_hash(tmp_path):
    kwargs = _inputs(tmp_path)
    package = kwargs["dist_dir"] / "PDF-Escolar.exe"
    original_size = package.stat().st_size
    package.write_bytes(b"X" * original_size)

    with pytest.raises(ValueError, match="SHA-256 difiere"):
        BUNDLE.create_release_bundle(**kwargs)

    assert not (kwargs["dist_dir"] / "LICENSE-AUDIT-EVIDENCE-0.1.0-beta.2.zip").exists()


def test_release_bundle_rejects_modified_notice_text(tmp_path):
    kwargs = _inputs(tmp_path)
    notice = kwargs["evidence_dir"] / "license-audit-windows" / "THIRD-PARTY-NOTICES.txt"
    notice.write_text("content changed after metadata generation\n", encoding="utf-8")

    with pytest.raises(ValueError, match="avisos no coinciden"):
        BUNDLE.create_release_bundle(**kwargs)


def test_release_bundle_rejects_wrong_commit_or_version(tmp_path):
    kwargs = _inputs(tmp_path)
    kwargs["commit"] = "b" * 40
    with pytest.raises(ValueError, match="Commit de origen"):
        BUNDLE.create_release_bundle(**kwargs)

    kwargs = _inputs(tmp_path)
    kwargs["version"] = "0.1.0-beta.1"
    with pytest.raises(ValueError, match="Versión"):
        BUNDLE.create_release_bundle(**kwargs)


def test_release_bundle_fails_if_any_platform_evidence_is_missing(tmp_path):
    kwargs = _inputs(tmp_path)
    (kwargs["evidence_dir"] / "license-audit-macos-Intel" / "LICENSE-AUDIT-METADATA.txt").unlink()

    with pytest.raises(ValueError, match="Falta metadatos de license-audit-macos-Intel"):
        BUNDLE.create_release_bundle(**kwargs)


def test_release_bundle_cannot_overwrite_an_installer_or_checksum_manifest(tmp_path):
    kwargs = _inputs(tmp_path)
    kwargs["output_path"] = kwargs["dist_dir"] / "PDF-Escolar.exe"
    with pytest.raises(ValueError, match="colisiona con otro artefacto"):
        BUNDLE.create_release_bundle(**kwargs)

    kwargs = _inputs(tmp_path)
    kwargs["output_path"] = kwargs["dist_dir"] / "SHA256SUMS.txt"
    with pytest.raises(ValueError, match="colisiona con otro artefacto"):
        BUNDLE.create_release_bundle(**kwargs)


def test_ci_verifier_checks_real_platform_evidence_before_hashing_the_bundle():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    verifier = workflow.split("  verify-artifacts:", 1)[1].split("  publish-release:", 1)[0]

    assert "name: Download platform-specific license audit evidence" in verifier
    assert "path: dist/license-audit-source" in verifier
    assert "tools/prepare_license_audit_release_bundle.py" in verifier
    assert "name: Verify license evidence bundle against generated packages" in verifier
    expected_extra_asset = '--extra-asset "LICENSE-AUDIT-EVIDENCE-0.1.0-dev.' + '    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")

    assert "name: Download platform-specific license audit evidence" in workflow
    assert "tools/prepare_license_audit_release_bundle.py" in workflow
    assert "dist/LICENSE-AUDIT-EVIDENCE-*.zip" in workflow
    expected_extra_asset = '--extra-asset "LICENSE-AUDIT-EVIDENCE-' + '$' + '{RELEASE_TAG#v}.zip"'
    assert expected_extra_asset in workflow
    assert "license-audit-*" in workflow
 + '{GITHUB_RUN_NUMBER}.zip"'
    assert expected_extra_asset in verifier
    assert verifier.index("Verify license evidence bundle") < verifier.index(
        "Validate package version and checksum manifest"
    )


def test_release_bundle_workflow_uploads_permanent_evidence_and_hashes_it():
    workflow = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")

    assert "name: Download platform-specific license audit evidence" in workflow
    assert "tools/prepare_license_audit_release_bundle.py" in workflow
    assert "dist/LICENSE-AUDIT-EVIDENCE-*.zip" in workflow
    expected_extra_asset = '--extra-asset "LICENSE-AUDIT-EVIDENCE-' + '$' + '{RELEASE_TAG#v}.zip"'
    assert expected_extra_asset in workflow
    assert "license-audit-*" in workflow
