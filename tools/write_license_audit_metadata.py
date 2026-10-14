"""Create verifiable, build-specific evidence for third-party license review.

The metadata records the exact notices file and distributable packages generated
by one platform job. It supports a manual licensing audit; it is not legal advice
or a declaration that redistribution requirements have been satisfied.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Iterable

VERSION_PATTERN = re.compile(
    r"\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?"
)
COMMIT_PATTERN = re.compile(r"[0-9a-fA-F]{40}")
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SUPPORTED_PLATFORMS = {
    ("Windows", "x64"),
    ("macOS", "Intel"),
    ("macOS", "Apple-Silicon"),
}
CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    """Hash a file incrementally without loading a large installer into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _existing_nonempty_file(path: Path, description: str) -> tuple[Path, int]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f"No existe el archivo de {description}: {path}")
    size = resolved.stat().st_size
    if size <= 0:
        raise ValueError(f"El archivo de {description} está vacío: {path.name}")
    return resolved, size


def render_metadata(
    *,
    version: str,
    platform_name: str,
    architecture: str,
    commit: str,
    repository: str,
    run_id: str,
    notice_file: Path,
    output_path: Path,
    package_paths: Iterable[Path],
) -> str:
    """Validate inputs and render deterministic metadata for one build job."""
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Versión inválida: {version!r}")
    if (platform_name, architecture) not in SUPPORTED_PLATFORMS:
        raise ValueError(
            f"Combinación de plataforma y arquitectura no admitida: "
            f"{platform_name!r} / {architecture!r}"
        )
    if not COMMIT_PATTERN.fullmatch(commit):
        raise ValueError("El commit debe ser un SHA completo de 40 caracteres hexadecimales.")
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError("El repositorio debe tener el formato propietario/repositorio.")
    if not run_id.isdigit():
        raise ValueError("El identificador de la ejecución debe ser numérico.")

    notice, notice_size = _existing_nonempty_file(notice_file, "avisos de terceros")
    output = output_path.expanduser().resolve()
    if not output.parent.is_dir():
        raise ValueError(f"No existe la carpeta de destino: {output.parent}")
    if output == notice:
        raise ValueError("El archivo de salida no puede reemplazar el inventario de avisos.")

    packages = list(package_paths)
    if not packages:
        raise ValueError("Debe indicarse al menos un paquete para registrar.")
    package_records: list[tuple[Path, int, str]] = []
    package_names: set[str] = set()
    seen_paths: set[Path] = set()

    for package_path in packages:
        package, size = _existing_nonempty_file(package_path, "paquete distribuible")
        if package == output or package == notice:
            raise ValueError(
                "El archivo de salida y los avisos no pueden registrarse como paquete."
            )
        if package in seen_paths:
            raise ValueError(f"El mismo paquete se indicó más de una vez: {package.name}")
        if package.name.casefold() in package_names:
            raise ValueError(
                f"Dos paquetes tienen el mismo nombre y no serían distinguibles: {package.name}"
            )
        seen_paths.add(package)
        package_names.add(package.name.casefold())
        package_records.append((package, size, sha256_file(package)))

    lines = [
        "PDF Escolar — Evidencia técnica para revisión de licencias",
        f"Versión: {version}",
        f"Plataforma: {platform_name}",
        f"Arquitectura: {architecture}",
        f"Commit de origen: {commit.lower()}",
        f"Repositorio: {repository}",
        f"Compilación: https://github.com/{repository}/actions/runs/{run_id}",
        "",
        "Avisos de terceros incluidos en la distribución:",
        f"  Archivo: {notice.name}",
        f"  Tamaño: {notice_size} bytes",
        f"  SHA-256: {sha256_file(notice)}",
        "",
        "Paquetes generados por esta compilación:",
    ]
    for package, size, digest in package_records:
        lines.extend(
            [
                f"  Archivo: {package.name}",
                f"    Tamaño: {size} bytes",
                f"    SHA-256: {digest}",
            ]
        )
    lines.extend(
        [
            "",
            "Alcance: identifica los archivos exactos producidos por esta compilación.",
            "Esta evidencia facilita una revisión manual; no certifica cumplimiento legal.",
            "",
        ]
    )
    return "\n".join(lines)


def write_metadata(**kwargs) -> Path:
    """Write metadata atomically so interrupted writes do not leave a partial file."""
    output = Path(kwargs["output_path"]).expanduser().resolve()
    content = render_metadata(**kwargs)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(content)
        os.replace(temporary_name, output)
    except OSError:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
        raise
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--platform", dest="platform_name", required=True)
    parser.add_argument("--architecture", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--notice-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--package",
        dest="package_paths",
        type=Path,
        action="append",
        required=True,
        help="Paquete producido; repetir para registrar varios archivos.",
    )
    args = parser.parse_args()

    try:
        output = write_metadata(
            version=args.version,
            platform_name=args.platform_name,
            architecture=args.architecture,
            commit=args.commit,
            repository=args.repository,
            run_id=args.run_id,
            notice_file=args.notice_file,
            output_path=args.output,
            package_paths=args.package_paths,
        )
    except (OSError, ValueError) as exc:
        print(f"No se pudo generar la evidencia de auditoría: {exc}", file=sys.stderr)
        return 1

    print(f"Evidencia de auditoría generada: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
