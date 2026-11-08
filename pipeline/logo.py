"""Logo Houlalah : un « h » dont l'arche se prolonge en une houle qui s'effile (trait continu, sans cran au raccord).

Une seule définition géométrique, utilisée par le site (en-tête), les pages de spots (seo.py), l'icône d'onglet et l'image de
partage (tools/make_og.py). Le mot « houlalah » s'écrit en entier à côté du symbole.
Pour retoucher : changer STEM, CENTER, W0 / W1 ci-dessous, relancer `python -m tools.make_og`, puis reporter inline_svg() et
favicon_uri() dans web/index.html (voir CLAUDE.md).
"""
import math
from urllib.parse import quote

SAND, INK = "#E4C79B", "#0B1316"
VIEWBOX = (6, 0, 196, 140)          # x, y, largeur, hauteur
STEM = (20, 10, 36, 120, 16)         # x, y, largeur, hauteur, rayon des angles
# Ligne médiane de la houle : trois courbes de Bézier (départ dans la tige, crête, creux, remontée finale).
CENTER = [
    ((42, 64), (56, 55), (68, 42), (86, 42)),
    ((84, 42), (106, 42), (118, 90), (140, 90)),
    ((140, 90), (158, 90), (172, 76), (188, 70)),
]
W0, W1 = 36.0, 16.0                  # épaisseur au départ (comme la tige) et à la pointe


def _bez(p, t):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = p
    u = 1 - t
    x = u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3
    y = u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3
    dx = 3 * u * u * (x1 - x0) + 6 * u * t * (x2 - x1) + 3 * t * t * (x3 - x2)
    dy = 3 * u * u * (y1 - y0) + 6 * u * t * (y2 - y1) + 3 * t * t * (y3 - y2)
    return x, y, dx, dy


def tail_outline(step=40):
    """Contour (liste de points) de la houle à épaisseur variable, avec un bout arrondi."""
    pts = []
    for seg in CENTER:
        for i in range(step):
            pts.append(_bez(seg, i / step))
    pts.append(_bez(CENTER[-1], 1.0))
    n = len(pts) - 1
    left, right = [], []
    for k, (x, y, dx, dy) in enumerate(pts):
        s = k / n
        w = W0 + (W1 - W0) * (s ** 1.15)
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    x, y, dx, dy = pts[-1]
    ln = math.hypot(dx, dy)
    a0 = math.atan2(dy, dx)
    r = W1 / 2
    cap = [(x + r * math.cos(a0 + math.pi / 2 - j * math.pi / 14), y + r * math.sin(a0 + math.pi / 2 - j * math.pi / 14)) for j in range(15)]
    # `left` est à +normale ; le demi-cercle va de la gauche vers la droite en passant par l'avant
    return left + cap + right[::-1]


def _path(points):
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in points) + "Z"


def stem_path():
    x, y, w, h, r = STEM
    stem = (f"M{x + r} {y}H{x + w - r}A{r} {r} 0 0 1 {x + w} {y + r}V{y + h - r}A{r} {r} 0 0 1 {x + w - r} {y + h}"
            f"H{x + r}A{r} {r} 0 0 1 {x} {y + h - r}V{y + r}A{r} {r} 0 0 1 {x + r} {y}Z")
    return stem


def shape_paths(fill):
    """Deux formes de même couleur (la tige et la houle), qui se fondent en un seul symbole."""
    return f'<path d="{stem_path()}" fill="{fill}"/><path d="{_path(tail_outline())}" fill="{fill}"/>'


def inline_svg(height=26, fill=SAND, cls=""):
    vx, vy, vw, vh = VIEWBOX
    width = round(height * vw / vh, 1)
    c = f' class="{cls}"' if cls else ""
    return (f'<svg{c} width="{width}" height="{height}" viewBox="{vx} {vy} {vw} {vh}" aria-hidden="true">'
            f'{shape_paths(fill)}</svg>')


def favicon_uri():
    """Icône d'onglet : carré arrondi sable, symbole sombre (lisible sur onglet clair comme sombre)."""
    vx, vy, vw, vh = VIEWBOX
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="24" fill="{SAND}"/>'
           f'<g transform="translate(8 25) scale(0.4)"><g transform="translate({-vx} 0)">{shape_paths(INK)}</g></g></svg>')
    return "data:image/svg+xml," + quote(svg, safe="/:=,;()' .-")
