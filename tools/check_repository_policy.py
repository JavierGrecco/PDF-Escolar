"""Guard pull requests against large blobs and manual edits to release downloads."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath


MAX_TRACKED_FILE_BYTES = 20 * 1024 * 1024
DOWNLOADS_DIRECTORY = "descargas/"


def policy_violations(
    changed_paths: Iterable[str],
    file_sizes: Mapping[str, int | None],
    *,
    max_file_size: int = MAX_TRACKED_FILE_BYTES,
) -> list[str]:
    """Return human-readable violations for the files changed by a pull request."""
    violations: list[str] = []
    for path in sorted(set(changed_paths)):
        normalized = PurePosixPath(path).as_posix()
        if normalized.startswith(DOWNLOADS_DIRECTORY):
            violations.append(
                f"{normalized}: descargas/ se actualiza únicamente mediante "
                "el flujo Build installers con una sincronización o publicación explícita."
            )
            continue

        size = file_sizes.get(path)
        # A missing blob means the path was deleted. Deletions are not a new
        # source of repository growth, so they are allowed by this size policy.
        if size is not None and size > max_file_size:
            mebibytes = size / (1024 * 1024)
            limit_mib = max_file_size / (1024 * 1024)
            violations.append(
                f"{normalized}: {mebibytes:.1f} MiB supera el límite de "
                f"{limit_mib:.0f} MiB para un archivo versionado."
            )
    return violations


def _run_git(*args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout if binary else result.stdout.decode("utf-8", errors="replace").strip()


def changed_paths(base: str, head: str) -> list[str]:
    """List changed file paths without relying on commit ancestry or a full clone."""
    output = _run_git("diff", "--name-only", "-z", "--no-renames", base, head, binary=True)
    assert isinstance(output, bytes)
    return [
        path.decode("utf-8", errors="surrogateescape")
        for path in output.split(b"\0")
        if path
    ]


def blob_size(revision: str, path: str) -> int | None:
    """Return a blob's size, or None if it was deleted or is not a regular blob."""
    try:
        output = _run_git("cat-file", "-s", f"{revision}:{path}")
    except subprocess.CalledProcessError:
        return None
    assert isinstance(output, str)
    try:
        return int(output)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="Base commit SHA of the pull request.")
    parser.add_argument("--head", default="HEAD", help="Commit/tree to validate (default: HEAD).")
    parser.add_argument(
        "--max-mib",
        type=int,
        default=20,
        help="Maximum size in MiB for a newly added or modified tracked file.",
    )
    args = parser.parse_args()
    if args.max_mib < 1:
        parser.error("--max-mib debe ser al menos 1.")

    try:
        paths = changed_paths(args.base, args.head)
        sizes = {
            path: blob_size(args.head, path)
            for path in paths
            if not PurePosixPath(path).as_posix().startswith(DOWNLOADS_DIRECTORY)
        }
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        print(f"No se pudo comparar el árbol del PR: {detail}", file=sys.stderr)
        return 2

    violations = policy_violations(
        paths,
        sizes,
        max_file_size=args.max_mib * 1024 * 1024,
    )
    if violations:
        print("La política del repositorio encontró cambios que requieren otra vía:", file=sys.stderr)
        for violation in violations:
            print(f" - {violation}", file=sys.stderr)
        print(
            "\nNo se borran ni se modifican las descargas oficiales desde un PR. "
            "Usá Build installers con las opciones explícitas de publicación/sincronización. "
            "Los archivos grandes deben distribuirse como assets de GitHub Releases o revisarse "
            "por separado antes de versionarlos.",
            file=sys.stderr,
        )
        return 1

    print(
        f"Política de tamaño aprobada: {len(paths)} archivo(s) cambiado(s); "
        f"límite por archivo {args.max_mib} MiB. descargas/ permanece intacta."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
