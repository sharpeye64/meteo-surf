"""Images de partage (1200 x 630) : une par spot et par bouée, avec la mesure ou la prévision du moment.

Elles s'affichent quand on colle un lien dans WhatsApp, Instagram, Facebook, Messenger…
Polices du site (Manrope, Unbounded, licence OFL) rangées dans pipeline/fonts pour un rendu identique partout.
Si Pillow manque ou si une image échoue, la page garde l'image générale web/og.png (rien ne casse)."""
import math
from pathlib import Path

W, H, S = 1200, 630, 2
HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
BRAND_DIR = HERE.parent / "web" / "brand"
SAND, MUTED, INK = (244, 226, 184), (174, 182, 180), (10, 17, 20)

_cache = {}


def _font(name, size, weight):
    from PIL import ImageFont
    key = (name, size, weight)
    if key not in _cache:
        f = ImageFont.truetype(str(FONTS / name), int(size * S))
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        _cache[key] = f
    return _cache[key]


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _background():
    """Fond mer sombre + trois vagues discrètes en bas. Calculé une seule fois, copié ensuite."""
    if "bg" in _cache:
        return _cache["bg"].copy()
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
    img = Image.new("RGB", (W * S, H * S), INK)
    d = ImageDraw.Draw(img)
    top, mid, bot = (10, 17, 20), (15, 36, 48), (10, 17, 20)
    for y in range(H * S):
        t = y / (H * S)
        d.line([(0, y), (W * S, y)], fill=_lerp(top, mid, t / .5) if t < .5 else _lerp(mid, bot, (t - .5) / .5))
    glow = Image.new("RGB", img.size, (0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = int(W * .78 * S), int(H * .22 * S)
    for r in range(560 * S, 0, -8 * S):
        k = (1 - r / (560 * S)) ** 2.2
        g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(int(c * k * .55) for c in (40, 110, 140)))
    img = ImageChops.add(img, glow.filter(ImageFilter.GaussianBlur(24 * S)))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for base, amp, per, col, a in ((470, 26, 380, (67, 184, 201), 46), (520, 24, 330, (141, 191, 178), 40), (570, 20, 300, (244, 226, 184), 28)):
        pts = [(x, (base + math.sin(x / (S * per) * 2 * math.pi + base) * amp) * S) for x in range(0, W * S + 8, 8)]
        ld.polygon(pts + [(W * S, H * S), (0, H * S)], fill=col + (a,))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    _cache["bg"] = img
    return img.copy()


def _fit(draw, text, name, size, weight, maxw):
    while size > 40:
        f = _font(name, size, weight)
        if draw.textlength(text, font=f) <= maxw * S:
            return f
        size -= 4
    return _font(name, 40, weight)


def _pill(img, x, y, label, value, unit, big):
    """Pastille : sable pour la houle (principale), verre sombre pour le reste. Retourne la largeur occupée."""
    from PIL import Image, ImageDraw
    d = ImageDraw.Draw(img)
    fl = _font("Manrope.ttf", 16, 800)
    fv = _font("Manrope.ttf", 70 if big else 56, 800)
    fu = _font("Manrope.ttf", 32 if big else 26, 700)
    wv, wu = d.textlength(value, font=fv), d.textlength(unit, font=fu)
    pw = max(wv + wu + (6 * S if unit else 0), d.textlength(label.upper(), font=fl) + 8 * S) + 60 * S
    ph = 124 * S
    mask = Image.new("L", (int(pw), ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, int(pw) - 1, ph - 1], radius=26 * S, fill=255)
    if big:
        g = Image.new("RGB", mask.size)
        gd = ImageDraw.Draw(g)
        for i in range(int(pw) + ph):
            gd.line([(i, 0), (i - ph, ph)], fill=_lerp((244, 226, 184), (227, 194, 131), i / (pw + ph)))
        img.paste(g, (int(x * S), int(y * S)), mask)
        ink, lab, uni = (42, 33, 18), (110, 92, 56), (110, 92, 56)
    else:
        veil = Image.new("RGB", mask.size, (255, 255, 255))
        img.paste(veil, (int(x * S), int(y * S)), mask.point(lambda v: int(v * .09)))
        ImageDraw.Draw(img).rounded_rectangle([int(x * S), int(y * S), int(x * S + pw) - 1, int(y * S) + ph - 1], radius=26 * S, outline=(70, 82, 88), width=S)
        ink, lab, uni = (242, 239, 232), (150, 160, 158), (150, 160, 158)
    d = ImageDraw.Draw(img)
    px, py = x * S + 30 * S, y * S
    d.text((px, py + 16 * S), label.upper(), font=fl, fill=lab)
    base = py + ph - 24 * S
    d.text((px, base), value, font=fv, fill=ink, anchor="ls")
    if unit:
        d.text((px + wv + 8 * S, base), unit, font=fu, fill=uni, anchor="ls")
    return pw / S


def render(out, tag, live, title, sub, pills):
    """pills : liste de (libellé, valeur, unité) ; la première est mise en avant."""
    from PIL import Image, ImageDraw
    img = _background()
    d = ImageDraw.Draw(img)
    lock = Image.open(BRAND_DIR / "lockup.png").convert("RGBA")
    lw = 150 * S
    lock = lock.resize((lw, int(lw * lock.height / lock.width)), Image.LANCZOS)
    img.paste(lock, (70 * S, 46 * S), lock)
    d = ImageDraw.Draw(img)
    ft = _font("Manrope.ttf", 22, 800)
    d.text((W * S - 70 * S - d.textlength(tag.upper(), font=ft), 62 * S), tag.upper(), font=ft, fill=MUTED)
    fl = _font("Manrope.ttf", 22, 800)
    d.ellipse([70 * S, 222 * S, 82 * S, 234 * S], fill=(31, 157, 85))
    d.text((96 * S, 215 * S), live.upper(), font=fl, fill=SAND)
    f = _fit(d, title, "Unbounded.ttf", 76, 700, 1060)
    d.text((70 * S, 248 * S), title, font=f, fill=(242, 239, 232))
    d.text((70 * S, 360 * S), sub, font=_font("Manrope.ttf", 28, 500), fill=MUTED)
    x = 70
    for i, (lab, val, unit) in enumerate(pills):
        x += _pill(img, x, 430, lab, val, unit, i == 0) + 18
    fu = _font("Manrope.ttf", 26, 800)
    d.text((W * S - 70 * S - d.textlength("houlalah.fr", font=fu), 556 * S), "houlalah.fr", font=fu, fill=SAND)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.resize((W, H), Image.LANCZOS).save(out, optimize=True)
    return out


def _fr(x, nd=1):
    return f"{x:.{nd}f}".replace(".", ",")


def _sector(deg):
    sec = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    return "" if deg is None else sec[int((deg % 360) / 22.5 + .5) % 16]


def spot_image(root, sp, t, now):
    """root/og/spots/<slug>.png ; retourne l'adresse relative (og/spots/<slug>.png) ou None si impossible."""
    try:
        if not t or t.get("hs") is None:
            return None
        pills = [("Houle", _fr(t["hs"]), "m")]
        if t.get("tp") is not None:
            pills.append(("Période", _fr(t["tp"], 0), "s"))
        if t.get("wind") is not None:
            pills.append(("Vent", _fr(t["wind"], 0), "km/h " + _sector(t.get("wdir"))))
        rel = f"og/spots/{sp['slug']}.png"
        render(Path(root) / rel, "Prévisions surf", f"Aujourd'hui · mis à jour à {now:%H} h {now:%M}", sp["name"],
               f"{sp['commune'] if sp['commune'] != sp['name'] else sp['region']} · {sp['type']}", pills)
        return rel
    except Exception:
        return None


def buoy_image(root, b, now):
    try:
        L = b["L"]
        pills = [("Houle", _fr(L["hs"]), "m")]
        if L.get("tp") is not None:
            pills.append(("Période", _fr(L["tp"], 0), "s"))
        if L.get("dir") is not None:
            pills.append(("Direction", _sector(L["dir"]), ""))
        if L.get("sst") is not None:
            pills.append(("Eau", _fr(L["sst"]), "°C"))
        rel = f"og/bouees/{b['slug']}.png"
        hh = L["time"][11:13].lstrip("0") or "0"
        render(Path(root) / rel, "Bouée en direct", f"Mesure réelle · relevé de {hh} h {L['time'][14:16]}", f"Bouée {b['name']}",
               b["sub"][:1].upper() + b["sub"][1:], pills)
        return rel
    except Exception:
        return None
