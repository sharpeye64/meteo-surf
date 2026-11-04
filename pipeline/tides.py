"""Marées calculées par la méthode harmonique (comme le Shom), à partir de constantes ajustées
sur les mesures des marégraphes REFMAR. Calcul indépendant, non officiel.
"""
import json

import numpy as np
import pandas as pd
import utide
from utide.utilities import Bunch

from . import config


def _to_bunch(obj):
    if isinstance(obj, dict):
        return Bunch({k: _to_bunch(v) for k, v in obj.items()})
    if isinstance(obj, list) and obj and all(isinstance(x, (int, float)) for x in obj):
        return np.array(obj, dtype=float)
    if isinstance(obj, list) and obj and all(isinstance(x, str) for x in obj):
        return np.array(obj, dtype=object)
    return obj


def load_constants(port):
    f = config.TIDE_CONSTANTS_DIR / f"{port}.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text())
    coef = _to_bunch(data["coef"])
    coef["aux"]["lind"] = np.asarray(coef["aux"]["lind"], dtype=int)
    return data["meta"], coef


def predict(port, start_local, days):
    """Hauteurs horaires (pour la courbe) et pleines/basses mers à la minute, en heure locale."""
    loaded = load_constants(port)
    if not loaded:
        return None
    meta, coef = loaded
    start = pd.Timestamp(start_local).tz_localize(config.TIMEZONE).tz_convert("UTC").tz_localize(None)
    fine = pd.date_range(start - pd.Timedelta("2h"), start + pd.Timedelta(days=days, hours=2), freq="2min")
    h = utide.reconstruct(fine.values, coef, verbose=False).h
    # Affinage parabolique autour de chaque extremum, pour une heure à la minute près.
    extremes = []
    for i in range(1, len(h) - 1):
        if (h[i] > h[i - 1] and h[i] >= h[i + 1]) or (h[i] < h[i - 1] and h[i] <= h[i + 1]):
            a, b, c = h[i - 1], h[i], h[i + 1]
            denom = a - 2 * b + c
            off = 0.5 * (a - c) / denom if denom else 0.0
            t = fine[i] + pd.Timedelta(minutes=2 * off)
            hh = b - 0.25 * (a - c) * off
            tl = t.tz_localize("UTC").tz_convert(config.TIMEZONE).tz_localize(None)
            extremes.append({"t": tl.strftime("%Y-%m-%dT%H:%M"), "type": "PM" if b > a else "BM", "h": round(float(hh), 2)})
    hourly_idx = pd.date_range(pd.Timestamp(start_local), periods=days * 24, freq="h")
    hourly_utc = hourly_idx.tz_localize(config.TIMEZONE, ambiguous="NaT", nonexistent="shift_forward").tz_convert("UTC").tz_localize(None)
    hh = utide.reconstruct(hourly_utc.values, coef, verbose=False).h
    return {"port": port, "label": config.TIDE_PORTS.get(port, port), "source": meta,
            "hourly": [round(float(x), 3) for x in hh],
            "extremes": [e for e in extremes if e["t"] >= hourly_idx[0].strftime("%Y-%m-%dT%H:%M")]}


def shift(tide, minutes):
    """Décalage horaire propre à un spot (à calibrer sur le terrain), appliqué aux pleines/basses mers."""
    if not tide or not minutes:
        return tide
    out = dict(tide)
    out["extremes"] = [{**e, "t": (pd.Timestamp(e["t"]) + pd.Timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M")}
                       for e in tide["extremes"]]
    return out
