"""Vectorise FIDÈLEMENT le logo fourni (brand/logo-source.webp) : aucune forme redessinée, seulement un calque de contour.

Sortie dans web/brand/ : symbol.svg (le h-houle), wordmark.svg (le mot), lockup.svg (les deux, empilés comme l'original),
plus lockup.png (fond transparent, pour l'image de partage). Couleur de remplissage = couleur de l'original.
Usage : python -m tools.trace_logo   (Pillow, numpy et potracer requis)
"""
from pathlib import Path

import numpy as np
import potrace
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "brand" / "logo-source.webp"
OUT = ROOT / "web" / "brand"
SAND = "#E9C694"          # couleur mesurée sur l'original
BG = np.array([3, 11, 17], dtype=float)
UP = 3                    # agrandissement avant tracé (contours plus lisses)


def load_mask():
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im, dtype=float)
    sand = np.array([233, 198, 148], dtype=float)
    # alpha = position entre le fond (0) et le sable (1)
    t = ((a - BG) @ (sand - BG)) / float(((sand - BG) ** 2).sum())
    return np.clip(t, 0, 1)


def bbox(mask, y0, y1, thr=0.35, pad=0):
    sub = mask[y0:y1] > thr
    ys, xs = np.where(sub)
    return xs.min() - pad, ys.min() + y0 - pad, xs.max() + 1 + pad, ys.max() + y0 + 1 + pad


def trace(mask, box):
    x0, y0, x1, y1 = box
    crop = Image.fromarray((mask[y0:y1, x0:x1] * 255).astype("uint8")).resize(((x1 - x0) * UP, (y1 - y0) * UP), Image.LANCZOS)
    bm = potrace.Bitmap(np.asarray(crop) <= 127)
    plist = bm.trace(turdsize=8, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0, opticurve=True, opttolerance=0.4)
    d = []
    f = lambda p: f"{p.x / UP:.1f} {p.y / UP:.1f}"
    for curve in plist:
        d.append("M" + f(curve.start_point))
        for seg in curve.segments:
            if seg.is_corner:
                d.append("L" + f(seg.c) + "L" + f(seg.end_point))
            else:
                d.append("C" + f(seg.c1) + " " + f(seg.c2) + " " + f(seg.end_point))
        d.append("Z")
    return "".join(d), (x1 - x0, y1 - y0)


def svg(paths, w, h, fill=SAND):
    body = "".join(f'<path d="{d}" transform="translate({tx} {ty})" fill-rule="evenodd"/>' for d, tx, ty in paths)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" fill="{fill}">{body}</svg>'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mask = load_mask()
    h_img = mask.shape[0]
    split = 660                                     # entre le symbole (en haut) et le mot (en bas)
    sb = bbox(mask, 0, split)
    wb = bbox(mask, split, h_img)
    sd, (sw, sh) = trace(mask, sb)
    wd, (ww, wh) = trace(mask, wb)
    (OUT / "symbol.svg").write_text(svg([(sd, 0, 0)], sw, sh), encoding="utf-8")
    (OUT / "wordmark.svg").write_text(svg([(wd, 0, 0)], ww, wh), encoding="utf-8")
    # lockup empilé, comme l'original (positions relatives conservées)
    lx0, ly0 = min(sb[0], wb[0]), sb[1]
    lx1, ly1 = max(sb[2], wb[2]), wb[3]
    lockup = svg([(sd, sb[0] - lx0, sb[1] - ly0), (wd, wb[0] - lx0, wb[1] - ly0)], lx1 - lx0, ly1 - ly0)
    (OUT / "lockup.svg").write_text(lockup, encoding="utf-8")
    # PNG transparent (image de partage)
    rgba = np.zeros((ly1 - ly0, lx1 - lx0, 4), dtype="uint8")
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 233, 198, 148
    rgba[..., 3] = (mask[ly0:ly1, lx0:lx1] * 255).astype("uint8")
    Image.fromarray(rgba, "RGBA").save(OUT / "lockup.png", optimize=True)
    Image.fromarray(np.dstack([rgba[sb[1] - ly0:sb[3] - ly0, sb[0] - lx0:sb[2] - lx0, :3], (mask[sb[1]:sb[3], sb[0]:sb[2]] * 255).astype("uint8")]), "RGBA").save(OUT / "symbol.png", optimize=True)
    print("symbole", sb, "mot", wb, "| tailles", (sw, sh), (ww, wh))


if __name__ == "__main__":
    main()
