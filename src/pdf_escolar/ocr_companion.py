"""Download, verify, install, and run the optional local OCR companion."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Callable

REPOSITORY = "JavierGrecco/PDF-Escolar"
RELEASES_API = f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100"
MAX_ARCHIVE_BYTES = 850 * 1024 * 1024
MAX_UNPACKED_BYTES = 2 * 1024 * 1024 * 1024
MAX_ARCHIVE_FILES = 50_000
CHUNK_SIZE = 1024 * 1024
RELEASE_TAG_PATTERN = re.compile(r"^ocr-engine-v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


class OCRCompanionError(RuntimeError):
    """An actionable OCR companion installation or runtime error."""


ProgressCallback = Callable[[int, int, str], None]


def platform_support_error() -> str | None:
    """Return a Spanish explanation when no companion is built for this system."""
    machine = platform.machine().lower()
    if sys.platform == "win32":
        if machine not in {"amd64", "x86_64"}:
            return "El complemento OCR está disponible para Windows de 64 bits."
        return None

    if sys.platform == "darwin":
        if machine in {"x86_64", "amd64"}:
            return (
                "El complemento OCR está optimizado para Mac con chip Apple Silicon (M1 o posterior). "
                "En Mac Intel podés seguir usando las demás herramientas de PDF Escolar."
            )
        if machine not in {"arm64", "aarch64"}:
            return "El complemento OCR no está disponible para esta arquitectura de Mac."
        version_parts = platform.mac_ver()[0].split(".")
        try:
            version = tuple(int(part) for part in version_parts[:2])
        except ValueError:
            version = ()
        if not version or version < (14, 0):
            return (
                "El complemento OCR necesita macOS 14 o posterior en equipos Apple Silicon. "
                "PDF Escolar puede seguir usando sus demás herramientas en este equipo."
            )
        return None

    return "El complemento OCR está disponible para Windows de 64 bits y Mac compatibles."


def expected_asset_name() -> str:
    """Return the exact release asset for the current platform."""
    problem = platform_support_error()
    if problem:
        raise OCRCompanionError(problem)

    if sys.platform == "win32":
        return "PDF-Escolar-OCR-Windows-x64.zip"
    return "PDF-Escolar-OCR-macOS-Apple-Silicon.zip"


def _data_root() -> Path:
    """Choose a per-user install location, never a system-wide location."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        return Path(base) / "PDF Escolar" / "OCR" if base else (
            Path.home() / "AppData" / "Local" / "PDF Escolar" / "OCR"
        )
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PDF Escolar" / "OCR"
    base = os.environ.get("XDG_DATA_HOME")
    return (
        Path(base) / "pdf-escolar" / "ocr"
        if base
        else Path.home() / ".local" / "share" / "pdf-escolar" / "ocr"
    )


def _validate_tag(tag: str) -> bool:
    return bool(RELEASE_TAG_PATTERN.fullmatch(tag))


def _helper_in_package(package_dir: Path) -> Path:
    executable = (
        package_dir / "PDF-Escolar-OCR.exe"
        if sys.platform == "win32"
        else package_dir / "PDF-Escolar-OCR"
    )
    if not executable.is_file():
        raise OCRCompanionError(
            "No encontramos el ejecutable del complemento OCR. Intentá instalarlo nuevamente."
        )
    return executable


