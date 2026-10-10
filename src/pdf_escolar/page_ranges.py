"""Parse and validate one-based PDF page selections."""
from __future__ import annotations
import re


def parse_page_ranges(specification: str, total_pages: int) -> list[int]:
    """Return zero-based indexes, preserving the order entered by the user."""
    if total_pages < 1:
        raise ValueError("El PDF no contiene páginas.")
    if not specification or not specification.strip():
        raise ValueError("Indicá qué páginas querés incluir.")
    selected: list[int] = []
    for raw_token in specification.split(","):
        token = raw_token.strip()
        if not token:
            raise ValueError("Hay un elemento vacío en la selección de páginas.")
        if re.fullmatch(r"\d+", token):
            start = end = int(token)
        else:
            match = re.fullmatch(r"(\d*)\s*-\s*(\d*)", token)
            if not match:
                raise ValueError(f"No entiendo el rango «{token}». Usá, por ejemplo, 1-8, 12, 20-25.")
            raw_start, raw_end = match.groups()
            if not raw_start and not raw_end:
                raise ValueError(f"El rango «{token}» está vacío.")
            start = int(raw_start) if raw_start else 1
            end = int(raw_end) if raw_end else total_pages
        if start < 1 or end < 1:
            raise ValueError("Los números de página empiezan en 1.")
        if start > total_pages or end > total_pages:
            raise ValueError(f"El PDF tiene {total_pages} páginas; el rango «{token}» supera ese límite.")
        if start > end:
            raise ValueError(f"El rango «{token}» está invertido; el inicio supera al final.")
        selected.extend(range(start - 1, end))
    return selected
