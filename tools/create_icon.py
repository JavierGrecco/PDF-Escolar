"""Generate the PDF Escolar application icon in portable PNG and Windows ICO formats."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SIZE = 1024


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    # Paint a smooth blue background and clip it to a rounded-square app tile.
    base = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gradient = Image.new("RGBA", (SIZE, SIZE))
    pixels = gradient.load()
    top = (43, 91, 208)
    bottom = (31, 55, 126)
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = tuple(round(top[c] * (1 - t) + bottom[c] * t) for c in range(3)) + (255,)
        for x in range(SIZE):
            pixels[x, y] = color
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((28, 28, SIZE - 28, SIZE - 28), radius=210, fill=255)
    base.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(base)
    # A clean, folded page with a subtle blue-gray shadow.
    draw.rounded_rectangle((254, 150, 770, 830), radius=44, fill=(15, 34, 91, 90))
    draw.rounded_rectangle((230, 126, 746, 806), radius=42, fill=(255, 255, 255, 255))
    draw.polygon([(600, 126), (746, 272), (600, 272)], fill=(211, 226, 255, 255))
    draw.line((600, 126, 600, 272, 746, 272), fill=(163, 190, 244, 255), width=12)

    # Page lines and a simple selection mark communicate school material + PDF tools.
    blue = (48, 87, 194, 255)
    for y, end_x in [(365, 645), (440, 645), (515, 560)]:
        draw.rounded_rectangle((310, y, end_x, y + 22), radius=11, fill=(198, 211, 239, 255))
    draw.rounded_rectangle((308, 610, 670, 735), radius=30, fill=blue)
    font = load_font(74)
    label = "PDF"
    bounds = draw.textbbox((0, 0), label, font=font)
    tw, th = bounds[2] - bounds[0], bounds[3] - bounds[1]
    draw.text(((SIZE - tw) / 2, 631 - bounds[1]), label, font=font, fill="white")

    png = ASSETS / "pdf-escolar.png"
    ico = ASSETS / "pdf-escolar.ico"
    base.save(png, format="PNG", optimize=True)
    base.save(
        ico,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Generated {png} and {ico}")


if __name__ == "__main__":
    main()
