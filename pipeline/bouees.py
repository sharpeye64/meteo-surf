"""Pages statiques des bouées : /bouees/ (liste) et /bouees/<bouée>/ (une page par bouée avec mesures réelles).

Chaque page contient du vrai texte (relevé actuel, tableau des relevés des 48 dernières heures, spots voisins) : les moteurs de
recherche la lisent directement. La carte est ajoutée côté navigateur (MapLibre, chargée seulement quand elle devient visible).
Régénérées à chaque passage du robot, avec les dernières mesures. Aucune valeur n'est inventée : tout vient de forecast.json.
"""
import html
import json
import math
from datetime import datetime

from . import config, timefmt
from .seotext import fit, fit_desc
from .seo import BRAND, fr, hav, page, sector, slugify

esc = html.escape
DAYS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]

EXTRA_CSS = """
.stale{margin:14px 0 6px;padding:13px 16px;border-radius:14px;background:#FBF1E4;box-shadow:inset 0 0 0 1px rgba(176,86,58,.25);color:#5A3A22;font-size:15px}.stale b{color:#8A3A1F}.stale a{color:#5A3A22;font-weight:700}
.src{font-size:13px}.live.off{color:#8A867C}
.sg{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}@media(max-width:760px){.sg{grid-template-columns:1fr 1fr}}
.sg b{display:block;font-size:26px;font-weight:800;letter-spacing:-.02em;margin:4px 0 2px}.sg b i{font-size:.55em;font-style:normal;opacity:.6;font-weight:600}.sg small{display:block;font-size:12px;color:var(--muted)}.sg .k{color:var(--muted)}
.dbars{margin-top:20px}.dbars svg{display:block;width:100%;height:84px;margin-top:8px}.dax{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-top:4px}
.crumb{font-size:13px;color:var(--muted);margin:0 0 12px}.crumb a{color:var(--muted)}.crumb b{color:var(--text);font-weight:600}
.live{display:inline-flex;gap:8px;align-items:center;font-size:12px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#7a5a1c;margin-bottom:8px}
.live:before{content:"";width:8px;height:8px;border-radius:50%;background:none;box-shadow:inset 0 0 0 1.5px currentColor;opacity:.8}.live.on:before{background:#1f9d55;opacity:1;box-shadow:0 0 0 0 rgba(31,157,85,.5);animation:lv 2.2s ease-out infinite}@keyframes lv{70%{box-shadow:0 0 0 8px rgba(31,157,85,0)}100%{box-shadow:0 0 0 0 rgba(31,157,85,0)}}@media (prefers-reduced-motion:reduce){.live:before{animation:none}}
.bh{display:grid;grid-template-columns:1.25fr 1fr;gap:14px;margin:22px 0 0}
@media(max-width:760px){.bh{grid-template-columns:1fr}}
.mapbox{position:relative;border-radius:24px;overflow:hidden;min-height:400px;border:1px solid var(--edge);background:#EFE9DC}
@media(max-width:760px){.mapbox{min-height:300px}}
#bmap{position:absolute;inset:0}#bmap .maplibregl-canvas{filter:none}
.cur{background:radial-gradient(500px 240px at 100% 0%,rgba(217,164,65,.22),transparent 68%),#0B1B26;color:#F3EFE6;border-radius:24px;padding:24px 26px;display:flex;flex-direction:column;gap:16px;box-shadow:0 30px 60px -40px rgba(11,27,38,.6)}.cur .big{color:#F2C66B}.cur .live{color:#E6B95E}
.k{font-size:11px;letter-spacing:.1em;text-transform:uppercase;font-weight:800}.cur .k{color:#E6B95E}
.big{font-size:clamp(60px,9vw,88px);font-weight:800;line-height:.95;letter-spacing:-.04em}.big small{font-size:.3em;font-weight:600;letter-spacing:0;opacity:.7}
.cur .when{font-size:13px;font-weight:600;opacity:.8}
.cg{display:grid;grid-template-columns:1fr 1fr;gap:10px}.cg div{background:rgba(243,239,230,.06);box-shadow:inset 0 0 0 1px rgba(243,239,230,.1);border-radius:14px;padding:11px 14px}
.cg b{display:flex;gap:8px;align-items:center;font-size:23px;line-height:1.15}.cg b i{font-size:.55em;font-style:normal;opacity:.7;font-weight:600}
.bcard{background:var(--card);border-radius:22px;padding:18px 20px;box-shadow:0 0 0 1px var(--edge)}
.chart{width:100%;height:auto;display:block}.leg{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-top:6px}
.leg i{display:inline-block;width:18px;height:3px;border-radius:2px;margin-right:7px;vertical-align:middle}
.tw{overflow-x:auto}table.rel td{white-space:nowrap}table.rel{background:none;border-radius:0}
table.rel td.h{font-size:17px;font-weight:800}tr.now td{background:rgba(227,194,131,.22);font-weight:700}tr.now td:first-child{border-left:3px solid var(--sand)}
.tr{font-size:11px;margin-left:6px}.tr.u{color:#c4691a}.tr.d{color:#2b8aa8}
details.more summary{list-style:none;cursor:pointer;text-align:center;margin-top:8px;padding:12px;border:1px solid rgba(16,32,44,.18);border-radius:14px;font-weight:700;font-size:14px}
details.more summary::-webkit-details-marker{display:none}details.more[open] summary{margin-bottom:6px}
.chips{display:flex;gap:8px;flex-wrap:wrap;list-style:none;padding:0;margin:0}
.chips a{display:flex;align-items:center;gap:9px;background:var(--card);border-radius:14px;padding:10px 14px;text-decoration:none;color:var(--text);font-size:14px}
.chips small{color:var(--muted)}.chips .v{font-weight:800;margin-left:4px}.dot{width:10px;height:10px;border-radius:50%;flex:none}
.pt{width:15px;height:15px;border-radius:50%;border:2px solid #fff;box-shadow:0 2px 8px rgba(16,32,44,.35);cursor:pointer}
.bu{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#f6e6bf,#e0bd7a);color:#2a2112;display:grid;place-items:center;border:2px solid #fff;box-shadow:0 4px 14px rgba(16,32,44,.35)}
.lbl{font:700 12px system-ui;background:#fff;color:#10202c;border:1px solid var(--edge);box-shadow:0 2px 8px rgba(16,32,44,.2);border-radius:10px;padding:3px 8px;white-space:nowrap;margin-top:46px}
.maplibregl-popup-content{background:#fff;color:#10202c;border:1px solid var(--edge);box-shadow:0 6px 20px rgba(16,32,44,.2);border-radius:14px;padding:10px 14px;font:600 13px system-ui}.maplibregl-popup-tip{display:none}
.bznav{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 8px}.bznav a{background:var(--card);border-radius:999px;padding:7px 14px;text-decoration:none;color:var(--text);font-weight:700;font-size:14px}.bznav small{color:var(--muted);font-weight:600;margin-left:3px}
.bz{margin:30px 0 12px;scroll-margin-top:16px}.bz small{font-size:14px;font-weight:600;color:var(--muted);margin-left:6px}
.bidx a.mute{opacity:.55}
ul.bidx{padding:0;margin:0}
.bidx{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;list-style:none;padding:0;margin:0}
.bidx a{display:block;background:var(--card);border-radius:20px;padding:16px 18px;text-decoration:none;color:var(--text);box-shadow:0 0 0 1px var(--edge);transition:transform .15s,box-shadow .15s}.bidx a:hover{transform:translateY(-1px);box-shadow:0 0 0 1px rgba(11,27,38,.22)}.bidx .v{font-family:Unbounded,system-ui,sans-serif;letter-spacing:-.04em}
.bidx b{font-size:18px}.bidx small{display:block;color:var(--muted)}.bidx .v{font-size:28px;font-weight:800;margin-top:6px}
"""

