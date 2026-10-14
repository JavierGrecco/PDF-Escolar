"""Validate platform audit evidence and create a permanent release evidence ZIP."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

VERSION_PATTERN = re.compile(
    r"\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?"
)
COMMIT_PATTERN = re.compile(r"[0-9a-fA-F]{40}")
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
PACKAGE_RECORD_PATTERN = re.compile(
    r"(?m)^  Archivo: ([^\r\n]+)\n"
    r"    Tamaño: ([0-9]+) bytes\n"
    r"    SHA-256: ([0-9a-f]{64})$"
)
NOTICE_RECORD_PATTERN = re.compile(
    r"(?m)^  Archivo: ([^\r\n]+)\n"
    r"  Tamaño: ([0-9]+) bytes\n"
    r"  SHA-256: ([0-9a-f]{64})$"
)

PLATFORMS = (
    ("license-audit-windows", "Windows", "x64", "Windows"),
    ("license-audit-macos-Intel", "macOS", "Intel", "macOS-Intel"),
    ("license-audit-macos-Apple-Silicon", "macOS", "Apple-Silicon", "macOS-Apple-Silicon"),
)
NOTICE_NAME = "THIRD-PARTY-NOTICES.txt"
METADATA_NAME = "LICENSE-AUDIT-METADATA.txt"
CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    """Calculate SHA-256 incrementally."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_file(path: Path, description: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ValueError(f"Falta {description}: {path}")
    if resolved.stat().st_size <= 0:
        raise ValueError(f"El archivo de {description} está vacío: {path.name}")
    return resolved


def _expected_package_names(version: str, platform_name: str, architecture: str) -> set[str]:
    if platform_name == "Windows":
        return {
            "PDF-Escolar.exe",
            f"PDF-Escolar-Instalador-{version}-Windows.exe",
        }
    return {
        f"PDF-Escolar-Instalador-{version}-macOS-{architecture}.dmg",
        f"PDF-Escolar-macOS-{version}-{architecture}.zip",
    }


