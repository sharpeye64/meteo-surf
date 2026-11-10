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


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


CSS = """:root{--bg:#0A1114;--card:#142128;--text:#F2EFE8;--muted:#AEB6B4;--sand:#E4C79B;--aqua:#8DBFB2}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--sand)}main{max-width:900px;margin:0 auto;padding:24px 20px 60px}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px}
.brand{font-weight:700;text-decoration:none;color:var(--text);letter-spacing:.01em;display:inline-flex;align-items:center;gap:9px}.mk{display:block;width:auto;height:26px}.bw{display:block;width:auto;height:15px}
h1{font-size:clamp(28px,5vw,42px);line-height:1.1;margin:0 0 12px}h2{font-size:20px;margin:34px 0 12px}
.lead{font-size:18px;color:var(--text);margin:0 0 20px}.muted{color:var(--muted);font-size:14px}
.cta{display:inline-block;background:var(--sand);color:#1A1405;font-weight:700;padding:12px 20px;border-radius:999px;text-decoration:none;margin:6px 0 10px}
table{width:100%;border-collapse:collapse;background:var(--card);border-radius:16px;overflow:hidden}
th,td{padding:10px 12px;text-align:left;border-top:1px solid rgba(255,255,255,.08);font-size:15px}thead th{border-top:0;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}
dl.fiche{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:0 0 16px}dl.fiche div{background:var(--card);border-radius:14px;padding:10px 14px}dl.fiche dt{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700}dl.fiche dd{margin:3px 0 0;font-weight:600}
ul.near{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
ul.near a{display:block;background:var(--card);border-radius:14px;padding:12px 14px;text-decoration:none;color:var(--text)}ul.near small{display:block;color:var(--muted)}
.grp{margin-top:26px}.grp h2{color:var(--sand)}footer{margin-top:44px;color:var(--muted);font-size:13px}footer nav{margin-bottom:6px}footer a{color:var(--muted)}
.prose p,.prose li{max-width:68ch}.prose ul{padding-left:20px}"""