MAP_JS = """
(function(){
  var ag=document.getElementById('bage'); if(ag){var t=new Date(ag.getAttribute('data-t')); var h=(Date.now()-t.getTime())/36e5; if(h>=0&&h<24*30) ag.textContent=h<1?"à l'instant":h<36?'il y a '+Math.round(h)+' h':'il y a '+Math.round(h/24)+' j'; var lim=+(ag.getAttribute('data-lim')||1); if(ag.parentNode&&ag.parentNode.classList) ag.parentNode.classList.toggle('on',h>=0&&h<lim); /* si le robot n'a pas tourné depuis : la page se corrige seule (titre, pastille, encadré) */ if(h>=Math.max(6,3*lim)){ document.title=document.title.replace(/ : houle( mesurée)? en direct/,' : dernières mesures'); if(ag.parentNode) ag.parentNode.classList.add('off'); if(!document.querySelector('.stale')){ var d=document.createElement('div'); d.className='stale'; d.innerHTML='<b>Dernière mesure reçue '+ag.textContent+'.</b> Les valeurs ci-dessous peuvent ne plus refléter la mer actuelle.'; var h1=document.querySelector('h1'), nx=h1&&h1.nextElementSibling; if(nx) nx.parentNode.insertBefore(d,nx.nextSibling); } } }
  var el=document.getElementById('bmap'); var raw=document.getElementById('bdata'); if(!el||!raw) return;
  var D=JSON.parse(raw.textContent), started=false;
  function col(h){var S=[[0,'#9ed8f0'],[.6,'#43b8c9'],[1.2,'#6bc46d'],[1.8,'#e8d54a'],[2.4,'#f39a2b'],[3.2,'#e24a3b']];for(var i=S.length-1;i>=0;i--)if(h>=S[i][0])return S[i][1];return S[0][1];}
  function fm(x){return x.toFixed(1).replace('.',',');}
  function start(){
    if(started) return; started=true;
    var l=document.createElement('link'); l.rel='stylesheet'; l.href='https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css'; document.head.appendChild(l);
    var s=document.createElement('script'); s.src='https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.js';
    s.onload=function(){
      var m=new maplibregl.Map({container:'bmap',style:'https://tiles.openfreemap.org/styles/positron',center:[D.b.lon,D.b.lat],zoom:8.6,attributionControl:{compact:true},dragRotate:false});
      m.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
      var b=document.createElement('div'); b.className='bu'; b.setAttribute('aria-hidden','true');
      b.innerHTML='<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 15a7 7 0 0 1 14 0zM12 8V4M3 19c2-1.5 4-1.5 6 0s4 1.5 6 0 4-1.5 6 0"/></svg>';
      new maplibregl.Marker({element:b}).setLngLat([D.b.lon,D.b.lat]).addTo(m);
      var lb=document.createElement('div'); lb.className='lbl'; lb.textContent='Bouée '+D.b.n+' · '+fm(D.b.hs)+' m'; new maplibregl.Marker({element:lb}).setLngLat([D.b.lon,D.b.lat]).addTo(m);
      var mob=window.innerWidth<760, lo=[D.b.lon,D.b.lat], hi=[D.b.lon,D.b.lat];
      D.s.forEach(function(p){lo=[Math.min(lo[0],p.lon),Math.min(lo[1],p.lat)];hi=[Math.max(hi[0],p.lon),Math.max(hi[1],p.lat)];});
      if(D.s.length) m.fitBounds([lo,hi],{padding:mob?50:70,maxZoom:10,duration:0});
      var pop=new maplibregl.Popup({closeButton:false,offset:12});
      D.s.forEach(function(p){var e=document.createElement('div'); e.className='pt'; e.style.background=col(p.h); e.title=p.n;
        e.onclick=function(){pop.setLngLat([p.lon,p.lat]).setHTML('<b>'+p.n+'</b> · '+fm(p.h)+' m prévu<br><a style="color:#8a5f14" href="'+D.base+'?spot='+p.slug+'">Ouvrir la prévision →</a>').addTo(m);};
        new maplibregl.Marker({element:e}).setLngLat([p.lon,p.lat]).addTo(m);});
      m.on('load',function(){m.addSource('l',{type:'geojson',data:{type:'FeatureCollection',features:D.s.map(function(p){return {type:'Feature',geometry:{type:'LineString',coordinates:[[D.b.lon,D.b.lat],[p.lon,p.lat]]}};})}});
        m.addLayer({id:'l',type:'line',source:'l',paint:{'line-color':'#8aa0ab','line-width':1.5,'line-dasharray':[2,3]}});});
    };
    document.head.appendChild(s);
  }
  if('IntersectionObserver' in window){var io=new IntersectionObserver(function(e){if(e[0].isIntersecting){io.disconnect();start();}},{rootMargin:'200px'}); io.observe(el);} else start();
})();
"""


MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def date_fr(t):
    return f"{int(t[8:10])} {MOIS[int(t[5:7]) - 1]}" + ("" if t[:4] == str(datetime.now().year) else f" {t[:4]}")


def stats_html(st):
    """Records et moyennes depuis le début de l'archive. Annonce honnêtement la durée couverte."""
    if not st or st["days"] < 2:
        return ""
    nd = st["days"]
    dur = f"{nd} jours de mesures, depuis le {date_fr(st['since'])}"
    cells = [("Plus grosse houle", f'{fr(st["hs_max"])}<i> m</i>', date_fr(st["hs_max_t"])),
             ("Plus grosse vague", f'{fr(st["hmax_max"])}<i> m</i>' if st.get("hmax_max") is not None else "—", date_fr(st["hmax_max_t"]) if st.get("hmax_max_t") else ""),
             ("Houle moyenne", f'{fr(st["hs_mean"])}<i> m</i>', f'période {fr(st["tp_mean"], 0)} s en moyenne' if st.get("tp_mean") else ""),
             ("Eau", f'{sst_txt(st["sst_mean"])}<i> °C</i>' if st.get("sst_mean") is not None else "—",
              f'de {sst_txt(st["sst_min"])} à {sst_txt(st["sst_max"])} °C' if st.get("sst_min") is not None else "")]
    grid = "".join(f'<div><span class="k">{k}</span><b>{v}</b><small>{esc(n)}</small></div>' for k, v, n in cells)
    daily = st.get("daily") or []
    bars = ""
    if len(daily) >= 3:
        top = max(max(v for _, v in daily), 1.0)
        w = 100.0 / len(daily)
        rects = "".join(f'<rect x="{i * w + w * .12:.2f}" y="{60 - 56 * v / top:.1f}" width="{w * .76:.2f}" height="{56 * v / top:.1f}" rx="1" fill="{spot_color(v)}"><title>{date_fr(d)} : {fr(v)} m</title></rect>' for i, (d, v) in enumerate(daily))
        bars = (f'<div class="dbars"><span class="k">Houle maximale de chaque jour</span><svg viewBox="0 0 100 62" preserveAspectRatio="none" role="img" aria-label="Houle maximale par jour">{rects}</svg>'
                f'<div class="dax"><span>{date_fr(daily[0][0])}</span><span>{date_fr(daily[-1][0])}</span></div></div>')
    return f'<h2>Records et moyennes</h2><div class="bcard"><div class="sg">{grid}</div>{bars}<p class="muted" style="margin:14px 0 0;font-size:13px">{dur}. Les chiffres se précisent à mesure que les mesures s’accumulent.</p></div>'


def sst_txt(x):
    return "—" if x is None else fr(x, 1)


def arrow(d, s=24):
    if d is None:
        return ""
    return (f'<svg width="{s}" height="{s}" viewBox="-13 -13 26 26" aria-hidden="true" style="vertical-align:middle"><circle r="11.5" fill="none" stroke="currentColor" stroke-opacity=".35"/>'
            f'<g style="transform:rotate({(d + 180) % 360:.0f}deg)"><path d="M0 -8V7M-4.5 -3L0 -8L4.5 -3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></g></svg>')


