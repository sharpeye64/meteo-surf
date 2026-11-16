"""Données allégées pour l'application mobile (Expo), tirées du même calcul que le site.

forecast.json fait ~6,5 Mo : trop lourd sur un réseau mobile. On écrit :
  web/data/app/index.json         : la liste des spots (nom, région, position, orientation) + un résumé « maintenant »
                                    (houle, période, direction, vent) et les dernières mesures des bouées.   ~60 Ko
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
    meta = {"v": VERSION, "generated": payload["meta"]["generated"], "spots": index, "buoys": _buoys(payload)}
    (tmp / "index.json").write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if APP_DIR.exists():
        shutil.rmtree(APP_DIR)
    tmp.rename(APP_DIR)
    return len(index)
