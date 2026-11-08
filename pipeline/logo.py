"""Logo Houlalah : un rond en contour sable, cinq houles identiques et parallèles (symétrique gauche/droite et haut/bas).

Une seule définition géométrique, utilisée par le site (index.html), les pages de spots (seo.py) et l'image de partage
(tools/make_og.py). Pour le modifier, changer ROWS / AMP / HALF ici puis relancer `python -m tools.make_og` et reporter
le résultat de `inline_svg()` dans l'en-tête de web/index.html si besoin.
"""
import math
from urllib.parse import quote

SAND, INK = "#E4C79B", "#0B1316"
ROWS = [28, 39, 50, 61, 72]   # cinq rangées équidistantes autour de y = 50
AMP = 4.5                      # amplitude de chaque houle
HALF = 25.0                    # demi-longueur d'onde : deux vagues complètes sur la largeur


def wave_path(y0, amp=AMP, half=HALF):
    """Cosinusoïde en Bézier, creux en x = 50 : symétrique exactement par rapport à x = 50."""
    c, m = 0.37 * half, math.ceil(60 / half)
    xs = [50 + j * half for j in range(-m, m + 1)]
    ys = [y0 + amp * (1 if j % 2 == 0 else -1) for j in range(-m, m + 1)]
    d = f"M{xs[0]:g} {ys[0]:.2f}"
    for i in range(len(xs) - 1):
        d += f"C{xs[i] + c:g} {ys[i]:.2f} {xs[i + 1] - c:g} {ys[i + 1]:.2f} {xs[i + 1]:g} {ys[i + 1]:.2f}"
    return d


def inner(sw, ring=SAND, bg=INK, uid="lg"):
    paths = "".join(f'<path d="{wave_path(y)}"/>' for y in ROWS)
    return (f'<clipPath id="{uid}"><circle cx="50" cy="50" r="46"/></clipPath>'
            f'<circle cx="50" cy="50" r="47" fill="{bg}" stroke="{ring}" stroke-width="3"/>'
            f'<g clip-path="url(#{uid})" fill="none" stroke="{ring}" stroke-width="{sw}" stroke-linecap="round">{paths}</g>')


def inline_svg(size=30, sw=4.4, uid="lg", cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<svg{c} width="{size}" height="{size}" viewBox="0 0 100 100" aria-hidden="true">{inner(sw, uid=uid)}</svg>'


def favicon_uri():
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{inner(6.4, uid="f")}</svg>'
    return "data:image/svg+xml," + quote(svg, safe="/:=,;()' .-")