def spot_color(h):
    stops = [(0, "#9ed8f0"), (.6, "#43b8c9"), (1.2, "#6bc46d"), (1.8, "#e8d54a"), (2.4, "#f39a2b"), (3.2, "#e24a3b")]
    c = stops[0][1]
    for v, k in stops:
        if h >= v:
            c = k
    return c


# « de » devant le nom d'un houlographe (H1 : « Bouée houlographe d'Anglet »)
DE = {"Cap Ferret": "du Cap Ferret", "Anglet": "d'Anglet", "Saint-Jean-de-Luz": "de Saint-Jean-de-Luz", "Plateau du Four": "du Plateau du Four",
      "Les Pierres Noires": "des Pierres Noires", "Île de Batz": "de l'Île de Batz", "Belle-Île": "de Belle-Île"}
# exploitants connus (documentés dans pipeline/ibi_buoys.py) ; sinon on ne cite que la source Copernicus Marine
OPERATOR = {"6200024": "Puertos del Estado", "donostia": "Euskalmet"}


def station(b):
    """Ce que l'on sait VRAIMENT de la station : type, identifiant officiel, source, licence, cadence de publication.
    lim = âge (h) jusqu'auquel la mesure est dite « en direct » (cadence + retard de publication de la source)."""
    from . import candhis, ibi_buoys
    bid = str(b["id"])
    cs = next((x for x in candhis.STATIONS if x["id"] == bid), None)
    if cs:
        return {"kind": "houlographe", "ident": f"CANDHIS {bid}", "source": "Cerema, réseau CANDHIS", "license": "Licence Ouverte Etalab 2.0",
                "url": candhis.URL.format(page=cs["page"]), "cadence": "une mesure toutes les 30 minutes", "lim": 1, "creator": "Cerema (réseau CANDHIS)"}
    if bid == "gascogne":
        return {"kind": "bouée du large", "ident": "Météo-France 62001", "source": "Météo-France", "license": "Licence Ouverte Etalab 2.0",
                "url": None, "cadence": "une mesure par heure", "lim": 2, "creator": "Météo-France"}
    st = next((x for x in ibi_buoys.STATIONS if x["id"] == bid), None)
    code = st["file"].replace("IR_TS_MO_", "") if st else bid
    op = OPERATOR.get(bid)
    return {"kind": "bouée", "ident": f"plateforme Copernicus {code}", "source": (op + ", via " if op else "") + "Copernicus Marine (In Situ)",
            "license": "données Copernicus Marine, libres et gratuites", "url": None, "cadence": "une mesure par heure", "lim": 2,
            "creator": (op + " / " if op else "") + "Copernicus Marine Service"}


def age_h(now, t):
    """Âge d'une mesure : instants exacts (issue #2), l'heure publiée portant son décalage ; `now` naïf = heure de Paris."""
    from . import timefmt
    try:
        return timefmt.age_h(t, now)
    except (ValueError, TypeError):
        return 999


CLOCK_SKEW_H = 0.25   # tolérance d'horloge : une mesure datée jusqu'à 15 min dans le futur vaut « à l'instant »


def fresh_state(now, t, lim=1):
    """Règle commune site / appli / robot (issue #4, docs/regles-communes.md ; site pvFresh, appli rules.freshState) :
    en direct < lim, récente < 3 × lim, ancienne < 48 h, muette au-delà. Mesure datée de plus de 15 min dans le futur :
    heure incohérente, « ancienne » (jamais en direct). Heure illisible : muette."""
    a = age_h(now, t)
    if a == 999:
        return "off"
    if a < -CLOCK_SKEW_H:
        return "old"
    a = max(0.0, a)
    return "live" if a < lim else "recent" if a < 3 * lim else "old" if a < 48 else "off"


def is_fresh(now, t, lim=1):
    """seule une mesure « en direct » (selon la cadence de la station) justifie la pastille verte animée"""
    return fresh_state(now, t, lim) == "live"


def age_txt(now, t):
    h = age_h(now, t)
    if h == 999:
        return ""
    if h < 1:
        return "à l'instant"
    if h < 36:
        return f"il y a {round(h)} h"
    return f"il y a {round(h / 24)} j"


def hour_label(t):
    d = datetime.strptime(t[:16], "%Y-%m-%dT%H:%M")
    return f"{d.hour} h" if d.hour else f"{DAYS[d.weekday()]} 0 h"


def collect(payload):
    """Liste des bouées utilisables (mesure présente), avec leur adresse."""
    out = []
    for b in (payload.get("coast") or []) + (payload.get("offshore") or []):
        L = b.get("latest") or {}
        if L.get("hs") is None:
            continue
        out.append({"id": b["id"], "name": b["name"], "slug": slugify(b["name"]), "sub": b.get("sub") or "sur la côte", "lat": float(b["lat"]),
                    "lon": float(b["lon"]), "L": L, "obs": b.get("obs") or [], "model": b.get("model") or [],
                    "st": (payload.get("buoy_stats") or {}).get(b["id"]), "silent": bool(b.get("silent")), "tz": b.get("tz")})
    g = payload.get("gascogne") or {}
    L = g.get("latest") or {}
    if L.get("hs") is not None:   # bouée du large (Météo-France 62001) : même page que les autres
        out.append({"id": "gascogne", "name": "Gascogne", "slug": "gascogne", "sub": "au large, bouée Météo-France 62001", "lat": float(g["lat"]),
                    "lon": float(g["lon"]), "L": L, "obs": g.get("obs") or [], "model": g.get("model") or [], "st": None, "far": True, "tz": g.get("tz")})
    return out


