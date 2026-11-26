"""Pages statiques pour le référencement (SEO) : une page par spot, une page d'index, sitemap.xml et robots.txt.

Chaque page contient du vrai texte et un tableau de prévisions (pas seulement du JavaScript) : les moteurs de recherche
et les réseaux sociaux la lisent directement. Les pages sont régénérées à chaque passage, avec les prévisions du moment.
"""
import html
import json
import math
import re
import shutil
import statistics
import unicodedata
from datetime import datetime

from . import config
from .seotext import fit, fit_desc

SECTORS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
BRAND = "Houlalah"


def slugify(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def sector(deg):
    return None if deg is None else SECTORS[int((deg % 360) / 22.5 + 0.5) % 16]


def circ_mean(vals):
    v = [x for x in vals if x is not None]
    if not v:
        return None
    sx = sum(math.sin(math.radians(a)) for a in v)
    sy = sum(math.cos(math.radians(a)) for a in v)
    return math.degrees(math.atan2(sx, sy)) % 360


def med(vals):
    v = [x for x in vals if x is not None]
    return statistics.median(v) if v else None


def fr(x, nd=1):
    return "—" if x is None else f"{x:.{nd}f}".replace(".", ",")


def day_rows(sp, coef):
    m, w = sp["marine"], sp["wind"]
    by = {}
    for i, t in enumerate(m["time"]):
        by.setdefault(t[:10], []).append(i)
    rows = []
    for date, idx in sorted(by.items()):
        day = [i for i in idx if 7 <= int(m["time"][i][11:13]) <= 20]
        if len(day) < 6:
            continue
        g = lambda arr, key=None: [arr[i] for i in day if i < len(arr)]
        h = med(g(m["wave_height"]))
        if h is None:
            continue
        wi = [i for i, t in enumerate(w["time"]) if t[:10] == date and 7 <= int(t[11:13]) <= 20]
        d = datetime.strptime(date, "%Y-%m-%d")
        rows.append({
            "date": date, "label": DAYS[d.weekday()].capitalize(), "dm": d.strftime("%d/%m"),
            "hs": h, "hmin": min(x for x in g(m["wave_height"]) if x is not None), "hmax": max(x for x in g(m["wave_height"]) if x is not None),
            "tp": med(g(m["wave_period"])), "dir": circ_mean(g(m["wave_direction"])),
            "wind": med([w["wind_speed_10m"][i] for i in wi]), "wdir": circ_mean([w["wind_direction_10m"][i] for i in wi]),
            "coef": max(coef.get(date) or [0]) or None,
        })
    return rows


def hourly(sp, now):
    """La journée toutes les 3 h (6 h à 21 h), à partir des prévisions horaires déjà calculées. Après 19 h : le lendemain."""
    from datetime import timedelta
    m, w = sp["marine"], sp["wind"]
    day = (now + timedelta(days=1 if now.hour >= 19 else 0)).strftime("%Y-%m-%d")
    mi = {t: i for i, t in enumerate(m["time"])}
    wi = {t: i for i, t in enumerate(w["time"])}
    g = lambda d, k, i: (d.get(k) or [None] * (i + 1))[i] if i is not None and i < len(d.get(k) or []) else None
    out = []
    for h in (6, 9, 12, 15, 18, 21):
        t = f"{day}T{h:02d}:00"
        i, j = mi.get(t), wi.get(t)
        hs = g(m, "wave_height", i)
        if hs is None:
            continue
        out.append({"h": h, "hs": hs, "tp": g(m, "wave_period", i), "dir": g(m, "wave_direction", i),
                    "w": g(w, "wind_speed_10m", j), "wd": g(w, "wind_direction_10m", j), "gust": g(w, "wind_gusts_10m", j)})
    return {"day": day, "rows": out}


def tide_days(sp, coef):
    """Pleines et basses mers de la semaine (horaires calculés pour le port de référence du spot, décalage du spot compris)."""
    t = sp.get("tide") or {}
    by = {}
    for x in t.get("extremes") or []:
        by.setdefault(x["t"][:10], []).append(x)
    rows = []
    for date in sorted(by)[:7]:
        d = datetime.strptime(date, "%Y-%m-%d")
        fmt = lambda x: f"{int(x['t'][11:13])} h {x['t'][14:16]}" + (f" ({fr(x['h'])} m)" if x.get("h") is not None else "")
        rows.append({"label": DAYS[d.weekday()].capitalize(), "dm": d.strftime("%d/%m"),
                     "pm": [fmt(x) for x in by[date] if x["type"] == "PM"], "bm": [fmt(x) for x in by[date] if x["type"] == "BM"],
                     "coef": max(coef.get(date) or [0]) or None})
    return {"port": t.get("label"), "rows": rows}


WIND_WORD = {"lisse": "Lisse", "offshore": "Offshore", "side-off": "Side-offshore", "de côté": "Side-shore", "onshore": "Onshore"}


def wind_for_spot(v, wd, ori):
    """Même règle que le site (windInfo) : vent rapporté à l'orientation PROPRE du spot (offshore = vent de terre)."""
    if v is None or wd is None or ori is None:
        return None
    if v < 8:
        return "lisse"
    d = _angle(wd, (ori + 180) % 360)
    return "offshore" if d <= 45 else "side-off" if d <= 80 else "de côté" if d <= 120 else "onshore"


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


CSS = """:root{--bg:#F3EFE6;--card:#FFFDF8;--text:#0B1B26;--muted:#5F6B71;--sand:#8A6418;--gold:#D9A441;--aqua:#1C6EA6;--edge:rgba(11,27,38,.09);--navy:#0B1B26;--cream:#F3EFE6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 Manrope,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--text);text-decoration-color:rgba(11,27,38,.35);text-underline-offset:3px}a:hover{text-decoration-color:currentColor}
.band{position:relative;background:radial-gradient(900px 380px at 88% -20%,rgba(48,118,160,.5),transparent 62%),url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='44' viewBox='0 0 240 44'%3E%3Cpath d='M0 22Q30 10 60 22T120 22T180 22T240 22' fill='none' stroke='rgba(243,239,230,0.07)'/%3E%3C/svg%3E"),#0B1B26;color:var(--cream)}
.band header{max-width:900px;margin:0 auto;padding:18px 20px 22px;display:flex;justify-content:space-between;align-items:center}
.band:after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:16px;background:var(--bg);-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 16' preserveAspectRatio='none'%3E%3Cpath d='M0 16V9C100 1 200 1 300 9S500 17 600 9 800 1 900 9 1100 17 1200 9V16Z'/%3E%3C/svg%3E") center/100% 100% no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 16' preserveAspectRatio='none'%3E%3Cpath d='M0 16V9C100 1 200 1 300 9S500 17 600 9 800 1 900 9 1100 17 1200 9V16Z'/%3E%3C/svg%3E") center/100% 100% no-repeat}
.band .top{color:rgba(243,239,230,.85);font-weight:700;font-size:14px;text-decoration:none;border:1px solid rgba(243,239,230,.18);border-radius:999px;padding:7px 14px;transition:background .15s}.band .top:hover{background:rgba(243,239,230,.08)}
main{max-width:900px;margin:0 auto;padding:30px 20px 60px}
.brand{font-weight:700;text-decoration:none;color:var(--cream);letter-spacing:.01em;display:inline-flex;align-items:center;gap:9px}.mk{display:block;width:auto;height:26px}.bw{display:block;width:auto;height:15px}
h1{font:700 clamp(30px,5.4vw,48px)/1.05 Unbounded,system-ui,sans-serif;letter-spacing:-.045em;margin:0 0 14px}h2{font:700 21px/1.2 Unbounded,system-ui,sans-serif;letter-spacing:-.035em;margin:38px 0 14px}
.lead{font-size:18px;color:var(--text);margin:0 0 20px}.muted{color:var(--muted);font-size:14px}
.cta{display:inline-flex;align-items:center;gap:8px;background:var(--navy);color:var(--cream);font-weight:800;padding:13px 22px;border-radius:999px;text-decoration:none;margin:6px 0 10px;box-shadow:0 14px 30px -16px rgba(11,27,38,.6);transition:transform .2s}.cta:hover{transform:translateY(-1px)}
table{width:100%;border-collapse:collapse;background:var(--card);border-radius:18px;overflow:hidden;box-shadow:0 0 0 1px var(--edge),0 20px 40px -32px rgba(11,27,38,.35);font-variant-numeric:tabular-nums}
th,td{padding:11px 14px;text-align:left;border-top:1px solid var(--edge);font-size:15px}thead th{border-top:0;color:var(--muted);font-size:11.5px;text-transform:uppercase;letter-spacing:.08em}
dl.fiche{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:0 0 16px}dl.fiche div{background:var(--card);border-radius:16px;padding:12px 15px;box-shadow:0 0 0 1px var(--edge)}dl.fiche dt{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:800}dl.fiche dd{margin:4px 0 0;font-weight:700}
ul.near{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
ul.near a{display:block;background:var(--card);border-radius:16px;padding:13px 15px;text-decoration:none;color:var(--text);box-shadow:0 0 0 1px var(--edge);transition:box-shadow .15s,transform .15s}ul.near a:hover{transform:translateY(-1px);box-shadow:0 0 0 1px rgba(11,27,38,.2)}ul.near small{display:block;color:var(--muted)}
.grp{margin-top:26px}.grp h2{color:var(--text)}footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--edge);color:var(--muted);font-size:13px}footer nav{margin-bottom:6px}footer a{color:var(--muted)}
.prose p,.prose li{max-width:68ch}.prose ul{padding-left:20px}
@media (max-width:640px){table{display:block;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}th,td{padding:10px 12px}}"""


def country_of(region):
    """Pays d'un spot d'après sa région (données structurées : FR, ES ou PT)."""
    return "ES" if region in ("Espagne Nord", "Galice") else "PT" if region.startswith("Portugal") else "FR"


def org(site):
    """L'éditeur du site, déclaré sur toutes les pages (données structurées) : Houlalah, sans nom de personne."""
    return {"@context": "https://schema.org", "@type": "Organization", "@id": f"{site}/#org", "name": BRAND, "url": f"{site}/",
            "logo": f"{site}/brand/icon-512.png", "email": "contact@houlalah.fr",
            "description": "Prévisions surf de la Bretagne au Portugal, vérifiées avec les mesures des bouées en mer."}


def page(site, title, desc, canonical, body, jsonld, base="../../", extra_css="", top=None, og_image=None):
    og = f"{site}/{og_image}" if og_image else f"{site}/og.png"
    top = top or ("Tous les spots", "spots/")
    for j in jsonld:   # chaque page se rattache à l'éditeur
        if j.get("@type") in ("WebPage", "CollectionPage", "AboutPage"):
            j.setdefault("publisher", {"@id": f"{site}/#org"})
    jsonld = [org(site)] + list(jsonld)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in jsonld)
    esc = html.escape
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND}"><meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{og}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{og}"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<meta name="theme-color" content="#0B1B26">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@700;800&family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<script data-goatcounter="https://houlalah.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
<link rel="icon" href="{base}brand/favicon.svg" type="image/svg+xml"><link rel="icon" href="{base}brand/icon-192.png" sizes="192x192" type="image/png"><link rel="shortcut icon" href="{base}favicon.ico"><link rel="apple-touch-icon" href="{base}brand/apple-touch-icon.png">
<style>{CSS}{extra_css}</style>{ld}</head><body><div class="band">
<header><a class="brand" href="{base}"><img class="mk" src="{base}brand/symbol.svg" alt="" height="26"><img class="bw" src="{base}brand/wordmark.svg" alt="{BRAND}" height="15"></a><a class="top" href="{base}{top[1]}">{top[0]}</a></header></div><main>
<div class="prose">{body}</div>
<footer><nav aria-label="Informations"><a href="{base}comment-ca-marche/">Comment ça marche</a> · <a href="{base}a-propos/">À propos</a> · <a href="{base}mentions-legales/">Mentions légales</a> · <a href="{base}confidentialite/">Confidentialité</a></nav><br>Prévisions calculées à partir de plusieurs modèles (Météo-France, DWD, ECMWF, NOAA, Ifremer) via Open-Meteo, corrigées avec les bouées. Estimations : à confirmer sur place. {BRAND} est un prototype non commercial.</footer>
</main></body></html>"""


def _angle(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _low(x):
    return x[:1].lower() + x[1:] if x else x


def _profile_generic(sp, t):
    esc = html.escape
    name, ori = sp["name"], sp["ori"]
    off_dir = (ori + 180) % 360
    p = (f"<p><b>{esc(name)}</b> ({esc(sp['region'])}) : la plage fait face au secteur {esc(sector(ori))}. Le vent de terre, qui lisse la surface, "
         f"vient donc du secteur {esc(sector(off_dir))} ; un vent du secteur {esc(sector(ori))} est un vent de mer qui hache les vagues.")
    if t and t.get("wdir") is not None:
        d = _angle(t["wdir"], off_dir)
        kindw = "de terre" if d <= 60 else ("de travers" if d <= 120 else "de mer")
        p += f" Aujourd'hui, le vent de {fr(t['wind'], 0)} km/h vient du secteur {esc(sector(t['wdir']))} : c'est un vent {kindw} ici."
    p += "</p>"
    items = [("Orientation", f"vers le {sector(ori)}")]
    dl = "".join(f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>" for k, v in items)
    return (f'<h2>{esc(name)} en bref</h2><dl class="fiche">{dl}</dl>{p}'
            '<p class="muted">Fiche détaillée (fond, niveau, marée idéale) bientôt disponible. Repères indicatifs, à confirmer sur place.</p>')


def profile_html(sp, t):
    """« Le spot en bref » : fiche tirée des champs du spot (orientation, fond, marée, niveau, taille) + lecture des conditions du jour.
    Rien n'est inventé : tout vient de pipeline/spots.json et des prévisions."""
    esc = html.escape
    name, ori = sp["name"], sp.get("ori")
    off_dir = None if ori is None else (ori + 180) % 360
    if sp.get("generic"):   # spot ajouté sans fiche détaillée : seuls l'orientation et les prévisions sont connus, rien n'est inventé
        return _profile_generic(sp, t)
    kind = _low(sp["type"])
    p1 = (f"<b>{esc(name)}</b> est un spot de type {esc(kind)} à {esc(sp['commune'])} ({esc(sp['region'])}), au fond de {esc(_low(sp['bottom']))}. "
          f"Il fonctionne en général avec une houle de {fr(sp['min'])} à {fr(sp['max'])} m orientée {esc(sp['swell'])}. ")
    lvl = sp.get("level") or ""
    if lvl in ("Expert", "Big wave / tow-in"):
        p1 += "C'est un spot exigeant, réservé aux surfeurs très expérimentés : renseigne-toi sur place avant de t'y mettre à l'eau."
    elif lvl in ("Débutant", "Débutant / longboard", "Débutant → intermédiaire"):
        p1 += "Il convient bien aux débutants et aux longboardeurs."
    elif lvl == "Tous":
        p1 += "Il est accessible à tous les niveaux quand la taille reste raisonnable."
    elif lvl:
        p1 += f"Niveau conseillé : {esc(_low(lvl))}."
    if sp.get("notes"):
        p1 += " À noter : " + esc(_low(sp["notes"]).rstrip(".")) + "."
    p2 = ""
    if ori is not None:
        p2 = (f"Le spot est orienté vers le secteur {esc(sector(ori))}. Le vent de terre, qui lisse la surface, vient donc du secteur {esc(sector(off_dir))} ; "
              f"un vent du secteur {esc(sector(ori))} est un vent de mer qui hache les vagues.")
        if t and t.get("wdir") is not None:
            d = _angle(t["wdir"], off_dir)
            kindw = "de terre" if d <= 60 else ("de travers" if d <= 120 else "de mer")
            p2 += f" Aujourd'hui, le vent de {fr(t['wind'], 0)} km/h vient du secteur {esc(sector(t['wdir']))} : c'est un vent {kindw} ici."
        if t and t.get("dir") is not None:
            lo, hi = (247.5, 337.5) if "à" in sp["swell"] else (292.5, 337.5)
            inw = lo <= t["dir"] % 360 <= hi
            p2 += (f" La houle arrive du secteur {esc(sector(t['dir']))}, " + ("dans la fenêtre habituelle du spot." if inw else "en dehors de la fenêtre habituelle du spot, ce qui réduit ce qu'elle apporte."))
    items = [("Type", sp["type"]), ("Fond", sp["bottom"]), ("Niveau", lvl or "—"), ("Marée", sp.get("tide") or "—"),
             ("Houle", sp["swell"]), ("Taille", f"{fr(sp['min'])} à {fr(sp['max'])} m")]
    dl = "".join(f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>" for k, v in items)
    return (f'<h2>{esc(name)} en bref</h2><dl class="fiche">{dl}</dl><p>{p1}</p>' + (f"<p>{p2}</p>" if p2 else "") +
            '<p class="muted">Repères indicatifs, à confirmer sur place : fonds, courants et dangers changent avec les tempêtes et les saisons.</p>')


def spot_page(site, sp, spots_meta, payload, now, og_image=None):
    name, slug = sp["name"], sp["slug"]
    rows = sp["rows"]
    t = rows[0] if rows else None
    esc = html.escape
    where = sp["commune"] if sp["commune"] != name else sp["region"]
    # la commune dans le titre et le h1 : on cherche « météo surf Hossegor » plus souvent que « La Gravière »
    same = lambda a, b: slugify(a).replace("-", "") in slugify(b).replace("-", "")   # « Vieux-Boucau » est déjà dans « Vieux Boucau »
    full = f"{name} ({sp['commune']})" if sp["commune"] and not same(sp["commune"], name) else name
    # « Météo surf » et le nom du spot passent avant la marque : sans place, on retire d'abord « | Houlalah »
    title = fit(f"Météo surf {full} : houle, vent et marée | {BRAND}", f"Météo surf {full} : houle et marée | {BRAND}",
                f"Météo surf {full} : houle et marée", f"Météo surf {full} | {BRAND}", f"Météo surf {full}", f"Surf {full}")
    if t:
        today = (f"Houle de {fr(t['hs'])} m à {name} ({where}) aujourd'hui, période {fr(t['tp'], 0)} s, vent {fr(t['wind'], 0)} km/h"
                 f"{' (' + sector(t['wdir']) + ')' if t['wdir'] is not None else ''}.")
        desc = fit_desc(today + " Prévisions 7 jours, marées et coefficients, mises à jour toutes les heures.",
                        today + " Prévisions 7 jours, marées et coefficients.", today + " Prévisions 7 jours et marées.", today)
    else:
        desc = fit_desc(f"Prévisions surf à {name} ({where}) : houle, vent, marée et coefficient sur 7 jours.")
    canonical = f"{site}/spots/{slug}/"
    app = f"../../?spot={slug}"
    trs = "".join(
        f"<tr><td>{r['label']} {r['dm']}</td><td>{fr(r['hmin'])}–{fr(r['hmax'])} m</td><td>{fr(r['tp'], 0)} s {sector(r['dir']) or ''}</td>"
        f"<td>{fr(r['wind'], 0)} km/h {sector(r['wdir']) or ''}</td><td>{r['coef'] or '—'}</td></tr>" for r in rows)
    near = sorted((o for o in spots_meta if o["slug"] != slug), key=lambda o: hav(sp, o))[:6]
    nl = "".join(f'<li><a href="../{o["slug"]}/">{esc(o["name"])}<small>{round(hav(sp, o))} km · {esc(o["commune"])}</small></a></li>' for o in near)
    lead = (f"Aujourd'hui à <b>{esc(name)}</b> : houle de <b>{fr(t['hs'])} m</b> toutes les <b>{fr(t['tp'], 0)} s</b>"
            f"{' venant du ' + sector(t['dir']) if t['dir'] is not None else ''}, vent de {fr(t['wind'], 0)} km/h"
            f"{' du ' + sector(t['wdir']) if t['wdir'] is not None else ''}"
            f"{', coefficient de marée ' + str(t['coef']) if t['coef'] else ''}.") if t else ""
    buoy_line = ""
    try:
        g = payload.get("gascogne") or {}
        pool = (payload.get("coast") or []) + (payload.get("offshore") or []) + ([dict(g, id="gascogne", name="Gascogne")] if g.get("lat") is not None else [])
        # même choix que le site et l'appli : bouée abritée réservée à ses spots, bouée de référence des Landes
        cb = [b for b in pool if (b.get("latest") or {}).get("hs") is not None and not b.get("silent")
              and (not config.BUOY_ONLY.get(b["name"]) or name in config.BUOY_ONLY[b["name"]])]
        dist = lambda x: hav(sp, {"lat": float(x["lat"]), "lon": float(x["lon"])})
        ref = config.ref_buoy(sp)
        b = next((x for x in cb if x["id"] == ref), None)
        if b is None and ref == "03302":
            b = next((x for x in cb if x["id"] == "gascogne"), None)
        label = "Bouée de référence"
        if b is None:
            near_b = [x for x in cb if x["id"] != "gascogne"]
            b = min(near_b, key=dist) if near_b else None
            label = "Bouée la plus proche"
            if b is not None and dist(b) > 80:
                b = None
        if b is not None:
            buoy_line = (f'<p class="muted">{label} : <a href="../../bouees/{slugify(b["name"])}/">{esc(b["name"])}</a>, '
                         f'à {round(dist(b))} km, mesure actuelle {fr(b["latest"]["hs"])} m.</p>')
    except Exception:
        buoy_line = ""
    from . import zones as _z
    zn = next((z for z in _z.ZONES if z["key"] == sp["region"]), None)
    zone_link = f'<p class="muted" style="margin-top:18px"><a href="../../{zn["slug"]}/">Météo surf {esc(zn["name"])} : tous les spots {zn["in"]}</a></p>' if zn else ""
    hh = sp.get("hours") or {}
    hours_html = ""
    if hh.get("rows"):
        hd = datetime.strptime(hh["day"], "%Y-%m-%d")
        lab = "aujourd'hui" if hh["day"] == now.strftime("%Y-%m-%d") else "demain"
        ws = lambda r: WIND_WORD.get(wind_for_spot(r["w"], r["wd"], sp.get("ori")), "—")
        hrs = "".join(f"<tr><td>{r['h']} h</td><td>{fr(r['hs'])} m</td><td>{fr(r['tp'], 0)} s {sector(r['dir']) or ''}</td>"
                      f"<td>{fr(r['w'], 0)} km/h {sector(r['wd']) or ''}{(' · rafales ' + fr(r['gust'], 0)) if r.get('gust') is not None else ''}</td><td>{ws(r)}</td></tr>" for r in hh["rows"])
        hours_html = (f'<h2>Heure par heure {lab} ({DAYS[hd.weekday()]} {hd:%d/%m})</h2>'
                      f'<table><thead><tr><th>Heure</th><th>Houle</th><th>Période</th><th>Vent</th><th>Pour ce spot</th></tr></thead><tbody>{hrs}</tbody></table>'
                      f'<p class="muted">Toutes les 3 heures. « Pour ce spot » : le vent rapporté à l’orientation de {esc(name)} (face au {sector(sp["ori"]) if sp.get("ori") is not None else "large"}). Le détail heure par heure, les modèles et la bouée : <a href="{app}">prévision complète</a>.</p>')
    td = sp.get("tides") or {}
    tides_html = ""
    if td.get("rows"):
        trw = "".join(f"<tr><td>{r['label']} {r['dm']}</td><td>{' · '.join(r['pm']) or '—'}</td><td>{' · '.join(r['bm']) or '—'}</td><td>{r['coef'] or '—'}</td></tr>" for r in td["rows"])
        tides_html = (f'<h2>Marées à {esc(name)}</h2>'
                      f'<table><thead><tr><th>Jour</th><th>Pleine mer</th><th>Basse mer</th><th>Coef.</th></tr></thead><tbody>{trw}</tbody></table>'
                      f'<p class="muted">Horaires indicatifs calculés pour {esc(td["port"]) if td.get("port") else "le port de référence"} (port de référence du spot).</p>')
    body = f"""<h1>Prévisions surf à {esc(full)}</h1>
<p class="lead">{lead}</p>
<p><a class="cta" href="{app}">Voir les prévisions heure par heure</a></p>
<p class="muted">{(esc(sp['type']) + ' · fond de ' + esc(sp['bottom'].lower()) + ' · ') if sp.get('type') and sp.get('bottom') else ''}{esc(sp['commune'])}, {esc(sp['region'])}. Mis à jour le {now:%d/%m/%Y à %Hh%M}.</p>
{buoy_line}<h2>La semaine à {esc(name)}</h2>
<table><thead><tr><th>Jour</th><th>Houle</th><th>Période</th><th>Vent</th><th>Coef.</th></tr></thead><tbody>{trs}</tbody></table>
{hours_html}{tides_html}
{profile_html(sp, t)}
<h2>Autres spots autour de {esc(name)}</h2><ul class="near">{nl}</ul>
{zone_link}"""
    ld = [
        {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "url": canonical, "inLanguage": "fr",
         "isPartOf": {"@type": "WebSite", "name": BRAND, "url": site + "/"},
         "about": {"@type": "Place", "name": f"{name} (spot de surf)", "geo": {"@type": "GeoCoordinates", "latitude": sp["lat"], "longitude": sp["lon"]},
                   "address": {"@type": "PostalAddress", "addressLocality": sp["commune"], "addressRegion": sp["region"], "addressCountry": country_of(sp["region"])}},
         "dateModified": now.strftime("%Y-%m-%dT%H:%M:00")},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
            {"@type": "ListItem", "position": 2, "name": "Spots de surf", "item": site + "/spots/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical}]},
    ]
    return page(site, title, desc, canonical, body, ld, og_image=og_image)


def index_page(site, spots_meta, now):
    esc = html.escape
    from . import zones as _z

    def _zl(r):
        z = next((z for z in _z.ZONES if z["key"] == r), None)
        return f'<p class="muted"><a href="../{z["slug"]}/">Météo surf {esc(z["name"])}, vue d’ensemble</a></p>' if z else ""

    order, groups = [], {}
    for s in spots_meta:
        if s["region"] not in groups:
            order.append(s["region"])
        groups.setdefault(s["region"], []).append(s)
    order.sort(key=lambda r: -max(x["lat"] for x in groups[r]))   # du nord au sud
    sec = "".join(
        f'<div class="grp"><h2>{esc(r)}</h2>{_zl(r)}<ul class="near">' + "".join(
            f'<li><a href="{s["slug"]}/">{esc(s["name"])}<small>{esc(s["commune"])}</small></a></li>' for s in groups[r]) + "</ul></div>"
        for r in order)
    title = fit(f"Spots de surf de {order[0]} à {order[-1]} : houle, vent, marée | {BRAND}",
                f"Spots de surf, de la Bretagne au Portugal | {BRAND}", f"Tous les spots de surf | {BRAND}")
    desc = fit_desc(f"Prévisions surf pour {len(spots_meta)} spots de la côte Atlantique, de {order[0]} au {order[-1]} : houle, vent, marées et coefficients, mises à jour toutes les heures.",
                    f"Prévisions surf pour {len(spots_meta)} spots, de la Bretagne au Portugal : houle, vent, marées et coefficients, mises à jour toutes les heures.")
    body = f'<h1>Spots de surf, de la Bretagne au Portugal</h1><p class="lead">{len(spots_meta)} spots, de la Bretagne au Portugal. Choisis ton spot pour voir la houle, le vent, la marée et le coefficient.</p>{sec}'
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": f"{site}/spots/", "inLanguage": "fr"},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
              {"@type": "ListItem", "position": 2, "name": "Spots de surf", "item": f"{site}/spots/"}]}]
    return page(site, title, desc, f"{site}/spots/", body, ld, base="../")


