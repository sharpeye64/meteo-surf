"""Données allégées pour l'application mobile (Expo), tirées du même calcul que le site.

forecast.json fait ~6,5 Mo : trop lourd sur un réseau mobile. On écrit :
  web/data/app/index.json         : la liste des spots (nom, région, position, orientation) + un résumé « maintenant »
                                    (houle, période, direction, vent) et les dernières mesures des bouées.   ~60 Ko
  web/data/app/bouees/<slug>.json : la fiche d'une bouée : 48 h mesurées, la prévision au même endroit, records, spots autour.
  web/data/app/spots/<slug>.json  : la fiche d'un spot : 7 jours heure par heure (houle mélangée, période, direction,
                                    vent, rafales, direction du vent, hauteur d'eau), marées, soleil, eau.     ~8 Ko
Toujours écrit après forecast.json ; ne bloque jamais la publication.
"""
import json
import re
import shutil
import unicodedata
from datetime import datetime

from . import config

APP_DIR = config.OUTPUT_FILE.parent / "app"
VERSION = 1


def slugify(name):
    s = unicodedata.normalize("NFD", name)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _r(v, nd=1):
    return None if v is None else round(float(v), nd)


def _now_index(times):
    key = datetime.now().strftime("%Y-%m-%dT%H")
    for i, t in enumerate(times):
        if t[:13] >= key:
            return i
    return 0


def _buoys(payload):
    out = []
    g = payload.get("gascogne")
    if g and (g.get("latest") or {}).get("hs") is not None:
        out.append({"id": "gascogne", "name": "Gascogne", "sub": "au large, Météo-France 62001", "lat": g["lat"], "lon": g["lon"],
                    "large": True, **{k: g["latest"].get(k) for k in ("time", "hs", "tp", "dir", "sst")}})
    for kind in ("coast", "offshore"):
        for b in payload.get(kind) or []:
            L = b.get("latest") or {}
            if L.get("hs") is None:
                continue
            out.append({"id": b["id"], "name": b["name"], "sub": b.get("sub") or "sur la côte", "lat": float(b["lat"]), "lon": float(b["lon"]),
                        **{k: L.get(k) for k in ("time", "hs", "tp", "dir", "sst")}})
    return out


def _km(a, b):
    import math
    r = math.pi / 180
    x = (b[1] - a[1]) * r * math.cos((a[0] + b[0]) / 2 * r)
    y = (b[0] - a[0]) * r
    return math.hypot(x, y) * 6371