def spot_forecasts(payload, now):
    """Prévision du moment de chaque spot : {nom: (h, p, byhour)}. Clés = heures ABSOLUES (issue #2, revue PR #17) : un spot
    portugais (heure de Lisbonne) et `now` (heure de Paris) désignent le même instant."""
    from . import timefmt
    key = timefmt.hour_key(now)
    meta = {s["name"]: s for s in json.loads(config.SPOTS_FILE.read_text(encoding="utf-8"))}
    res = []
    for sp in payload["spots"]:
        m, mm = sp["marine"], meta.get(sp["name"])
        if not mm:
            continue
        by = {timefmt.hour_key(t): h for t, h in zip(m["time"], m["wave_height"])}
        h = by.get(key)
        if h is None:
            continue
        res.append({"name": sp["name"], "slug": slugify(sp["name"]), "lat": mm.get("mlat", mm["lat"]), "lon": mm.get("mlon", mm["lon"]), "h": h, "by": by})
    return res


def chart_svg(obs, fc, label):
    n = len(obs)
    if n < 4:
        return '<p class="muted">Pas assez de mesures récentes pour tracer la courbe.</p>'
    W, H, pl, pb, pt, pr = 760, 170, 34, 22, 10, 8
    vals = [o["hs"] for o in obs if o.get("hs") is not None] + [v for v in fc if v is not None]
    mx = max(1.0, math.ceil(max(vals) * 1.15 * 2) / 2)
    X = lambda i: pl + i / (n - 1) * (W - pl - pr)
    Y = lambda v: pt + (1 - v / mx) * (H - pt - pb)
    pm = " ".join(f"{X(i):.1f},{Y(o['hs']):.1f}" for i, o in enumerate(obs) if o.get("hs") is not None)
    pf = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(fc) if v is not None)
    g, v = "", 0.0
    while v <= mx + 1e-9:
        g += f'<line x1="{pl}" x2="{W - pr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="rgba(16,32,44,.1)"/><text x="{pl - 6}" y="{Y(v) + 4:.1f}" text-anchor="end" font-size="11" fill="#5b6b75">{fr(v)}</text>'
        v += 0.5
    ax = ""
    for i, o in enumerate(obs):
        d = datetime.strptime(o["t"][:16], "%Y-%m-%dT%H:%M")
        if d.hour == 0:
            ax += f'<text x="{X(i):.1f}" y="{H - 5}" font-size="11" fill="#5b6b75">{DAYS[d.weekday()]}</text>'
    last = obs[-1]
    fcl = f'<polyline points="{pf}" fill="none" stroke="#3f8fb0" stroke-width="2.2" stroke-dasharray="7 6"/>' if pf else ""
    legend = '<span><i style="background:#c8962f;height:4px"></i>Mesuré par la bouée</span>' + (f'<span><i style="background:#3f8fb0"></i>{esc(label)}</span>' if pf else "")
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Hauteur de vagues mesurée par la bouée sur 48 heures">{g}{ax}{fcl}'
            f'<polyline points="{pm}" fill="none" stroke="#c8962f" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{X(n - 1):.1f}" cy="{Y(last["hs"]):.1f}" r="5.5" fill="#c8962f" stroke="#fff" stroke-width="2"/></svg><div class="leg">{legend}</div>')


def rows_html(obs, upto, skip=0):
    lst = list(reversed(obs))
    out = []
    for i, o in enumerate(lst):
        if i < skip or i >= upto:
            continue
        prev = lst[i + 1] if i + 1 < len(lst) else None
        dd = (o["hs"] - prev["hs"]) if prev and o.get("hs") is not None and prev.get("hs") is not None else 0
        tr = "" if abs(dd) < 0.05 else ('<span class="tr u">▲</span>' if dd > 0 else '<span class="tr d">▼</span>')
        t = o["t"][:16]
        label = f"{t[8:10]}/{t[5:7]} {t[11:16]}"
        lab = ("Dernier relevé · " + label) if i == 0 else label
        out.append(f'<tr class="{"now" if i == 0 else ""}"><td>{lab}</td><td class="h">{fr(o["hs"])} m{tr}</td><td>{fr(o.get("hmax"))} m</td>'
                   f'<td>{fr(o.get("tp"))} s</td><td>{sector(o.get("dir")) or "—"} {arrow(o.get("dir"), 18)}</td><td>{sst_txt(o.get("sst"))} °C</td></tr>')
    return "".join(out)


