"""Unit tests for the repository's large-file and downloads policy."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "check_repository_policy.py"
SPEC = spec_from_file_location("check_repository_policy", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
POLICY = module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)


def test_unrelated_small_files_are_allowed():
    violations = POLICY.policy_violations(
        ["README.md", "src/pdf_escolar/app.py"],
        {"README.md": 4_000, "src/pdf_escolar/app.py": 9_000},
    )

    assert violations == []


def test_all_download_directory_changes_require_release_workflow():
    violations = POLICY.policy_violations(
        [
            "descargas/INFORMACION-DE-DESCARGA.txt",
            "descargas/PDF-Escolar.exe",
        ],
        {
            "descargas/INFORMACION-DE-DESCARGA.txt": 650,
            "descargas/PDF-Escolar.exe": 70_000_000,
        },
    )

    assert len(violations) == 2
    assert all("Build installers" in violation for violation in violations)


def test_new_or_modified_files_over_twenty_mib_are_rejected():
    path = "assets/sample-data.bin"
    violations = POLICY.policy_violations(
        [path],
        {path: 20 * 1024 * 1024 + 1},
    )

    assert len(violations) == 1
    assert "20.0 MiB" in violations[0]
    assert "20 MiB" in violations[0]


def test_a_file_at_the_size_limit_is_allowed():
    path = "docs/reference.txt"
    violations = POLICY.policy_violations(
        [path],
        {path: 20 * 1024 * 1024},
    )

    assert violations == []


def test_deleting_an_existing_large_file_does_not_increase_repository_size():
    path = "assets/obsolete-packaging.zip"
    violations = POLICY.policy_violations([path], {path: None})

    assert violations == []


def test_duplicate_paths_are_checked_only_once():
    path = "descargas/PDF-Escolar.exe"
    violations = POLICY.policy_violations(
        [path, path],
        {path: 70_000_000},
    )

    assert len(violations) == 1