def _buoy_sheets(spots, payload, out_dir):
    """Une fiche par bouée : 48 h de mesures, la prévision au même endroit (modèle au point de la bouée, sinon le spot
    le plus proche), les records des derniers jours et les spots autour. Retourne le nombre de fiches."""
    by_name = {s["name"]: s for s in payload["spots"]}
    stats = payload.get("buoy_stats") or {}
    raw = []
    g = payload.get("gascogne")
    if g:
        raw.append(("gascogne", "Gascogne", "au large, Météo-France 62001", g))
    for kind in ("coast", "offshore"):
        for b in payload.get(kind) or []:
            raw.append((b["id"], b["name"], b.get("sub") or "sur la côte", b))
    n = 0
    for bid, name, sub, b in raw:
        L = b.get("latest") or {}
        if L.get("hs") is None:
            continue
        pos = (float(b["lat"]), float(b["lon"]))
        only = config.BUOY_ONLY.get(name)                      # bouée abritée : seulement ses spots
        around = sorted(((_km(pos, (s["lat"], s["lon"])), s) for s in spots if not only or s["name"] in only), key=lambda x: x[0])
        model = [{"t": m["t"], "hs": _r(m["hs"], 2)} for m in (b.get("model") or []) if m.get("hs") is not None]
        src = "modèle au point de la bouée"
        if not model and around and around[0][0] < 60:          # bouée côtière : prévision du spot le plus proche
            f = by_name.get(around[0][1]["name"])
            if f:
                model = [{"t": t, "hs": _r(h, 2)} for t, h in zip(f["marine"]["time"], f["marine"]["wave_height"]) if h is not None]
                src = f"prévision du spot {around[0][1]['name']}"
        obs = [{k: o.get(k) for k in ("t", "hs", "tp", "dir", "hmax", "sst")} for o in (b.get("obs") or [])][-48:]
        t_first = obs[0]["t"] if obs else L.get("time")
        model = [m for m in model if t_first and m["t"] >= t_first][:72]
        st = stats.get(bid) or {}
        sheet = {"v": VERSION, "id": bid, "slug": slugify(name), "name": name, "sub": sub, "lat": pos[0], "lon": pos[1],
                 "latest": {k: L.get(k) for k in ("time", "hs", "hmax", "tp", "dir", "sst")}, "obs": obs, "model": model, "model_src": src,
                 "stats": {k: st.get(k) for k in ("since", "days", "hs_max", "hs_max_t", "hs_mean", "sst_mean")} if st else None,
                 "spots": [{"name": s["name"], "slug": slugify(s["name"]), "km": round(k)} for k, s in around[:6] if k < 60]}
        (out_dir / f"{slugify(name)}.json").write_text(json.dumps(sheet, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        n += 1
    return n


def generate(spots, payload):
    """spots : pipeline/spots.json ; payload : le contenu de forecast.json. Retourne le nombre de fiches écrites."""
    tmp = APP_DIR.with_name("app.tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / "spots").mkdir(parents=True)
    by_name = {s["name"]: s for s in payload["spots"]}
    index = []
    for s in spots:
        f = by_name.get(s["name"])
        if not f:
            continue
        slug = slugify(s["name"])
        m, w = f["marine"], f["wind"]
        times = m["time"]
        n = len(times)
        col = lambda arr, nd=1: [_r(x, nd) for x in (arr or [None] * n)[:n]]
        wt = {t: i for i, t in enumerate(w.get("time") or [])}
        wcol = lambda key, nd=0: [_r((w.get(key) or [])[wt[t]], nd) if t in wt and wt[t] < len(w.get(key) or []) else None for t in times]
        sheet = {
            "v": VERSION, "name": s["name"], "slug": slug, "region": s["region"], "commune": s.get("commune"),
            "lat": s["lat"], "lon": s["lon"], "ori": s.get("ori"), "type": s.get("type"), "level": s.get("level"),
            "bottom": s.get("bottom"), "notes": s.get("notes"),
            "t0": times[0] if times else None,
            "hs": col(m.get("wave_height"), 2), "tp": col(m.get("wave_period")), "dir": col(m.get("wave_direction"), 0),
            "sw": col(m.get("swell_wave_height"), 2), "swp": col(m.get("swell_wave_period")),
            "wind": wcol("wind_speed_10m"), "gust": wcol("wind_gusts_10m"), "wdir": wcol("wind_direction_10m"),
            "sea": col(m.get("sea_level_height_msl"), 2), "sst": col(m.get("sea_surface_temperature")),
            "tide": f.get("tide"), "sun": f.get("daily"),
        }
        (tmp / "spots" / f"{slug}.json").write_text(json.dumps(sheet, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        i = _now_index(times)
        index.append({"name": s["name"], "slug": slug, "region": s["region"], "commune": s.get("commune"),
                      "lat": s.get("mlat", s["lat"]), "lon": s.get("mlon", s["lon"]), "ori": s.get("ori"),
                      "now": {"t": times[i] if times else None, "hs": sheet["hs"][i] if n else None, "tp": sheet["tp"][i] if n else None,
                              "dir": sheet["dir"][i] if n else None, "wind": sheet["wind"][i] if n else None, "wdir": sheet["wdir"][i] if n else None}})
    (tmp / "bouees").mkdir()
    _buoy_sheets(spots, payload, tmp / "bouees")
    buoys = _buoys(payload)
    for bu in buoys:
        bu["slug"] = slugify(bu["name"])
    meta = {"v": VERSION, "generated": payload["meta"]["generated"], "spots": index, "buoys": buoys}
    (tmp / "index.json").write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    tmp.rename(APP_DIR)
    return len(index)