def generate(payload, out_dir=None, site=None):
    """Écrit web/spots/…, web/sitemap.xml et web/robots.txt. Retourne le nombre de pages créées."""
    site = (site or config.SITE_URL).rstrip("/")
    root = out_dir or (config.ROOT / "web")
    now = datetime.now()
    meta = {s["name"]: s for s in json.loads(config.SPOTS_FILE.read_text(encoding="utf-8"))}
    coef = payload.get("tide_coef") or {}
    spots = []
    for sp in payload["spots"]:
        m = meta.get(sp["name"])
        if not m:
            continue
        spots.append({**m, "slug": slugify(m["name"]), "rows": day_rows(sp, coef), "hours": hourly(sp, now), "tides": tide_days(sp, coef)})
    base = root / "spots"
    if base.exists():
        shutil.rmtree(base)
    if (root / "og").exists():
        shutil.rmtree(root / "og")
    base.mkdir(parents=True)
    (base / "index.html").write_text(index_page(site, spots, now), encoding="utf-8")
    for sp in spots:
        d = base / sp["slug"]
        d.mkdir()
        og = None
        if sp["rows"]:
            from . import share
            og = share.spot_image(root, sp, sp["rows"][0], now)
        (d / "index.html").write_text(spot_page(site, sp, spots, payload, now, og_image=og), encoding="utf-8")
    from . import pages
    for spec in pages.ALL:
        d = root / spec["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(pages.render(site, spec), encoding="utf-8")
    try:
        from . import bouees
        burls = bouees.generate(payload, root, site, now)
    except Exception as e:  # jamais bloquant : les pages de spots restent publiées
        print(f"  pages bouées non générées : {e}")
        burls = []
    try:
        from . import zones
        zurls = zones.generate(spots, payload, root, site, now)
    except Exception as e:  # jamais bloquant
        print(f"  pages par zone non générées : {e}")
        zurls = []
    day = now.strftime("%Y-%m-%d")
    urls = [(f"{site}/", "hourly", "1.0"), (f"{site}/spots/", "daily", "0.8")] + [(u, "hourly", "0.9") for u in zurls] + [(f"{site}/{c['slug']}/", "monthly", "0.5") for c in pages.ALL] + [(u, "hourly", "0.7") for u in burls] + [(f"{site}/spots/{s['slug']}/", "hourly", "0.7") for s in spots]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"<url><loc>{u}</loc><lastmod>{day}</lastmod><changefreq>{f}</changefreq><priority>{p}</priority></url>\n" for u, f, p in urls) + "</urlset>\n"
    (root / "sitemap.xml").write_text(sm, encoding="utf-8")
    (root / "robots.txt").write_text(ROBOTS.format(site=site), encoding="utf-8")
    (root / "llms.txt").write_text(llms_txt(site, spots), encoding="utf-8")
    return len(spots) + 1 + len(pages.ALL) + len(burls) + len(zurls)