def get_installed_ocr_companion() -> tuple[Path | None, str | None]:
    """Return the active helper and release tag when an installation exists."""
    problem = platform_support_error()
    if problem:
        return None, None

    root = _data_root()
    try:
        tag = (root / "current.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return None, None
    if not _validate_tag(tag):
        return None, None
    package_dir = root / tag / "PDF-Escolar-OCR"
    try:
        executable = _helper_in_package(package_dir)
    except OCRCompanionError:
        return None, None
    return executable, tag


def _request(url: str, *, accept: str, timeout: int = 60):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "PDF-Escolar OCR companion installer",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    return urllib.request.urlopen(request, timeout=timeout)


def _latest_release(asset_name: str) -> tuple[str, dict]:
    try:
        with _request(RELEASES_API, accept="application/vnd.github+json", timeout=25) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise OCRCompanionError("La respuesta de GitHub es demasiado grande.")
        releases = json.loads(raw.decode("utf-8"))
    except OCRCompanionError:
        raise
    except (OSError, urllib.error.URLError, UnicodeError, json.JSONDecodeError) as exc:
        raise OCRCompanionError(
            "No pudimos consultar las versiones del complemento OCR. "
            "Comprobá tu conexión e intentá nuevamente."
        ) from exc

    candidates = [
        release
        for release in releases
        if isinstance(release, dict)
        and not release.get("draft", False)
        and _validate_tag(str(release.get("tag_name", "")))
    ]
    candidates.sort(key=lambda item: str(item.get("published_at") or ""), reverse=True)
    for release in candidates:
        asset = next(
            (
                item
                for item in release.get("assets", [])
                if isinstance(item, dict) and item.get("name") == asset_name
            ),
            None,
        )
        if asset is None:
            continue
        digest = str(asset.get("digest") or "")
        size = asset.get("size")
        url = str(asset.get("browser_download_url") or "")
        parsed_url = urllib.parse.urlparse(url)
        if (
            not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", digest)
            or not isinstance(size, int)
            or size <= 0
            or size > MAX_ARCHIVE_BYTES
            or parsed_url.scheme != "https"
            or parsed_url.netloc != "github.com"
            or not parsed_url.path.startswith(f"/{REPOSITORY}/releases/download/")
        ):
            raise OCRCompanionError(
                "La publicación del complemento OCR no tiene datos de integridad válidos."
            )
        return str(release["tag_name"]), asset
    raise OCRCompanionError(
        "Todavía no hay una versión compatible del complemento OCR publicada para este equipo."
    )


def _download_asset(asset: dict, destination: Path, progress: ProgressCallback | None) -> None:
    expected_digest = str(asset["digest"]).split(":", 1)[1].lower()
    expected_size = int(asset["size"])
    digest = hashlib.sha256()
    bytes_written = 0

    try:
        with _request(
            str(asset["browser_download_url"]),
            accept="application/octet-stream",
            timeout=90,
        ) as response, destination.open("wb") as output:
            while True:
                block = response.read(CHUNK_SIZE)
                if not block:
                    break
                bytes_written += len(block)
                if bytes_written > expected_size or bytes_written > MAX_ARCHIVE_BYTES:
                    raise OCRCompanionError(
                        "La descarga superó el tamaño esperado y se canceló por seguridad."
                    )
                digest.update(block)
                output.write(block)
                if progress:
                    progress(
                        bytes_written,
                        expected_size,
                        "Descargando complemento OCR…",
                    )
    except OCRCompanionError:
        raise
    except (OSError, urllib.error.URLError) as exc:
        raise OCRCompanionError(
            "No pudimos descargar el complemento OCR. Comprobá tu conexión e intentá nuevamente."
        ) from exc

    if bytes_written != expected_size or digest.hexdigest() != expected_digest:
        destination.unlink(missing_ok=True)
        raise OCRCompanionError(
            "La verificación de la descarga no coincide. No instalamos el archivo."
        )


def _safe_extract(archive_path: Path, destination: Path) -> None:
    """Extract a ZIP without path traversal, symlinks, or unreasonable expansion."""
    root = destination.resolve()
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_FILES:
                raise OCRCompanionError("El paquete OCR contiene demasiados archivos.")
            unpacked_size = sum(info.file_size for info in infos)
            if unpacked_size > MAX_UNPACKED_BYTES:
                raise OCRCompanionError("El paquete OCR es demasiado grande para instalarlo.")
            for info in infos:
                name = info.filename.replace("\\", "/")
                relative = PurePosixPath(name)
                mode = info.external_attr >> 16
                if (
                    not name
                    or relative.is_absolute()
                    or ".." in relative.parts
                    or (relative.parts and ":" in relative.parts[0])
                    or stat.S_ISLNK(mode)
                ):
                    raise OCRCompanionError(
                        "El paquete OCR contiene una ruta no segura. No lo instalamos."
                    )
                target = root.joinpath(*relative.parts).resolve()
                if target != root and root not in target.parents:
                    raise OCRCompanionError(
                        "El paquete OCR contiene una ruta no segura. No lo instalamos."
                    )
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=CHUNK_SIZE)
                if mode & 0o777:
                    target.chmod(mode & 0o777)
    except OCRCompanionError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, zipfile.LargeZipFile) as exc:
        raise OCRCompanionError("El paquete OCR está dañado o no se pudo extraer.") from exc


