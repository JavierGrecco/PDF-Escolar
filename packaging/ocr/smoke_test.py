"""Build-time end-to-end test for a bundled OCR companion."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from pdfminer.high_level import extract_text
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def create_scanned_pdf(destination: Path) -> None:
    """Generate a raster-only page with high-contrast Spanish test text."""
    image = Image.new("RGB", (1654, 2339), "white")
    draw = ImageDraw.Draw(image)
    heading = "PDF ESCOLAR"
    message = "PRUEBA DE RECONOCIMIENTO DE TEXTO"
    heading_font = _font(100)
    message_font = _font(58)

    def centered(text: str, top: int, font: ImageFont.ImageFont) -> None:
        left, upper, right, lower = draw.textbbox((0, 0), text, font=font)
        width = right - left
        draw.text(((image.width - width) / 2, top), text, fill="black", font=font)

    centered(heading, 700, heading_font)
    centered(message, 880, message_font)

    image_pdf = destination.with_suffix(".png")
    image.save(image_pdf, format="PNG", dpi=(200, 200))
    page = canvas.Canvas(str(destination), pagesize=A4)
    page.drawImage(ImageReader(image_pdf), 0, 0, width=A4[0], height=A4[1])
    page.showPage()
    page.save()
    image_pdf.unlink(missing_ok=True)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: smoke_test.py RUTA_AL_EJECUTABLE_OCR")
    executable = Path(sys.argv[1]).resolve()
    if not executable.is_file():
        raise FileNotFoundError(f"No se encontró el ejecutable OCR: {executable}")

    with tempfile.TemporaryDirectory(prefix="pdf-escolar-ocr-smoke-") as temporary:
        directory = Path(temporary)
        source = directory / "escaneo.pdf"
        output = directory / "buscable.pdf"
        create_scanned_pdf(source)

        check = subprocess.run(
            [str(executable), "--check"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if check.returncode:
            raise RuntimeError(
                "La comprobación del complemento OCR falló: "
                + (check.stderr.strip() or check.stdout.strip())
            )

        result = subprocess.run(
            [
                str(executable),
                "--input",
                str(source),
                "--output",
                str(output),
                "--language",
                "spa+eng",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=900,
        )
        if result.returncode:
            raise RuntimeError(
                "El OCR de prueba no terminó correctamente: "
                + (result.stderr.strip() or result.stdout.strip())
            )
        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError("El OCR no creó el PDF de salida.")

        extracted = " ".join(extract_text(str(output)).upper().split())
        if "PDF ESCOLAR" not in extracted or "RECONOCIMIENTO" not in extracted:
            raise RuntimeError(
                f"El PDF de prueba no contiene el texto reconocido esperado: {extracted!r}"
            )
        print(f"Prueba OCR aprobada: {extracted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