# Robots : tout le monde est autorisé. Les moteurs de recherche des IA sont nommés explicitement (pour être cités dans
# leurs réponses) ; les robots qui collectent pour entraîner les IA restent autorisés par la règle générale (choix à revoir
# avec l'utilisateur : il suffit d'ajouter un groupe « Disallow: / » pour GPTBot, ClaudeBot, Google-Extended, CCBot).
ROBOTS = """User-agent: *
Allow: /

# Moteurs de recherche des IA (réponses avec citations)
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
User-agent: Perplexity-User
Allow: /

Sitemap: {site}/sitemap.xml
"""


def llms_txt(site, spots):
    """llms.txt : un résumé du site et ses pages principales, pour les assistants IA (format llmstxt.org)."""
    from . import zones as _z
    regions = "\n".join(f"- [Météo surf {z['name']}]({site}/{z['slug']}/)" for z in _z.ZONES)
    return f"""# {BRAND}

> Prévisions surf gratuites pour {len(spots)} spots de la côte atlantique, de la Bretagne au Portugal : houle (hauteur, période,
> direction), vent, marée et coefficient, croisées entre plusieurs modèles et comparées en direct aux mesures des bouées en mer.
> Mises à jour toutes les heures. La hauteur affichée est celle de la houle au large, pas la taille des vagues au bord.

## Pages principales
- [Carte de la côte et prévisions]({site}/)
- [Tous les spots, par région]({site}/spots/)
- [Bouées de houle en direct]({site}/bouees/)
- [Comment {BRAND} calcule ses prévisions]({site}/comment-ca-marche/)
- [À propos]({site}/a-propos/)

## Régions
{regions}

## Données
- Prévisions : Open-Meteo (Météo-France, DWD, ECMWF, NOAA), modèle côtier Ifremer MARC
- Mesures : bouées Météo-France, Cerema (CANDHIS), Puertos del Estado, Euskalmet (via Copernicus Marine)
- Les prévisions sont des estimations : à confirmer sur place.
"""