def page(site, title, desc, canonical, body, jsonld, base="../../", extra_css="", top=None, og_image=None):
    og = f"{site}/{og_image}" if og_image else f"{site}/og.png"
    top = top or ("Tous les spots", "spots/")
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in jsonld)
    esc = html.escape
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}"><meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND}"><meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{og}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{og}"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}">
<meta name="theme-color" content="#0A1114">
<link rel="icon" href="{base}brand/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="{base}brand/apple-touch-icon.png">
<style>{CSS}{extra_css}</style>{ld}</head><body><main>
<header><a class="brand" href="{base}"><img class="mk" src="{base}brand/symbol.svg" alt="" height="26"><img class="bw" src="{base}brand/wordmark.svg" alt="{BRAND}" height="15"></a><a class="muted" href="{base}{top[1]}">{top[0]}</a></header>
<div class="prose">{body}</div>
<footer><nav aria-label="Informations"><a href="{base}comment-ca-marche/">Comment ça marche</a> · <a href="{base}mentions-legales/">Mentions légales</a> · <a href="{base}confidentialite/">Confidentialité</a></nav><br>Prévisions calculées à partir de plusieurs modèles (Météo-France, DWD, ECMWF, NOAA, Ifremer) via Open-Meteo, corrigées avec les bouées. Estimations : à confirmer sur place. {BRAND} est un prototype non commercial.</footer>
</main></body></html>"""


def _angle(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _low(x):
    return x[:1].lower() + x[1:] if x else x


def profile_html(sp, t):
    """« Le spot en bref » : fiche tirée des champs du spot (orientation, fond, marée, niveau, taille) + lecture des conditions du jour.
    Rien n'est inventé : tout vient de pipeline/spots.json et des prévisions."""
    esc = html.escape
    name, ori = sp["name"], sp.get("ori")
    off_dir = None if ori is None else (ori + 180) % 360
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
    title = f"Prévisions surf {name} : houle, vent et marée | {BRAND}"
    if t:
        desc = (f"Houle de {fr(t['hs'])} m à {name} ({where}) aujourd'hui, période {fr(t['tp'], 0)} s, vent {fr(t['wind'], 0)} km/h"
                f"{' (' + sector(t['wdir']) + ')' if t['wdir'] is not None else ''}. Prévisions 7 jours, marées et coefficients, mises à jour toutes les 3 heures.")
    else:
        desc = f"Prévisions surf à {name} ({where}) : houle, vent, marée et coefficient sur 7 jours."
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
        cb = [b for b in (payload.get("coast") or []) + (payload.get("offshore") or []) if (b.get("latest") or {}).get("hs") is not None]
        if cb:
            b = min(cb, key=lambda x: hav(sp, {"lat": float(x["lat"]), "lon": float(x["lon"])}))
            km = hav(sp, {"lat": float(b["lat"]), "lon": float(b["lon"])})
            if km <= 80:
                buoy_line = (f'<p class="muted">Bouée la plus proche : <a href="../../bouees/{slugify(b["name"])}/">{esc(b["name"])}</a>, '
                             f'à {round(km)} km, mesure actuelle {fr(b["latest"]["hs"])} m.</p>')
    except Exception:
        buoy_line = ""
    body = f"""<h1>Prévisions surf à {esc(name)}</h1>
<p class="lead">{lead}</p>
<p><a class="cta" href="{app}">Voir les prévisions heure par heure</a></p>
<p class="muted">{esc(sp['type'])} · fond de {esc(sp['bottom'].lower())} · {esc(sp['commune'])}, {esc(sp['region'])}. Mis à jour le {now:%d/%m/%Y à %Hh%M}.</p>
{buoy_line}<h2>La semaine à {esc(name)}</h2>
<table><thead><tr><th>Jour</th><th>Houle</th><th>Période</th><th>Vent</th><th>Coef.</th></tr></thead><tbody>{trs}</tbody></table>
{profile_html(sp, t)}
<h2>Autres spots autour de {esc(name)}</h2><ul class="near">{nl}</ul>"""
    ld = [
        {"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "url": canonical, "inLanguage": "fr",
         "isPartOf": {"@type": "WebSite", "name": BRAND, "url": site + "/"},
         "about": {"@type": "Place", "name": f"{name} (spot de surf)", "geo": {"@type": "GeoCoordinates", "latitude": sp["lat"], "longitude": sp["lon"]},
                   "address": {"@type": "PostalAddress", "addressLocality": sp["commune"], "addressRegion": sp["region"], "addressCountry": "FR"}},
         "dateModified": now.strftime("%Y-%m-%dT%H:%M:00")},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
            {"@type": "ListItem", "position": 2, "name": "Spots de surf", "item": site + "/spots/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical}]},
    ]
    return page(site, title, desc, canonical, body, ld, og_image=og_image)


def index_page(site, spots_meta, now):
    esc = html.escape
    order, groups = [], {}
    for s in spots_meta:
        if s["region"] not in groups:
            order.append(s["region"])
        groups.setdefault(s["region"], []).append(s)
    sec = "".join(
        f'<div class="grp"><h2>{esc(r)}</h2><ul class="near">' + "".join(
            f'<li><a href="{s["slug"]}/">{esc(s["name"])}<small>{esc(s["commune"])}</small></a></li>' for s in groups[r]) + "</ul></div>"
        for r in order)
    title = f"Spots de surf de Lacanau à Hendaye : prévisions houle, vent, marée | {BRAND}"
    desc = f"Prévisions surf pour {len(spots_meta)} spots de la côte Atlantique, de la Gironde au Pays basque : houle, vent, marées et coefficients, mises à jour toutes les 3 heures."
    body = f'<h1>Spots de surf, de Lacanau à Hendaye</h1><p class="lead">{len(spots_meta)} spots, de la Gironde au Pays basque. Choisis ton spot pour voir la houle, le vent, la marée et le coefficient.</p>{sec}'
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
        spots.append({**m, "slug": slugify(m["name"]), "rows": day_rows(sp, coef)})
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
    day = now.strftime("%Y-%m-%d")
    urls = [(f"{site}/", "hourly", "1.0"), (f"{site}/spots/", "daily", "0.8")] + [(f"{site}/{c['slug']}/", "monthly", "0.5") for c in pages.ALL] + [(u, "hourly", "0.7") for u in burls] + [(f"{site}/spots/{s['slug']}/", "hourly", "0.7") for s in spots]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
        f"<url><loc>{u}</loc><lastmod>{day}</lastmod><changefreq>{f}</changefreq><priority>{p}</priority></url>\n" for u, f, p in urls) + "</urlset>\n"
    (root / "sitemap.xml").write_text(sm, encoding="utf-8")
    (root / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site}/sitemap.xml\n", encoding="utf-8")
    return len(spots) + 1 + len(pages.ALL) + len(burls)