def install_ocr_companion(
    progress: ProgressCallback | None = None,
) -> tuple[Path, str]:
    """Download the latest matching release, verify its digest, and install per user."""
    asset_name = expected_asset_name()
    tag, asset = _latest_release(asset_name)
    existing_helper, existing_tag = get_installed_ocr_companion()
    if existing_helper is not None and existing_tag == tag:
        try:
            check = subprocess.run(
                [str(existing_helper), "--check"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            check = None
        if check is not None and check.returncode == 0:
            if progress:
                progress(1, 1, "El complemento OCR ya está actualizado.")
            return existing_helper, tag

    root = _data_root()
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".ocr-stage-", dir=str(root)))
    archive_path = staging / "companion.zip"
    extracted = staging / "extracted"
    extracted.mkdir()
    final_dir = root / tag
    backup_dir = root / f".{tag}.previous"
    try:
        _download_asset(asset, archive_path, progress)
        if progress:
            progress(0, 1, "Verificando el paquete OCR…")
        _safe_extract(archive_path, extracted)
        package_dir = extracted / "PDF-Escolar-OCR"
        helper = _helper_in_package(package_dir)
        if sys.platform != "win32":
            helper.chmod(helper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            tesseract = package_dir / "tesseract" / "bin" / "tesseract"
            if tesseract.is_file():
                tesseract.chmod(
                    tesseract.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                )

        try:
            check = subprocess.run(
                [str(helper), "--check"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise OCRCompanionError(
                "Se descargó el complemento OCR, pero no pudimos iniciarlo en este equipo."
            ) from exc
        if check.returncode != 0:
            raise OCRCompanionError(
                "El complemento OCR no superó la comprobación de instalación. "
                "No quedó activado en esta computadora."
            )

        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)
        if final_dir.exists():
            final_dir.rename(backup_dir)
        try:
            extracted.rename(final_dir)
        except Exception:
            if backup_dir.exists() and not final_dir.exists():
                backup_dir.rename(final_dir)
            raise

        current_temp = root / ".current.tmp"
        current_temp.write_text(tag + "\n", encoding="utf-8")
        os.replace(current_temp, root / "current.txt")
        shutil.rmtree(backup_dir, ignore_errors=True)
        for old_dir in root.glob("ocr-engine-v*"):
            if old_dir != final_dir and old_dir.is_dir():
                shutil.rmtree(old_dir, ignore_errors=True)
        installed_helper = _helper_in_package(final_dir / "PDF-Escolar-OCR")
        if progress:
            progress(1, 1, "Complemento OCR instalado y verificado.")
        return installed_helper, tag
    except OCRCompanionError:
        raise
    except OSError as exc:
        raise OCRCompanionError(
            "No pudimos instalar el complemento OCR en la carpeta de datos de tu usuario."
        ) from exc
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def run_ocr_with_companion(
    input_path: str,
    output_path: str,
    *,
    languages: list[str],
    pages: str | None = None,
    executable: Path | None = None,
) -> int:
    """Run the separate OCR process and return the output page count."""
    helper = executable
    if helper is None:
        helper, _tag = get_installed_ocr_companion()
    if helper is None or not helper.is_file():
        raise OCRCompanionError("Primero instalá el complemento OCR de PDF Escolar.")

    if not languages or any(language not in {"spa", "eng"} for language in languages):
        raise OCRCompanionError("Elegí español, inglés o ambos idiomas.")
    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.is_file():
        raise OCRCompanionError("No encontramos el PDF de origen.")
    if source == target:
        raise OCRCompanionError("Elegí un archivo de salida distinto del PDF original.")
    if target.suffix.lower() != ".pdf":
        raise OCRCompanionError("El archivo de salida debe tener extensión .pdf.")
    if not target.parent.is_dir():
        raise OCRCompanionError("La carpeta de destino no existe.")

    with tempfile.TemporaryDirectory(
        prefix=".pdf-escolar-ocr-publish-",
        dir=str(target.parent),
    ) as working_directory:
        temporary_output = Path(working_directory) / "resultado.pdf"
        arguments = [
            str(helper),
            "--input",
            str(source),
            "--output",
            str(temporary_output),
            "--language",
            "+".join(languages),
        ]
        if pages and pages.strip():
            arguments.extend(["--pages", pages.strip()])
        try:
            result = subprocess.run(
                arguments,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except OSError as exc:
            raise OCRCompanionError(
                "No pudimos iniciar el complemento OCR. Intentá instalarlo nuevamente."
            ) from exc

        if result.returncode != 0:
            raise OCRCompanionError(
                "No pudimos crear el PDF buscable. Comprobá que el documento no esté protegido "
                "y que las páginas seleccionadas sean legibles."
            )
        if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
            raise OCRCompanionError("El complemento no generó un PDF válido.")

        try:
            import pikepdf

            with pikepdf.open(temporary_output) as pdf:
                count = len(pdf.pages)
        except Exception as exc:
            raise OCRCompanionError(
                "El resultado del OCR no es un PDF válido. El archivo de destino quedó sin cambios."
            ) from exc
        if count == 0:
            raise OCRCompanionError(
                "El resultado del OCR no contiene páginas. El archivo de destino quedó sin cambios."
            )
        os.replace(temporary_output, target)
        return count