def buoy_page(site, b, allb, spots, now, og_image=None):
    L, obs, slug = b["L"], b["obs"], b["slug"]
    name = b["name"]
    # prévision de comparaison : modèle au point de la bouée (large) sinon spot le plus proche (à moins de 40 km)
    fc, label = [], ""
    only = config.BUOY_ONLY.get(name)                  # bouée abritée : seulement ses spots
    if only:
        spots = [s for s in spots if s["name"] in only]
    if b["model"]:
        by = {timefmt.hour_key(m["t"]): m["hs"] for m in b["model"] if m.get("hs") is not None}
        fc = [by.get(timefmt.hour_key(o["t"])) for o in obs]
        label = "Prévision de référence au point de la bouée"
    if not any(v is not None for v in fc) and spots:
        s0 = min(spots, key=lambda s: hav(b, s))
        if hav(b, s0) < 40:
            fc = [s0["by"].get(timefmt.hour_key(o["t"])) for o in obs]
            label = f"Prévision au spot {s0['name']} (point différent)"
    near = sorted(((hav(b, s), s) for s in spots), key=lambda x: x[0])
    kept = []   # spots espacés d'au moins 4 km : sinon une zone dense (Anglet) donne 7 points collés
    for k, s in near:
        if k > (400 if b.get("far") else 70) or len(kept) >= 8:
            break
        if all(hav(s, t) >= 4 for _, t in kept):
            kept.append((k, s))
    near = kept
    others = sorted(((hav(b, o), o) for o in allb if o["slug"] != slug), key=lambda x: x[0])
    S = station(b)
    fs = fresh_state(now, L["time"], S["lim"])
    working = fs in ("live", "recent") or age_h(now, L["time"]) < 6      # station qui publie normalement
    houlo = S["kind"] == "houlographe"
    who = f"Bouée houlographe {name}" if houlo else f"Bouée {name}"
    wl = who[0].lower() + who[1:]
    tail = "houle mesurée en direct" if working else "dernières mesures de houle"
    short = "houle en direct" if working else "dernières mesures"
    # sans place : on garde les mots recherchés (« houle en direct ») plutôt que la marque
    title = fit(f"{who} : {tail} | {BRAND}", f"{who} : {short} | {BRAND}", f"{who} : {short}", f"{who} : {tail}", f"{who} | {BRAND}", who)
    when = f"le {L['time'][8:10]}/{L['time'][5:7]} à {int(L['time'][11:13])} h {L['time'][14:16]}".replace(" h 00", " h")
    vals = (f"{fr(L['hs'])} m" + (f", période {fr(L['tp'], 0)} s" if L.get("tp") else "")
            + (f", direction {sector(L['dir'])}" if L.get("dir") is not None else "") + (f", eau {fr(L['sst'])} °C" if L.get("sst") is not None else ""))
    if working:
        desc = fit_desc(f"Hauteur de houle mesurée en direct par la {wl} ({S['ident']}) : {vals}. Historique 48 h, records et spots voisins.",
                        f"Hauteur de houle mesurée par la {wl} ({S['ident']}) : {vals}. Historique, records et spots voisins.",
                        f"Houle mesurée par la {wl} : {vals}. Historique et spots voisins.")
    else:
        desc = fit_desc(f"Dernières mesures de la {wl} ({S['ident']}), {when} : {vals}. Historique, records et bouées voisines à jour.",
                        f"Dernières mesures de la {wl}, {when} : {vals}. Historique et bouées voisines à jour.")
    # Résumé visible et daté : ne jamais présenter une ancienne mesure comme la houle actuelle.
    t_obs = L["time"]   # instant complet, décalage compris (issue #2) ; affichage à l'heure du lieu de la bouée
    date_obs = f"{t_obs[8:10]}/{t_obs[5:7]}/{t_obs[:4]} à {t_obs[11:16]}"
    tzl = timefmt.tz_label(b.get("tz"))
    period = (f" ; période de pic {fr(L['tp'])} s" if L.get("tp") is not None else
              f" ; période moyenne {fr(L['tm'])} s" if L.get("tm") is not None else "")
    direction = f" ; direction {sector(L['dir'])} ({fr(L['dir'], 0)}°)" if L.get("dir") is not None else ""
    status = "Dernière mesure disponible"
    summary = (f'<p class="lead">{esc(status)} pour la station {esc(S["ident"])} : '
               f'<time datetime="{esc(t_obs)}">{esc(date_obs)}</time> ({tzl}), '
               f'hauteur significative {fr(L["hs"])} m{period}{direction}. '
               f'Source : {esc(S["source"])}. Cette valeur décrit la mer à la bouée, pas la hauteur des vagues au bord.</p>')
    canonical = f"{site}/bouees/{slug}/"
    base = "../../"
    chips = "".join(f'<li><a href="{base}spots/{s["slug"]}/"><i class="dot" style="background:{spot_color(s["h"])}"></i><span><b>{esc(s["name"])}</b> <small>{round(k)} km</small></span><span class="v">{fr(s["h"])} m</span></a></li>' for k, s in near)
    ochips = "".join(f'<li><a href="../{o["slug"]}/"><span aria-hidden="true">⚓</span><span><b>{esc(o["name"])}</b> <small>{round(k)} km</small></span><span class="v">{fr(o["L"]["hs"])} m</span></a></li>' for k, o in others)
    cg = (f'<div><span class="k">Vague max</span><b>{fr(L.get("hmax"))}<i> m</i></b></div><div><span class="k">Période</span><b>{fr(L.get("tp"))}<i> s</i></b></div>'
          f'<div><span class="k">Direction</span><b>{sector(L.get("dir")) or "—"} {arrow(L.get("dir"), 26)}</b></div><div><span class="k">Eau</span><b>{sst_txt(L.get("sst"))}<i> °C</i></b></div>')
    head = "".join(f"<th>{h}</th>" for h in (f"Date / heure ({ {timefmt.PARIS: 'Paris', timefmt.MADRID: 'Espagne', timefmt.LISBON: 'Portugal'}.get(b.get('tz') or timefmt.PARIS, 'heure locale')})", "Hauteur", "Max", "Période", "Direction", "Eau"))
    stale = ""
    if not working:
        alt = [(k, o) for k, o in others if fresh_state(now, o["L"]["time"], station(o)["lim"]) in ("live", "recent")][:3]
        al = ", ".join(f'<a href="../{o["slug"]}/">{esc(o["name"])}</a> ({round(k)} km, {fr(o["L"]["hs"])} m)' for k, o in alt)
        stale = (f'<div class="stale"><b>Pas de mesure transmise depuis {when}.</b> Les valeurs ci-dessous sont les dernières reçues.'
                 + (f' Bouées à jour les plus proches : {al}.' if al else '') + '</div>')
    src = (f'<p class="muted src">Source des mesures : {esc(S["source"])}'
           + (f', station <a href="{esc(S["url"])}" rel="noopener" target="_blank">{esc(S["ident"].replace("CANDHIS ", ""))}</a>' if S["url"] else f', {esc(S["ident"])}')
           + f' · {esc(S["license"])} · {esc(S["cadence"])} · mesures en temps réel, non validées.</p>')
    data = {"b": {"n": name, "lat": b["lat"], "lon": b["lon"], "hs": L["hs"]}, "base": base,
            "s": [{"n": s["name"], "slug": s["slug"], "lat": s["lat"], "lon": s["lon"], "h": s["h"]} for k, s in near]}
    body = f"""<p class="crumb"><a href="{base}">{BRAND}</a> › <a href="../">Bouées</a> › <b>{esc(name)}</b></p>
<span class="live{' on' if is_fresh(now, L['time'], S['lim']) else ''}{' off' if not working else ''}">Mesure réelle · <span id="bage" data-lim="{S['lim']}" data-t="{esc(L["time"])}">{esc(age_txt(now, L["time"]))}</span></span>
<h1>{"Bouée houlographe " + esc(DE.get(name, "de " + name)) if houlo else "Bouée " + esc(name)}</h1>
<p class="muted">{("Houlographe du réseau CANDHIS (Cerema) · station " + esc(S["ident"].replace("CANDHIS ", "")) + " · ") if houlo else esc(b["sub"][:1].upper() + b["sub"][1:]) + " · " + esc(S["ident"]) + " · "}{fr(abs(b["lat"]), 2)} °N, {fr(abs(b["lon"]), 2)} °{"O" if b["lon"] < 0 else "E"} · {esc(S["cadence"])}</p>
{stale}
{summary}
<div class="bh"><div class="mapbox"><div id="bmap"></div></div>
<div class="cur"><span class="k">{"Dernière mesure de houle" if working else "Dernière mesure reçue"}</span><div><div class="big">{fr(L["hs"])}<small> m</small></div><div class="when">Hauteur significative des vagues</div></div><div class="cg">{cg}</div></div></div>
<p class="muted"><a href="{base}guide/lire-une-bouee/">Lire la hauteur, la période et la fraîcheur d’un relevé de bouée</a></p>
<h2>Historique de la hauteur de houle (48 h)</h2><div class="bcard">{chart_svg(obs, fc, label)}</div>
<h2>Historique des mesures</h2><div class="bcard tw"><table class="rel"><thead><tr>{head}</tr></thead><tbody>{rows_html(obs, 12)}</tbody></table>
<details class="more"><summary>Afficher les 48 dernières heures</summary><table class="rel"><tbody>{rows_html(obs, len(obs), 12)}</tbody></table></details></div>
{stats_html(b.get("st"))}
<h2>Spots autour de la bouée</h2><ul class="chips">{chips}</ul>
<h2>Bouées voisines</h2><ul class="chips">{ochips}</ul>
<p class="muted" style="margin-top:26px">La bouée mesure la mer à l'endroit où elle est placée, pas la taille des vagues sur un spot précis. Prévisions : voir la page de chaque spot. Pour comprendre la hauteur significative, les modèles et les limites des comparaisons, consulter <a href="../../comment-ca-marche/">la méthode Houlalah</a>.</p>
{src}
<script type="application/json" id="bdata">{json.dumps(data, ensure_ascii=False)}</script><script>{MAP_JS}</script>"""
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "url": canonical, "inLanguage": "fr",
           "isPartOf": {"@type": "WebSite", "name": BRAND, "url": site + "/"},
           "about": {"@type": "Place", "name": f"Bouée {name}", "geo": {"@type": "GeoCoordinates", "latitude": b["lat"], "longitude": b["lon"]}},
           "dateModified": now.strftime("%Y-%m-%dT%H:%M:00")},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
              {"@type": "ListItem", "position": 2, "name": "Bouées", "item": f"{site}/bouees/"},
              {"@type": "ListItem", "position": 3, "name": name, "item": canonical}]},
          {"@context": "https://schema.org", "@type": "Dataset", "name": f"Mesures de houle de la {wl} ({S['ident']})",
           "description": f"Hauteur significative, hauteur maximale, période et direction de la houle, et température de l'eau mesurées par la {wl} ({S['ident']}), {S['cadence']}. Dernières 48 heures.",
           "url": canonical, "isAccessibleForFree": True, "license": "https://www.etalab.gouv.fr/licence-ouverte-open-licence/" if "Etalab" in S["license"] else "https://marine.copernicus.eu/user-corner/service-commitments-and-licence",
           "creator": {"@type": "Organization", "name": S["creator"]},
           "spatialCoverage": {"@type": "Place", "geo": {"@type": "GeoCoordinates", "latitude": b["lat"], "longitude": b["lon"]}},
           "temporalCoverage": (obs[0]["t"][:16] + "/" + obs[-1]["t"][:16]) if obs else L["time"][:16],
           "variableMeasured": ["Hauteur significative des vagues", "Hauteur maximale des vagues", "Période de la houle", "Direction de la houle", "Température de l'eau"],
           "dateModified": now.strftime("%Y-%m-%dT%H:%M:00")}]
    return page(site, title, desc, canonical, body, ld, base=base, extra_css=EXTRA_CSS, og_image=og_image)


