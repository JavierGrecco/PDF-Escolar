"""Validate release package names and create a checksum manifest."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path


VERSION_PATTERN = re.compile(
    r"\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?"
)

PORTABLE_NAME = "PDF-Escolar.exe"
INSTALLER_PATTERNS = {
    "Windows": "PDF-Escolar-Instalador-*-Windows.exe",
    "macOS Intel": "PDF-Escolar-Instalador-*-macOS-Intel.dmg",
    "macOS Apple Silicon": "PDF-Escolar-Instalador-*-macOS-Apple-Silicon.dmg",
}


def expected_asset_names(version: str) -> tuple[str, ...]:
    """Return the four canonical download names for an application release."""
    return (
        PORTABLE_NAME,
        f"PDF-Escolar-Instalador-{version}-Windows.exe",
        f"PDF-Escolar-Instalador-{version}-macOS-Intel.dmg",
        f"PDF-Escolar-Instalador-{version}-macOS-Apple-Silicon.dmg",
    )


def sha256_file(path: Path) -> str:
    """Calculate SHA-256 without loading the entire binary into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_release_manifest(
    *,
    version: str,
    commit: str,
    repository: str,
    run_id: str,
    dist_dir: Path,
) -> Path:
    """Validate version-specific installers and write SHA256SUMS.txt.

    This fails closed if an expected asset is missing, empty, ambiguous, or
    accompanied by a stale installer for another version.
    """
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Versión inválida para una Release: {version!r}")
    if not commit.strip():
        raise ValueError("Falta el commit de origen.")
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
        raise ValueError(f"Nombre de repositorio inválido: {repository!r}")
    if not run_id.isdigit():
        raise ValueError(f"Identificador de ejecución inválido: {run_id!r}")
    if not dist_dir.is_dir():
        raise ValueError(f"No existe la carpeta de artefactos: {dist_dir}")

    expected = expected_asset_names(version)
    expected_set = set(expected)

    for platform, pattern in INSTALLER_PATTERNS.items():
        matches = sorted(path.name for path in dist_dir.glob(pattern))
        correct = f"PDF-Escolar-Instalador-{version}-"
        if len(matches) != 1 or matches[0] not in expected_set:
            raise ValueError(
                f"Se esperaba exactamente un instalador de {platform} para "
                f"{version}; encontrados: {matches or 'ninguno'}."
            )
        if not matches[0].startswith(correct):
            raise ValueError(
                f"El instalador de {platform} no corresponde a la versión {version}: "
                f"{matches[0]}"
            )

    asset_paths = [dist_dir / name for name in expected]
    for path in asset_paths:
        if not path.is_file():
            raise ValueError(f"Falta un artefacto requerido para publicar: {path.name}")
        if path.stat().st_size <= 0:
            raise ValueError(f"El artefacto está vacío: {path.name}")

    lines = [
        f"PDF Escolar v{version}",
        f"Commit de origen: {commit}",
        f"Repositorio: {repository}",
        f"Compilación: https://github.com/{repository}/actions/runs/{run_id}",
        "",
        "SHA-256:",
    ]
    lines.extend(f"{sha256_file(path)}  {path.name}" for path in asset_paths)

    manifest = dist_dir / "SHA256SUMS.txt"
    temporary = dist_dir / ".SHA256SUMS.txt.tmp"
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Version sin prefijo v.")
    parser.add_argument("--commit", required=True, help="SHA del commit compilado.")
    parser.add_argument("--repository", required=True, help="Repositorio owner/name.")
    parser.add_argument("--run-id", required=True, help="ID de GitHub Actions.")
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()

    try:
        manifest = write_release_manifest(
            version=args.version,
            commit=args.commit,
            repository=args.repository,
            run_id=args.run_id,
            dist_dir=args.dist_dir,
        )
    except (OSError, ValueError) as exc:
        print(f"No se puede validar la publicación: {exc}", file=sys.stderr)
        return 1

    print(f"Artefactos validados; manifiesto de checksums: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
