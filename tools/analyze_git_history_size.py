"""Audit unique Git objects and large historical blobs without modifying repository history."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

MIB = 1024 * 1024


def _run_git(repo: Path, *args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_text,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="surrogateescape",
    )
    return result.stdout.strip()


def _reachable_objects(repo: Path) -> tuple[dict[str, str], list[str]]:
    """Return unique object IDs and one representative path per reachable object."""
    output = _run_git(repo, "rev-list", "--objects", "--all")
    object_ids: set[str] = set()
    paths: dict[str, str] = {}
    for line in output.splitlines():
        if not line:
            continue
        object_id, _, path = line.partition(" ")
        object_ids.add(object_id)
        if path and object_id not in paths:
            paths[object_id] = path
    return paths, sorted(object_ids)


def _current_downloads(repo: Path, head: str | None) -> list[dict[str, Any]]:
    """List regular blobs currently tracked under descargas/ at HEAD."""
    if head is None:
        return []
    output = _run_git(repo, "ls-tree", "-r", "-l", "-z", head, "--", "descargas/")
    files: list[dict[str, Any]] = []
    for record in output.split("\0"):
        if not record:
            continue
        metadata, separator, path = record.partition("\t")
        if not separator:
            continue
        fields = metadata.split()
        if len(fields) < 4 or fields[1] != "blob":
            continue
        try:
            size = int(fields[3])
        except ValueError:
            continue
        files.append({"path": path, "sha": fields[2], "size_bytes": size})
    return sorted(files, key=lambda item: (-item["size_bytes"], item["path"]))


def build_report(repo: Path, *, min_size_bytes: int) -> dict[str, Any]:
    """Collect a read-only inventory of unique reachable Git blobs."""
    repo = repo.expanduser().resolve()
    head = None
    try:
        _run_git(repo, "rev-parse", "--git-dir")
        try:
            head = _run_git(repo, "rev-parse", "HEAD")
        except subprocess.CalledProcessError:
            pass
        shallow = _run_git(repo, "rev-parse", "--is-shallow-repository").lower() == "true"
        refs_output = _run_git(repo, "for-each-ref", "--format=%(refname)")
        refs = [ref for ref in refs_output.splitlines() if ref]
        count_objects = _run_git(repo, "count-objects", "-vH")
        paths, object_ids = _reachable_objects(repo)
        sizes_output = _run_git(
            repo,
            "cat-file",
            "--batch-check=%(objectname) %(objecttype) %(objectsize)",
            input_text="".join(f"{object_id}\n" for object_id in object_ids),
        )
    except FileNotFoundError as exc:
        raise RuntimeError("No se encontró Git. Instalá Git y volvé a ejecutar la auditoría.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise RuntimeError(
            f"No se pudo leer el repositorio Git en {repo}: {detail or 'comando Git fallido'}"
        ) from exc

    blobs: list[dict[str, Any]] = []
    reachable_object_count = 0
    for line in sizes_output.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        object_id, object_type, size_text = fields
        reachable_object_count += 1
        if object_type != "blob":
            continue
        try:
            size = int(size_text)
        except ValueError:
            continue
        blobs.append(
            {
                "sha": object_id,
                "size_bytes": size,
                "path": paths.get(object_id, "(sin ruta representativa)"),
            }
        )

    blobs.sort(key=lambda item: (-item["size_bytes"], item["sha"]))
    large_blobs = [blob for blob in blobs if blob["size_bytes"] >= min_size_bytes]
    downloads = _current_downloads(repo, head)
    downloads_total = sum(item["size_bytes"] for item in downloads)
    return {
        "repository_path": str(repo),
        "head": head,
        "shallow_clone": shallow,
        "refs": refs,
        "reachable_object_count": reachable_object_count,
        "unique_reachable_blob_count": len(blobs),
        "unique_reachable_blob_bytes": sum(blob["size_bytes"] for blob in blobs),
        "large_blob_threshold_bytes": min_size_bytes,
        "large_blob_count": len(large_blobs),
        "large_blob_bytes": sum(blob["size_bytes"] for blob in large_blobs),
        "large_blobs": large_blobs,
        "current_descargas_files": downloads,
        "current_descargas_total_bytes": downloads_total,
        "git_count_objects": count_objects,
        "notes": [
            "Los tamaños de blobs son lógicos (sin compresión ni deltas); no equivalen al tamaño del paquete Git ni al valor size de la API de GitHub.",
            "Se consideran los objetos alcanzables desde las referencias presentes en este clon. Un clon superficial o con ramas/etiquetas no descargadas dará una vista incompleta del historial.",
            "Git identifica el contenido por SHA; el mismo blob usado en varias rutas se cuenta una sola vez. La ruta informada es representativa, no una lista completa de todas sus apariciones históricas.",
        ],
    }


def _mib(size_bytes: int) -> str:
    return f"{size_bytes / MIB:,.2f} MiB"


def format_report(report: dict[str, Any], *, top_n: int) -> str:
    refs = report["refs"]
    output = [
        "Auditoría de tamaño del historial Git (solo lectura)",
        f"Repositorio: {report['repository_path']}",
        f"HEAD: {report['head'] or '(sin HEAD)'}",
        f"Referencias locales: {len(refs)}",
        f"Clon superficial: {'sí; el historial es incompleto' if report['shallow_clone'] else 'no'}",
        f"Objetos alcanzables únicos: {report['reachable_object_count']:,}",
        f"Blobs alcanzables únicos: {report['unique_reachable_blob_count']:,} ({_mib(report['unique_reachable_blob_bytes'])})",
        (
            f"Blobs de al menos {_mib(report['large_blob_threshold_bytes'])}: "
            f"{report['large_blob_count']:,} ({_mib(report['large_blob_bytes'])})"
        ),
        "",
        "Archivos que hoy están en descargas/ (HEAD):",
    ]
    downloads = report["current_descargas_files"]
    if downloads:
        for item in downloads:
            output.append(f"  {_mib(item['size_bytes']):>13}  {item['path']}")
        output.append(f"  {'TOTAL':>13}  {_mib(report['current_descargas_total_bytes'])}")
    else:
        output.append("  (no hay archivos regulares bajo descargas/ en HEAD)")

    output.extend(["", f"Blobs más grandes (máximo {top_n}):"])
    large_blobs = report["large_blobs"][:top_n]
    if large_blobs:
        for blob in large_blobs:
            output.append(f"  {_mib(blob['size_bytes']):>13}  {blob['sha']}  {blob['path']}")
    else:
        output.append("  (ninguno alcanza el umbral)")
    output.extend(["", "Tamaño de almacenamiento local informado por git count-objects -vH:"])
    output.extend(f"  {line}" for line in report["git_count_objects"].splitlines())
    output.extend(["", "Advertencias:"])
    output.extend(f"  - {note}" for note in report["notes"])
    if not refs:
        output.append("  - No se encontraron referencias locales; el inventario podría estar vacío.")
    return "\n".join(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Ruta al repositorio Git (incluye clones bare/mirror).")
    parser.add_argument(
        "--min-size-mib",
        type=int,
        default=10,
        help="Umbral inclusivo de tamaño para listar blobs, en MiB (por defecto: 10).",
    )
    parser.add_argument("--top", type=int, default=30, help="Cantidad máxima de blobs grandes a mostrar (por defecto: 30).")
    parser.add_argument("--json", dest="json_path", type=Path, help="Guardar el inventario completo, incluidos todos los blobs sobre el umbral, en JSON.")
    args = parser.parse_args(argv)
    if args.min_size_mib < 1:
        parser.error("--min-size-mib debe ser al menos 1.")
    if args.top < 1:
        parser.error("--top debe ser al menos 1.")

    try:
        report = build_report(args.repo, min_size_bytes=args.min_size_mib * MIB)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(format_report(report, top_n=args.top))
    if report["shallow_clone"]:
        print(
            "\nATENCIÓN: este clon es superficial. Repetí el análisis en un clon espejo completo.",
            file=sys.stderr,
        )
    if args.json_path:
        try:
            args.json_path.expanduser().resolve().write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            print(f"No se pudo escribir el informe JSON: {exc}", file=sys.stderr)
            return 2
        print(f"\nInforme JSON guardado en: {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