# Grandes zones de côte, du nord au sud (même découpage que l'onglet Bouées de l'appli, app/src/BuoyScreens.tsx)
ZONES = [("bretagne", "Bretagne"), ("gascogne", "Golfe de Gascogne"), ("espagne", "Espagne"), ("portugal", "Portugal")]


def zone_of(b):
    lat, lon = float(b["lat"]), float(b["lon"])
    return "portugal" if lat < 42 else "espagne" if lat < 44.5 and lon < -1.8 else "bretagne" if lat > 47 else "gascogne"


def zone_order(key, b):
    lat, lon = float(b["lat"]), float(b["lon"])
    if key == "espagne":   # on suit la côte : de la frontière vers l'ouest, puis la Galice vers le sud
        return -lon if lat >= 43 else 100 - lat
    return -lat


def per_txt(L):
    """Période : pic si mesurée, sinon moyenne (Gascogne, Météo-France) dite comme telle."""
    return f"{fr(L.get('tp'), 0)} s" if L.get("tp") else f"{fr(L.get('tm'), 0)} s moy." if L.get("tm") else ""


def index_page(site, allb, now):
    item = lambda b: (f'<li><a href="{b["slug"]}/"{' class="mute"' if b.get("silent") else ''}><b>{"Houlographe" if station(b)["kind"] == "houlographe" else "Bouée"} {esc(b["name"])}</b><small>{esc(b["sub"])} · {("pas de mesure depuis le " + b["L"]["time"][8:10] + "/" + b["L"]["time"][5:7]) if b.get("silent") else "relevé de " + hour_label(b["L"]["time"])}</small>'
                    f'<div class="v">{fr(b["L"]["hs"])} m<small style="display:inline;font-size:14px;font-weight:500"> · {per_txt(b["L"])} {sector(b["L"].get("dir")) or ""}</small></div></a></li>')
    groups = []
    for key, name in ZONES:
        lst = sorted((b for b in allb if zone_of(b) == key), key=lambda b: zone_order(key, b))
        if lst:
            groups.append((key, name, lst))
    nav = "".join(f'<a href="#{k}">{esc(n)} <small>{len(l)}</small></a>' for k, n, l in groups)
    items = "".join(f'<h2 id="{k}" class="bz">{esc(n)} <small>{len(l)} bouée{"s" if len(l) > 1 else ""}</small></h2>'
                    f'<ul class="bidx">{"".join(item(b) for b in l)}</ul>' for k, n, l in groups)
    title = fit(f"Bouées de houle en direct, de la Bretagne au Portugal | {BRAND}", f"Toutes les bouées de houle en direct | {BRAND}")
    desc = fit_desc(f"Mesures réelles de {len(allb)} bouées, de la Bretagne au Portugal : hauteur des vagues, période, direction et "
                    f"température de l'eau, mises à jour toutes les heures.")
    body = (f'<h1>Les bouées, mesures réelles en mer</h1><p class="lead">{len(allb)} bouées dont les mesures servent de référence aux prévisions des spots. '
            f'Choisis une bouée pour voir son relevé actuel et les dernières heures.</p><nav class="bznav" aria-label="Zones">{nav}</nav>{items}')
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "description": desc, "url": f"{site}/bouees/", "inLanguage": "fr"},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
              {"@type": "ListItem", "position": 2, "name": "Bouées", "item": f"{site}/bouees/"}]}]
    return page(site, title, desc, f"{site}/bouees/", body, ld, base="../", extra_css=EXTRA_CSS)


def generate(payload, root, site, now):
    """Écrit root/bouees/… Retourne la liste des adresses créées (pour le plan du site)."""
    import shutil
    allb = collect(payload)
    if not allb:
        return []
    spots = spot_forecasts(payload, now)
    base = root / "bouees"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    (base / "index.html").write_text(index_page(site, allb, now), encoding="utf-8")
    urls = [f"{site}/bouees/"]
    for b in allb:
        d = base / b["slug"]
        d.mkdir()
        from . import share
        og = share.buoy_image(root, b, now)
        (d / "index.html").write_text(buoy_page(site, b, allb, spots, now, og_image=og), encoding="utf-8")
        urls.append(f"{site}/bouees/{b['slug']}/")
    return urls
