"""Pages par zone : « Météo surf Landes », « Météo surf Gironde », « Météo surf Pays basque ».

Visent les recherches larges. Tout vient des données déjà calculées : prévisions du jour et de la semaine des spots de la zone,
bouées proches, caractéristiques des spots (pipeline/spots.json). Rien n'est inventé.
"""
import html
import json
import statistics
from datetime import datetime

from .seo import BRAND, fr, hav, page, sector, slugify

ZONES = [
    {"key": "Gironde", "slug": "meteo-surf-gironde", "name": "Gironde", "in": "en Gironde"},
    {"key": "Landes", "slug": "meteo-surf-landes", "name": "Landes", "in": "dans les Landes"},
    {"key": "Pays Basque", "slug": "meteo-surf-pays-basque", "name": "Pays basque", "in": "au Pays basque"},
]

EXTRA_CSS = """
table.z{width:100%;border-collapse:collapse;font-size:15px}
table.z th{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px 10px;font-weight:700}
table.z td{padding:10px;border-top:1px solid rgba(255,255,255,.08);vertical-align:top}
table.z td small{display:block;color:var(--muted);font-size:12px}
table.z a{color:var(--text);font-weight:600;text-decoration:none}table.z a:hover{text-decoration:underline}
.zw{overflow-x:auto;background:var(--card);border-radius:18px;padding:6px 8px}
.zk{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:18px 0 6px}
.zk div{background:var(--card);border-radius:14px;padding:12px 14px}.zk b{display:block;font-size:24px;font-weight:800;letter-spacing:-.02em}
.zk span{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700}
"""


