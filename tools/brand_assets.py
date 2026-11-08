"""Icônes dérivées du logo fourni (web/brand/symbol.png, produit par tools.trace_logo) : favicon.svg, apple-touch-icon.png, icon-512.png.
Usage : python -m tools.trace_logo && python -m tools.brand_assets"""
import re
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "web" / "brand"
SAND, INK = (233, 198, 148), (11, 19, 22)


def favicon_svg():
    sym = (OUT / "symbol.svg").read_text(encoding="utf-8")
    w, h = map(float, re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', sym).groups())
    body = re.search(r">(.*)</svg>", sym, re.S).group(1)
    k = 64 / w                                   # le symbole occupe 64 % de la largeur de l'icône
    tx, ty = (100 - w * k) / 2, (100 - h * k) / 2
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="24" fill="#E9C694"/>'
           f'<g transform="translate({tx:.2f} {ty:.2f}) scale({k:.5f})" fill="#0B1316">{body}</g></svg>')
    (OUT / "favicon.svg").write_text(svg, encoding="utf-8")


def png_icon(size, name, radius=0.24):
    sym = Image.open(OUT / "symbol.png").convert("RGBA")
    S = 4
    big = size * S
    base = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(base).rounded_rectangle([0, 0, big - 1, big - 1], radius=int(big * radius), fill=SAND + (255,))
    sw = int(big * 0.64)
    sh = int(sw * sym.height / sym.width)
    alpha = sym.split()[3].resize((sw, sh), Image.LANCZOS)
    ink = Image.new("RGBA", (sw, sh), INK + (255,))
    base.paste(ink, ((big - sw) // 2, (big - sh) // 2), alpha)
    base.resize((size, size), Image.LANCZOS).save(OUT / name, optimize=True)


if __name__ == "__main__":
    favicon_svg()
    png_icon(180, "apple-touch-icon.png", radius=0.0)   # iOS arrondit lui-même
    png_icon(512, "icon-512.png")
    print("OK", [p.name for p in OUT.iterdir()])
