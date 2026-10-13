"""Tests for the read-only Git history size audit."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "analyze_git_history_size.py"
SPEC = importlib.util.spec_from_file_location("analyze_git_history_size", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo with spaces"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "PDF Escolar tests")
    _git(repo, "config", "user.email", "tests@example.invalid")
    (repo / "descargas").mkdir()
    (repo / "assets").mkdir()
    old_blob = b"A" * 1_100_000
    (repo / "assets" / "archive.bin").write_bytes(old_blob)
    (repo / "descargas" / "sample.exe").write_bytes(old_blob)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "Add first large blob")

    # Reusing the same content at another path must not count as another blob.
    (repo / "docs").mkdir()
    (repo / "docs" / "same content.bin").write_bytes(old_blob)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "Reuse existing blob")

    # A different version remains reachable from history after the path changes.
    (repo / "assets" / "archive.bin").write_bytes(b"B" * 1_200_000)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "Replace large blob")
    _git(repo, "tag", "audit-test-tag")
    return repo


def test_counts_unique_reachable_blobs_not_repeated_paths(repository: Path):
    report = AUDIT.build_report(repository, min_size_bytes=1_000_000)
    large_blobs = report["large_blobs"]

    assert report["shallow_clone"] is False
    assert report["head"] == _git(repository, "rev-parse", "HEAD")
    assert report["large_blob_count"] == 2
    assert {item["size_bytes"] for item in large_blobs} == {1_100_000, 1_200_000}
    assert report["unique_reachable_blob_bytes"] >= 2_300_000
    assert "refs/heads/" in " ".join(report["refs"])
    assert "refs/tags/audit-test-tag" in report["refs"]


def test_current_descargas_size_is_reported_separately(repository: Path):
    report = AUDIT.build_report(repository, min_size_bytes=1_000_000)

    assert len(report["current_descargas_files"]) == 1
    download = report["current_descargas_files"][0]
    assert download["path"] == "descargas/sample.exe"
    assert download["size_bytes"] == 1_100_000
    assert len(download["sha"]) == 40
    assert report["current_descargas_total_bytes"] == 1_100_000


def test_supports_bare_mirror_repositories(repository: Path, tmp_path: Path):
    mirror = tmp_path / "audit mirror.git"
    subprocess.run(
        ["git", "clone", "--mirror", str(repository), str(mirror)],
        check=True,
        capture_output=True,
        text=True,
    )

    report = AUDIT.build_report(mirror, min_size_bytes=1_000_000)

    assert report["head"] is not None
    assert report["shallow_clone"] is False
    assert report["large_blob_count"] == 2
    assert report["current_descargas_total_bytes"] == 1_100_000


def test_cli_writes_json_and_prints_human_readable_report(repository: Path, tmp_path: Path):
    output = tmp_path / "history-report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo",
            str(repository),
            "--min-size-mib",
            "1",
            "--top",
            "5",
            "--json",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Archivos que hoy están en descargas/" in result.stdout
    assert "Blobs más grandes" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["large_blob_count"] == 2
    assert len(payload["large_blobs"]) == 2


def test_rejects_zero_threshold(repository: Path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repository), "--min-size-mib", "0"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "--min-size-mib" in result.stderr


def test_non_repository_returns_clear_error(tmp_path: Path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "No se pudo leer el repositorio Git" in result.stderr