def _med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def _zone_pages(zone, spots, payload, now, site):
    esc = html.escape
    zs = sorted((s for s in spots if s["region"] == zone["key"]), key=lambda s: -s["lat"])   # du nord au sud
    if not zs:
        return None
    first = [s["rows"][0] for s in zs if s.get("rows")]
    n = len(zs)
    communes = []
    for s in zs:
        if s["commune"] not in communes:
            communes.append(s["commune"])
    name, where = zone["name"], zone["in"]
    base = "../"
    # lecture du jour
    hs = [r["hs"] for r in first if r.get("hs") is not None]
    lead = ""
    if hs:
        tp = _med([r["tp"] for r in first])
        wd = _med([r["wind"] for r in first])
        lead = (f"Aujourd'hui {where}, la houle prévue va de <b>{fr(min(hs))} m</b> à <b>{fr(max(hs))} m</b> selon le spot "
                f"(médiane {fr(_med(hs))} m), avec une période autour de {fr(tp, 0)} s et un vent médian de {fr(wd, 0)} km/h. "
                f"{n} spots suivis, de {esc(communes[0])} à {esc(communes[-1])}.")
    # tableau du jour
    trs = ""
    for s in zs:
        r = s["rows"][0] if s.get("rows") else None
        if not r:
            continue
        trs += (f'<tr><td><a href="{base}spots/{s["slug"]}/">{esc(s["name"])}</a>{"" if s["commune"] == s["name"] else "<small>" + esc(s["commune"]) + "</small>"}</td>'
                f'<td>{fr(r["hs"])} m</td><td>{fr(r["tp"], 0)} s {sector(r["dir"]) or ""}</td><td>{fr(r["wind"], 0)} km/h {sector(r["wdir"]) or ""}</td></tr>')
    table_now = ('<div class="zw"><table class="z"><thead><tr><th>Spot</th><th>Houle</th><th>Période</th><th>Vent</th></tr></thead><tbody>'
                 + trs + "</tbody></table></div>")
    # la semaine : médiane et écart entre spots, jour par jour
    by_day = {}
    for s in zs:
        for r in s.get("rows") or []:
            by_day.setdefault(r["date"], {"label": r["label"], "dm": r["dm"], "hs": [], "tp": [], "wind": []})
            for k in ("hs", "tp", "wind"):
                by_day[r["date"]][k].append(r[k])
    wk = ""
    for date in sorted(by_day):
        d = by_day[date]
        h = [x for x in d["hs"] if x is not None]
        if not h:
            continue
        wk += (f'<tr><td>{d["label"]} {d["dm"]}</td><td>{fr(_med(h))} m</td><td>{fr(min(h))} à {fr(max(h))} m</td>'
               f'<td>{fr(_med(d["tp"]), 0)} s</td><td>{fr(_med(d["wind"]), 0)} km/h</td></tr>')
    table_wk = ('<div class="zw"><table class="z"><thead><tr><th>Jour</th><th>Houle médiane</th><th>Entre spots</th><th>Période</th><th>Vent</th></tr></thead><tbody>'
                + wk + "</tbody></table></div>")
    # bouées proches du centre de la zone
    ctr = {"lat": sum(s["lat"] for s in zs) / n, "lon": sum(s["lon"] for s in zs) / n}
    bl = ""
    try:
        bs = []
        for b in (payload.get("coast") or []) + (payload.get("offshore") or []):
            L = b.get("latest") or {}
            if L.get("hs") is None:
                continue
            km = hav(ctr, {"lat": float(b["lat"]), "lon": float(b["lon"])})
            if km <= 90:
                bs.append((km, b))
        bs.sort(key=lambda x: x[0])
        if bs:
            bl = ("<h2>Mesures en mer</h2><ul class=\"near\">" + "".join(
                f'<li><a href="{base}bouees/{slugify(b["name"])}/">Bouée {esc(b["name"])}<small>{fr(b["latest"]["hs"])} m · {round(km)} km du centre de la zone</small></a></li>' for km, b in bs[:4]) + "</ul>")
    except Exception:
        bl = ""
    # profil de la zone, tiré des fiches de spots
    beach = sum(1 for s in zs if s["type"].lower().startswith("beach"))
    reef = sum(1 for s in zs if "reef" in s["type"].lower() or "récif" in s["bottom"].lower() or "point" in s["type"].lower())
    easy = sum(1 for s in zs if s["level"] in ("Tous", "Débutant", "Débutant / longboard", "Débutant → intermédiaire"))
    exp = sum(1 for s in zs if s["level"] in ("Expert", "Big wave / tow-in"))
    prof = (f"{where[0].upper() + where[1:]}, Houlalah suit <b>{n} spots</b> : {beach} beach breaks"
            + (f" et {reef} spot{'s' if reef > 1 else ''} de reef ou de roche" if reef else "")
            + f". {easy} {'est accessible' if easy == 1 else 'sont accessibles'} aux débutants ou à tous les niveaux"
            + (f", {exp} {'est réservé' if exp == 1 else 'sont réservés'} aux surfeurs très expérimentés" if exp else "") + ". "
            "La houle vient surtout de l'ouest au nord-ouest ; le vent de terre (qui lisse les vagues) dépend de l'orientation de chaque plage, indiquée sur la fiche du spot.")
    others = [z for z in ZONES if z["slug"] != zone["slug"]]
    ol = "".join(f'<li><a href="../{z["slug"]}/">Météo surf {z["name"]}<small>{sum(1 for s in spots if s["region"] == z["key"])} spots</small></a></li>' for z in others)
    title = f"Météo surf {name} : {n} spots, houle, vent et marée | {BRAND}"
    desc = (f"Météo surf {where} : houle, vent et marée de {communes[0]} à {communes[-1]}. {n} spots, prévisions sur 7 jours "
            f"et mesures des bouées, mises à jour toutes les 3 heures.")
    canonical = f"{site}/{zone['slug']}/"
    body = f"""<p class="crumb"><a href="{base}">{BRAND}</a> › <b>Météo surf {esc(name)}</b></p>
<h1>Météo surf {esc(name)}</h1>
<p class="lead">{lead}</p>
<p><a class="cta" href="{base}">Ouvrir la carte et les prévisions heure par heure</a></p>
<h2>Les conditions du jour, spot par spot</h2>{table_now}
<h2>La semaine {esc(where)}</h2>{table_wk}
{bl}
<h2>Les spots {esc(where)}</h2><p>{prof}</p>
<h2>Autres zones</h2><ul class="near">{ol}<li><a href="{base}spots/">Tous les spots<small>{len(spots)} spots, de Lacanau à Hendaye</small></a></li></ul>
<p class="muted" style="margin-top:22px">Mis à jour le {now:%d/%m/%Y à %Hh%M}. Prévisions indicatives, à confirmer sur place.</p>"""
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": canonical, "inLanguage": "fr",
           "isPartOf": {"@type": "WebSite", "name": BRAND, "url": site + "/"}, "dateModified": now.strftime("%Y-%m-%dT%H:%M:00")},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
              {"@type": "ListItem", "position": 2, "name": f"Météo surf {name}", "item": canonical}]}]
    return page(site, title, desc, canonical, body, ld, base=base, extra_css=EXTRA_CSS, top=("Tous les spots", "spots/"))


def generate(spots, payload, root, site, now=None):
    """Écrit root/<slug>/index.html pour chaque zone. Retourne la liste des adresses créées."""
    import shutil
    now = now or datetime.now()
    urls = []
    for z in ZONES:
        html_ = _zone_pages(z, spots, payload, now, site)
        if not html_:
            continue
        d = root / z["slug"]
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        (d / "index.html").write_text(html_, encoding="utf-8")
        urls.append(f"{site}/{z['slug']}/")
    return urls
