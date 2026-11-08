"""Génère web/og.png (1200x630), l'image d'aperçu quand on partage le lien (WhatsApp, Instagram, X…).
Usage : python -m tools.make_og   (Pillow requis ; polices Windows Segoe UI / Bahnschrift)."""
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H, S = 1200, 630, 2           # taille finale, facteur de lissage
OUT = Path(__file__).resolve().parent.parent / "web" / "og.png"
SAND, INK, MUTED = (228, 199, 155), (10, 17, 20), (174, 182, 180)
FONTS = Path("C:/Windows/Fonts")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size * S)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


img = Image.new("RGB", (W * S, H * S), INK)
d = ImageDraw.Draw(img)
top, mid, bot = (10, 17, 20), (20, 33, 40), (31, 58, 66)
for y in range(H * S):                      # ciel puis mer : dégradé vertical
    t = y / (H * S)
    d.line([(0, y), (W * S, y)], fill=lerp(top, mid, t / 0.62) if t < 0.62 else lerp(mid, bot, (t - 0.62) / 0.38))

glow = Image.new("RGB", img.size, (0, 0, 0))   # soleil bas sur l'horizon, à droite
g = ImageDraw.Draw(glow)
cx, cy = int(W * 0.76 * S), int(H * 0.62 * S)
for r in range(520 * S, 0, -6 * S):
    k = (1 - r / (520 * S)) ** 2.4
    g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(c * k * 0.55) for c in (240, 190, 120)))
glow = glow.filter(ImageFilter.GaussianBlur(18 * S))
img = ImageChops.add(img, glow)
d = ImageDraw.Draw(img)
d.ellipse([cx - 46 * S, cy - 46 * S, cx + 46 * S, cy + 46 * S], fill=(255, 232, 190))   # disque du soleil

hy = cy                                       # lignes de vagues sous l'horizon
for i, (amp, alpha) in enumerate([(7, 120), (10, 90), (14, 60), (18, 40)]):
    y0 = hy + (22 + i * 38) * S
    pts = [(x, y0 + math.sin(x / (S * (70 + i * 22)) + i * 1.3) * amp * S) for x in range(0, W * S + 8, 8)]
    col = lerp((31, 58, 66), SAND, alpha / 255)
    d.line(pts, fill=col, width=3 * S, joint="curve")
d.line([(0, hy), (W * S, hy)], fill=lerp((31, 58, 66), SAND, .35), width=2 * S)

# logo : trait de vague + mot-symbole
lx, ly = 84 * S, 186 * S
d.line([(lx + i * 2.4 * S, ly + math.sin(i / 7.0) * 15 * S) for i in range(0, 62)], fill=SAND, width=7 * S, joint="curve")
d.text((lx + 160 * S, 106 * S), "houlalah", font=font("seguibl.ttf", 104), fill=(244, 240, 232))
d.text((lx, 262 * S), "Prévisions surf, de Lacanau à Hendaye", font=font("segoeuib.ttf", 40), fill=SAND)
d.text((lx, 322 * S), "Houle · vent · marée · coefficient", font=font("segoeui.ttf", 34), fill=MUTED)
d.text((lx, 540 * S), "58 spots · croisés entre plusieurs modèles · vérifiés avec les bouées", font=font("segoeui.ttf", 26), fill=(150, 160, 158))

OUT.parent.mkdir(parents=True, exist_ok=True)
img.resize((W, H), Image.LANCZOS).save(OUT, optimize=True)
print("OK", OUT, OUT.stat().st_size // 1024, "Ko")
