#!/usr/bin/env python3
"""Standalone OCR process for PDF Escolar.

This file is packaged with its own Python dependencies and Tesseract runtime.
It intentionally does not use the main application's pikepdf environment.
"""

from __future__ import annotations

import argparse
import logging
import multiprocessing
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import ocrmypdf
import pypdfium2 as pdfium
from ocrmypdf import ExitCode, Verbosity

COMPANION_VERSION = "1.0.0"
SUPPORTED_LANGUAGES = {"spa", "eng"}


class CompanionError(Exception):
    """A user-correctable companion configuration or processing error."""


def _package_dir() -> Path:
    """Return the folder next to the executable, or the source file for development."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _find_tesseract(package_dir: Path) -> tuple[Path, Path]:
    """Find the bundled Tesseract executable and language-data directory."""
    root = package_dir / "tesseract"
    if sys.platform == "win32":
        executable_names = ("tesseract.exe",)
    else:
        executable_names = ("tesseract",)

    executable_candidates = [
        root / name for name in executable_names
    ] + [
        root / "bin" / name for name in executable_names
    ]
    executable = next(
        (candidate for candidate in executable_candidates if candidate.is_file()),
        None,
    )
    if executable is None:
        raise CompanionError(
            "Falta el motor de reconocimiento. Reinstalá el complemento OCR de PDF Escolar."
        )

    data_candidates = [
        root / "tessdata",
        root / "share" / "tessdata",
    ]
    data_dir = next(
        (
            candidate
            for candidate in data_candidates
            if (candidate / "spa.traineddata").is_file()
        ),
        None,
    )
    if data_dir is None:
        raise CompanionError(
            "Faltan los datos de idioma del OCR. Reinstalá el complemento OCR de PDF Escolar."
        )

    required_models = ("spa.traineddata", "eng.traineddata", "osd.traineddata")
    missing = [name for name in required_models if not (data_dir / name).is_file()]
    if missing:
        raise CompanionError(
            "El complemento OCR está incompleto. Reinstalalo para recuperar los datos de idioma."
        )
    return executable, data_dir


def _tesseract_environment(package_dir: Path) -> tuple[dict[str, str], Path]:
    """Set paths so OCRmyPDF uses only the bundled Tesseract installation."""
    executable, data_dir = _find_tesseract(package_dir)
    env = os.environ.copy()
    executable_dir = str(executable.parent)
    env["PATH"] = executable_dir + os.pathsep + env.get("PATH", "")
    env["TESSDATA_PREFIX"] = str(data_dir)
    env["OMP_THREAD_LIMIT"] = "1"

    if sys.platform == "darwin":
        library_dir = executable.parent.parent / "lib"
        existing = env.get("DYLD_LIBRARY_PATH", "")
        env["DYLD_LIBRARY_PATH"] = (
            str(library_dir) + (os.pathsep + existing if existing else "")
        )
        fallback = env.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        env["DYLD_FALLBACK_LIBRARY_PATH"] = (
            str(library_dir) + (os.pathsep + fallback if fallback else "")
        )
    return env, executable


def check_installation(package_dir: Path | None = None) -> str:
    """Verify the packaged OCR engine is complete and starts successfully."""
    root = package_dir or _package_dir()
    env, executable = _tesseract_environment(root)
    try:
        version = subprocess.run(
            [str(executable), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
        languages = subprocess.run(
            [str(executable), "--list-langs"],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CompanionError(
            "No pudimos iniciar el motor OCR. Reinstalá el complemento de PDF Escolar."
        ) from exc

    listed_languages = {
        line.strip()
        for line in languages.stdout.splitlines()
        if line.strip() and not line.lower().startswith("list of")
    }
    if not SUPPORTED_LANGUAGES.issubset(listed_languages):
        raise CompanionError(
            "El complemento OCR no contiene los idiomas necesarios. Reinstalalo."
        )
    first_line = version.stdout.splitlines()[0] if version.stdout else "Tesseract"
    return f"PDF Escolar OCR {COMPANION_VERSION}; {first_line}"


def _validate_paths(input_path: str, output_path: str) -> tuple[Path, Path]:
    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.is_file():
        raise CompanionError("No encontramos el PDF de origen.")
    if source == target:
        raise CompanionError(
            "Elegí un archivo de salida distinto. El PDF original no se modifica."
        )
    if target.suffix.lower() != ".pdf":
        raise CompanionError("El archivo de salida debe tener extensión .pdf.")
    if not target.parent.is_dir():
        raise CompanionError("La carpeta de destino no existe.")
    return source, target


def run_ocr(
    input_path: str,
    output_path: str,
    *,
    languages: list[str],
    pages: str | None = None,
    package_dir: Path | None = None,
) -> int:
    """Recognize text locally and atomically publish a validated searchable PDF."""
    unsupported = sorted(set(languages) - SUPPORTED_LANGUAGES)
    if not languages or unsupported:
        raise CompanionError("Elegí español, inglés o ambos idiomas para reconocer el texto.")

    source, target = _validate_paths(input_path, output_path)
    root = package_dir or _package_dir()
    env, _executable = _tesseract_environment(root)

    previous_environment = os.environ.copy()
    os.environ.update(env)
    try:
        with tempfile.TemporaryDirectory(
            prefix=".pdf-escolar-ocr-",
            dir=str(target.parent),
        ) as work_directory:
            temporary_output = Path(work_directory) / "resultado.pdf"
            try:
                ocrmypdf.configure_logging(
                    Verbosity.quiet,
                    progress_bar_friendly=False,
                    manage_root_logger=True,
                )
                result = ocrmypdf.ocr(
                    str(source),
                    str(temporary_output),
                    language=languages,
                    output_type="pdf",
                    mode="skip",
                    rasterizer="pypdfium",
                    rotate_pages=True,
                    deskew=True,
                    jobs=1,
                    optimize=0,
                    progress_bar=False,
                    pages=pages or None,
                )
            except Exception as exc:
                raise CompanionError(
                    "No pudimos reconocer el texto. Comprobá que el PDF sea válido, "
                    "que no tenga contraseña y que las páginas sean legibles."
                ) from exc

            if result != ExitCode.ok:
                raise CompanionError(
                    "No pudimos crear el PDF buscable. Comprobá que el documento sea válido "
                    "y que las páginas seleccionadas se puedan leer."
                )
            if not temporary_output.is_file() or temporary_output.stat().st_size == 0:
                raise CompanionError("El reconocimiento no generó un PDF válido.")

            document = None
            try:
                document = pdfium.PdfDocument(str(temporary_output))
                page_count = len(document)
            except Exception as exc:
                raise CompanionError("El resultado OCR no es un PDF válido.") from exc
            finally:
                if document is not None:
                    document.close()

            if page_count == 0:
                raise CompanionError("El PDF resultante no contiene páginas.")

            os.replace(temporary_output, target)
            return page_count
    finally:
        os.environ.clear()
        os.environ.update(previous_environment)


def _parse_languages(value: str) -> list[str]:
    languages = [part.strip() for part in value.split("+") if part.strip()]
    if not languages or any(language not in SUPPORTED_LANGUAGES for language in languages):
        raise argparse.ArgumentTypeError("Los idiomas admitidos son spa, eng o spa+eng.")
    if len(set(languages)) != len(languages):
        raise argparse.ArgumentTypeError("No repitas idiomas en la selección.")
    return languages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Complemento OCR local de PDF Escolar.",
    )
    parser.add_argument("--check", action="store_true", help="Verificar la instalación del complemento.")
    parser.add_argument("--input", help="PDF de origen.")
    parser.add_argument("--output", help="Ruta del PDF buscable nuevo.")
    parser.add_argument(
        "--language",
        type=_parse_languages,
        default=["spa"],
        help="Idiomas: spa (predeterminado), eng o spa+eng.",
    )
    parser.add_argument(
        "--pages",
        help="Páginas que se procesarán, por ejemplo 1-3, 6. Vacío = todas.",
    )
    args = parser.parse_args(argv)

    try:
        if args.check:
            print(check_installation())
            return 0
        if not args.input or not args.output:
            parser.error("Para procesar un documento indicá --input y --output.")

        page_count = run_ocr(
            args.input,
            args.output,
            languages=args.language,
            pages=args.pages,
        )
        print(f"Listo. El PDF buscable tiene {page_count} páginas.")
        return 0
    except CompanionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception:
        logging.getLogger(__name__).exception("Error interno del complemento OCR")
        print(
            "No pudimos completar el reconocimiento. El PDF original no se modificó.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