def _fields_from_metadata(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if line and not line.startswith((" ", "\t")):
            key, separator, value = line.partition(": ")
            if separator:
                fields[key] = value
    return fields


def _parse_notice_record(text: str) -> tuple[str, int, str]:
    section_start = text.find("Avisos de terceros incluidos en la distribución:\n")
    section_end = text.find("Paquetes generados por esta compilación:\n")
    if section_start < 0 or section_end < section_start:
        raise ValueError("Los metadatos no contienen las secciones de avisos y paquetes.")
    section = text[section_start:section_end]
    match = NOTICE_RECORD_PATTERN.search(section)
    if match is None:
        raise ValueError("Los metadatos no contienen un registro válido de avisos.")
    return match.group(1), int(match.group(2)), match.group(3)


def _parse_package_records(text: str) -> list[tuple[str, int, str]]:
    marker = "Paquetes generados por esta compilación:\n"
    if marker not in text:
        raise ValueError("Falta la sección de paquetes en los metadatos.")
    records = [
        (match.group(1), int(match.group(2)), match.group(3))
        for match in PACKAGE_RECORD_PATTERN.finditer(text.split(marker, 1)[1])
    ]
    if not records:
        raise ValueError("No hay registros de paquetes válidos en los metadatos.")
    return records


def _validate_platform_evidence(
    *,
    version: str,
    commit: str,
    repository: str,
    run_id: str,
    dist_dir: Path,
    evidence_dir: Path,
    artifact_name: str,
    platform_name: str,
    architecture: str,
) -> list[tuple[str, Path]]:
    artifact_dir = evidence_dir / artifact_name
    notice_path = _required_file(artifact_dir / NOTICE_NAME, f"avisos de {artifact_name}")
    metadata_path = _required_file(artifact_dir / METADATA_NAME, f"metadatos de {artifact_name}")
    try:
        metadata_text = metadata_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Los metadatos de {artifact_name} no son UTF-8 válido.") from exc

    fields = _fields_from_metadata(metadata_text)
    expected_fields = {
        "Versión": version,
        "Plataforma": platform_name,
        "Arquitectura": architecture,
        "Commit de origen": commit.lower(),
        "Repositorio": repository,
        "Compilación": f"https://github.com/{repository}/actions/runs/{run_id}",
    }
    for key, expected_value in expected_fields.items():
        if fields.get(key) != expected_value:
            raise ValueError(
                f"{artifact_name}: el campo {key!r} no coincide; "
                f"esperado {expected_value!r}, recibido {fields.get(key)!r}."
            )

    notice_name, notice_size, notice_hash = _parse_notice_record(metadata_text)
    if notice_name != NOTICE_NAME:
        raise ValueError(f"{artifact_name}: nombre inesperado del archivo de avisos.")
    if notice_path.stat().st_size != notice_size or sha256_file(notice_path) != notice_hash:
        raise ValueError(f"{artifact_name}: los avisos no coinciden con sus metadatos SHA-256.")

    package_records = _parse_package_records(metadata_text)
    package_names = [name for name, _size, _digest in package_records]
    expected_names = _expected_package_names(version, platform_name, architecture)
    if len(package_names) != len(set(package_names)) or set(package_names) != expected_names:
        raise ValueError(
            f"{artifact_name}: los paquetes enumerados no coinciden con los esperados. "
            f"Esperados: {sorted(expected_names)}; recibidos: {sorted(package_names)}."
        )

    for name, size, digest in package_records:
        if Path(name).name != name or "/" in name or "\\" in name:
            raise ValueError(f"{artifact_name}: nombre de paquete no permitido: {name!r}")
        package_path = _required_file(dist_dir / name, f"paquete {name}")
        if package_path.stat().st_size != size:
            raise ValueError(
                f"{name}: tamaño distinto del inventario de auditoría "
                f"({package_path.stat().st_size} frente a {size} bytes)."
            )
        actual_hash = sha256_file(package_path)
        if actual_hash != digest:
            raise ValueError(f"{name}: el SHA-256 difiere del inventario de auditoría.")
    archive_prefix = _archive_folder(platform_name, architecture)
    return [
        (f"{archive_prefix}/{NOTICE_NAME}", notice_path),
        (f"{archive_prefix}/{METADATA_NAME}", metadata_path),
    ]


def _archive_folder(platform_name: str, architecture: str) -> str:
    if platform_name == "Windows":
        return "Windows-x64"
    if architecture == "Intel":
        return "macOS-Intel"
    return "macOS-Apple-Silicon"


def create_release_bundle(
    *,
    version: str,
    commit: str,
    repository: str,
    run_id: str,
    dist_dir: Path,
    evidence_dir: Path,
    output_path: Path | None = None,
) -> Path:
    """Validate every platform's evidence against release packages and ZIP it."""
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"Versión inválida para la evidencia de Release: {version!r}")
    if not COMMIT_PATTERN.fullmatch(commit):
        raise ValueError("El commit debe ser un SHA completo de 40 caracteres hexadecimales.")
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError(f"Nombre de repositorio inválido: {repository!r}")
    if not run_id.isdigit():
        raise ValueError("Identificador de ejecución inválido.")
    dist = dist_dir.expanduser().resolve()
    evidence = evidence_dir.expanduser().resolve()
    if not dist.is_dir():
        raise ValueError(f"No existe la carpeta de paquetes: {dist}")
    if not evidence.is_dir():
        raise ValueError(f"No existe la carpeta de evidencias de auditoría: {evidence}")

    archive_files: list[tuple[str, Path]] = []
    for artifact_name, platform_name, architecture, _folder in PLATFORMS:
        archive_files.extend(
            _validate_platform_evidence(
                version=version,
                commit=commit,
                repository=repository,
                run_id=run_id,
                dist_dir=dist,
                evidence_dir=evidence,
                artifact_name=artifact_name,
                platform_name=platform_name,
                architecture=architecture,
            )
        )

    output = (
        output_path.expanduser().resolve()
        if output_path is not None
        else dist / f"LICENSE-AUDIT-EVIDENCE-{version}.zip"
    )
    protected_paths = {(dist / "SHA256SUMS.txt").resolve()}
    protected_paths.update(
        (dist / name).resolve()
        for _artifact_name, platform_name, architecture, _folder in PLATFORMS
        for name in _expected_package_names(version, platform_name, architecture)
    )
    protected_paths.update(path.resolve() for _name, path in archive_files)
    if output in protected_paths:
        raise ValueError("La ruta de salida colisiona con otro artefacto.")
    if not output.parent.is_dir():
        raise ValueError(f"No existe la carpeta de salida: {output.parent}")

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".license-audit-evidence.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
        with zipfile.ZipFile(
            temporary_name,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for archive_name, source_path in sorted(archive_files):
                info = zipfile.ZipInfo(archive_name, date_time=(2020, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, source_path.read_bytes(), compresslevel=9)

        with zipfile.ZipFile(temporary_name, mode="r") as archive:
            if archive.testzip() is not None:
                raise ValueError("El ZIP de evidencia no superó la verificación de integridad.")
            expected_archive_names = {name for name, _path in archive_files}
            if set(archive.namelist()) != expected_archive_names:
                raise ValueError("El ZIP de evidencia no contiene exactamente los seis archivos esperados.")
        os.replace(temporary_name, output)
    except (OSError, zipfile.BadZipFile):
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
        raise
    except ValueError:
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
    parser.add_argument("--commit", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        output = create_release_bundle(
            version=args.version,
            commit=args.commit,
            repository=args.repository,
            run_id=args.run_id,
            dist_dir=args.dist_dir,
            evidence_dir=args.evidence_dir,
            output_path=args.output,
        )
    except (OSError, ValueError) as exc:
        print(f"No se puede preparar la evidencia de licencias para Release: {exc}", file=sys.stderr)
        return 1
    print(f"Evidencia de licencias validada y empaquetada: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
