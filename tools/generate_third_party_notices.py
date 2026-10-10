"""Create a build-specific third-party license manifest for packaged builds.

The collector follows installed runtime dependency metadata, includes readable
license/notice files from those distributions, and records package versions
and declared license metadata. It deliberately fails if core license texts
cannot be found.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from importlib import metadata
from pathlib import Path, PurePosixPath

try:
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
except ImportError as exc:  # pragma: no cover - packaging is a PDF dependency
    raise SystemExit(
        "No se pudo generar el inventario de licencias: falta el paquete packaging."
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "packaging" / "app" / "THIRD-PARTY-NOTICES.md"
PROJECT_LICENSE_PATH = ROOT / "LICENSE"
TEXT_SUFFIXES = {
    "",
    ".txt",
    ".md",
    ".rst",
    ".html",
    ".htm",
    ".xml",
    ".json",
    ".license",
    ".notice",
    ".adoc",
    ".rtf",
}
MAX_LICENSE_FILE_BYTES = 2 * 1024 * 1024
CORE_NAMES = {"pyside6", "pikepdf", "pypdfium2", "pillow"}
PACKAGER_NAMES = {"pyinstaller"}


def distribution_index() -> dict[str, metadata.Distribution]:
    result: dict[str, metadata.Distribution] = {}
    for dist in metadata.distributions():
        name = dist.metadata.get("Name")
        if name:
            result.setdefault(canonicalize_name(name), dist)
    return result


def runtime_closure(
    installed: dict[str, metadata.Distribution],
) -> dict[str, metadata.Distribution]:
    """Resolve installed runtime requirements, honoring environment markers."""
    queue = ["pdf-escolar"]
    selected: dict[str, metadata.Distribution] = {}
    while queue:
        name = canonicalize_name(queue.pop())
        if name in selected:
            continue
        dist = installed.get(name)
        if dist is None:
            raise RuntimeError(
                f"No se encontró la dependencia requerida «{name}» al generar el inventario."
            )
        selected[name] = dist
        for raw_requirement in dist.requires or ():
            try:
                requirement = Requirement(raw_requirement)
            except Exception as exc:
                raise RuntimeError(
                    f"No se pudo interpretar una dependencia de "
                    f"{dist.metadata.get('Name')}: {raw_requirement}"
                ) from exc
            if requirement.marker and not requirement.marker.evaluate():
                continue
            queue.append(canonicalize_name(requirement.name))
    return selected


def metadata_license(dist: metadata.Distribution) -> str:
    expression = (dist.metadata.get("License-Expression") or "").strip()
    legacy = (dist.metadata.get("License") or "").strip()
    classifiers = [
        value.split("::", 1)[1].strip()
        for value in dist.metadata.get_all("Classifier", [])
        if value.startswith("License ::")
    ]
    candidates = []
    for value in (expression, legacy):
        if value and value.casefold() not in {"unknown", "none"} and value not in candidates:
            candidates.append(value)
    for value in classifiers:
        if value not in candidates:
            candidates.append(value)
    return "; ".join(candidates) if candidates else "No especificada en los metadatos"


def project_url(dist: metadata.Distribution) -> str:
    values = dist.metadata.get_all("Project-URL", [])
    for value in values:
        label, separator, url = value.partition(",")
        if separator and any(
            key in label.casefold() for key in ("source", "homepage", "repository")
        ):
            return url.strip()
    return (dist.metadata.get("Home-page") or "").strip()


def is_license_candidate(relative: PurePosixPath) -> bool:
    parts = [part.casefold() for part in relative.parts]
    name = parts[-1]
    suffix = PurePosixPath(name).suffix
    if suffix not in TEXT_SUFFIXES:
        return False

    license_directories = {
        "licenses",
        "license",
        "third-party-licenses",
        "third_party_licenses",
        "thirdpartylicenses",
        "build_licenses",
        "build-licenses",
    }
    if any(part in license_directories for part in parts[:-1]):
        return True

    stems = ("license", "licence", "copying", "notice", "copyright", "patent")
    if any(
        name == stem or name.startswith(f"{stem}.") or name.startswith(f"{stem}-")
        for stem in stems
    ):
        return True
    # Qt wheels also ship SPDX-named license texts at the package root,
    # for example LGPL-3.0-only.txt or GFDL-1.3-no-invariants-only.txt.
    spdx_prefixes = (
        "agpl-", "apache-", "bsd-", "cc0-", "cc-by-", "fdl-", "gfdl-",
        "gpl-", "lgpl-", "mpl-", "isc-", "mit", "qt-gpl-", "zlib-",
        "openssl-", "unlicense",
    )
    if name.startswith(spdx_prefixes):
        return True

    # Some Qt frameworks ship notices such as qtwebenginecore_licenses.rtf.
    if "_license" in name or "_licence" in name or name.endswith(("_license", "_licence")):
        return True
    return False


def _rtf_to_text(source: str) -> str:
    """Convert common RTF control sequences to readable plain text."""
    text = re.sub(
        r"{\\\*\\(?:fonttbl|colortbl|stylesheet|info|generator)[^{}]*}",
        "",
        source,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\\'([0-9a-fA-F]{2})",
        lambda match: bytes.fromhex(match.group(1)).decode("cp1252"),
        text,
    )
    text = re.sub(r"\\(?:par|line)\b\s?", "\n", text)
    text = re.sub(r"\\tab\b\s?", "\t", text)
    text = re.sub(r"\\[a-zA-Z]+-?\d*\s?", "", text)
    text = re.sub(r"\\([{}\\])", r"\1", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def read_text(path: Path) -> str:
    data = path.read_bytes()
    if len(data) > MAX_LICENSE_FILE_BYTES:
        raise ValueError(f"El archivo de licencia supera el límite de 2 MiB: {path.name}")
    if b"\x00" in data:
        raise ValueError(f"El archivo señalado como licencia parece binario: {path.name}")
    if path.suffix.casefold() == ".rtf":
        return _rtf_to_text(data.decode("cp1252", errors="replace"))
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer el texto de licencia: {path.name}")

_QT_LICENSE_FALLBACK_ROOTS: set[str] = set()


def collect_license_files(
    name: str, dist: metadata.Distribution
) -> list[tuple[str, str]]:
    """Read text license files recorded in a distribution, with a Qt resource fallback."""
    candidates: dict[str, tuple[str, str]] = {}
    for relative_file in dist.files or ():
        relative_text = str(relative_file).replace("\\", "/")
        relative = PurePosixPath(relative_text)
        if not is_license_candidate(relative):
            continue
        try:
            absolute = Path(dist.locate_file(relative_file))
            if not absolute.is_file():
                continue
            content = read_text(absolute)
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                f"No se pudo incorporar un aviso de {name} ({relative_text}): {exc}"
            ) from exc
        if content:
            candidates[relative_text] = (relative_text, content)

    # Some Qt wheels ship native framework license resources that are present on
    # disk but omitted from their .dist-info RECORD. Search the shared Qt package
    # only when normal metadata collection found no notices, and only once.
    if name.startswith("pyside6"):
        qt_root = Path(dist.locate_file("PySide6"))
        root_key = str(qt_root.resolve())
        if root_key not in _QT_LICENSE_FALLBACK_ROOTS and qt_root.is_dir():
            _QT_LICENSE_FALLBACK_ROOTS.add(root_key)
            for absolute in qt_root.rglob("*"):
                if not absolute.is_file():
                    continue
                relative = PurePosixPath(absolute.relative_to(qt_root).as_posix())
                if not is_license_candidate(relative):
                    continue
                relative_text = f"PySide6/{relative.as_posix()}"
                try:
                    content = read_text(absolute)
                except (OSError, ValueError) as exc:
                    raise RuntimeError(
                        f"No se pudo incorporar un aviso de Qt ({relative_text}): {exc}"
                    ) from exc
                if content:
                    candidates.setdefault(relative_text, (relative_text, content))

    return [candidates[key] for key in sorted(candidates)]


def render_manifest() -> str:
    installed = distribution_index()
    runtime = runtime_closure(installed)
    missing_core = CORE_NAMES - set(runtime)
    if missing_core:
        raise RuntimeError(
            "La instalación no incluye todos los componentes principales: "
            + ", ".join(sorted(missing_core))
        )

    # PyInstaller's bootloader is part of the packaged executable even though
    # PyInstaller itself is a build tool rather than an app dependency.
    components = dict(runtime)
    for name in PACKAGER_NAMES:
        if name in installed:
            components[name] = installed[name]

    files_by_component: dict[str, list[tuple[str, str]]] = {}
    for name, dist in sorted(components.items()):
        files_by_component[name] = collect_license_files(name, dist)

    core_groups = {
        "Qt for Python": {
            name for name in components
            if name.startswith("pyside6") or name == "shiboken6"
        },
        "pikepdf": {"pikepdf"},
        "pypdfium2 / PDFium": {"pypdfium2"},
        "Pillow": {"pillow"},
    }
    missing_texts = [
        label
        for label, names in core_groups.items()
        if not any(files_by_component.get(name) for name in names)
    ]
    if missing_texts:
        raise RuntimeError(
            "No se encontraron textos de licencia de los componentes: "
            + ", ".join(missing_texts)
            + ". No se generó un manifiesto incompleto."
        )

    try:
        template = TEMPLATE_PATH.read_text(encoding="utf-8").strip()
        project_license = PROJECT_LICENSE_PATH.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"No se pudieron leer los avisos base del proyecto: {exc}") from exc

    lines = [
        template,
        "",
        "## Inventario de este paquete",
        "",
        "Los datos se obtuvieron de los metadatos de las distribuciones instaladas "
        "en el entorno de compilación. «Licencia declarada» transcribe la información "
        "disponible; no es una interpretación legal.",
        "",
        "| Componente | Versión | Licencia declarada | Proyecto |",
        "|---|---|---|---|",
    ]
    for name, dist in sorted(
        components.items(),
        key=lambda item: item[1].metadata.get("Name", item[0]).casefold(),
    ):
        display_name = dist.metadata.get("Name", name)
        version = dist.version
        license_name = metadata_license(dist).replace("|", "\\|").replace("\n", " ")
        url = project_url(dist)
        url_cell = f"[Sitio del proyecto]({url})" if url else "No indicada"
        lines.append(f"| {display_name} | {version} | {license_name} | {url_cell} |")

    lines.extend(
        [
            "",
            "## Textos de licencia y avisos encontrados",
            "",
            "Se incluyen abajo los textos de licencia y avisos legibles que figuran en las "
            "listas de archivos de las distribuciones instaladas. Si una dependencia cambia "
            "su empaquetado, este inventario debe revisarse en la próxima actualización.",
        ]
    )

    unique_texts: dict[str, dict[str, object]] = {}
    for name, dist in sorted(components.items()):
        display_name = dist.metadata.get("Name", name)
        for relative_path, content in files_by_component[name]:
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            entry = unique_texts.setdefault(
                digest, {"content": content, "sources": []}
            )
            entry["sources"].append(f"{display_name} {dist.version} — {relative_path}")

    for digest, entry in sorted(
        unique_texts.items(),
        key=lambda item: str(item[1]["sources"][0]).casefold(),
    ):
        sources = entry["sources"]
        lines.extend(
            [
                "",
                f"### {sources[0]}",
                "",
            ]
        )
        if len(sources) > 1:
            lines.append("Este mismo texto también se encontró en:")
            lines.extend(f"- {source}" for source in sources[1:])
            lines.append("")
        lines.extend(
            [
                str(entry["content"]),
                "",
                f"SHA-256 del texto: {digest}",
                "",
            ]
        )

    lines.extend(
        [
            "## Licencia del código de PDF Escolar",
            "",
            "PDF Escolar, código propio de Javier Grecco:",
            "",
            project_license,
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Ruta donde escribir el inventario de licencias generado.",
    )
    args = parser.parse_args()
    try:
        manifest = render_manifest()
    except Exception as exc:
        print(f"Error al generar los avisos de terceros: {exc}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(manifest, encoding="utf-8", newline="\n")
    required_names = ("PySide6", "pikepdf", "pypdfium2", "Pillow", "pyinstaller")
    missing_names = [
        name for name in required_names if name.casefold() not in manifest.casefold()
    ]
    if missing_names:
        args.output.unlink(missing_ok=True)
        print(
            "El inventario generado no menciona estos componentes requeridos: "
            + ", ".join(missing_names),
            file=sys.stderr,
        )
        return 1
    print(
        f"Inventario de licencias generado: {args.output} "
        f"({len(manifest)} caracteres)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
