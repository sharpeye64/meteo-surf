"""Bouées côtières CANDHIS (Cerema), temps réel, Licence Ouverte Etalab 2.0.

Lecture des pages publiques « données temps réel » (une requête par bouée et par passage).
L'API officielle existe mais demande une clé sur demande ; si on l'obtient, seule `fetch_station` change.
Heures publiées en TU : converties en heure de Paris. Données temps réel non validées.
"""
import math
import re

import pandas as pd
import requests

from . import config

# Positions exactes : fichier officiel « Stations de mesure de Candhis » (Cerema, Licence Ouverte, data.gouv.fr).
STATIONS = [
    {"id": "03302", "name": "Cap Ferret", "lat": 44.6525, "lon": -1.4467, "page": "Y2FtcD0wMzMwMg=="},
    {"id": "06402", "name": "Anglet", "lat": 43.5322, "lon": -1.6150, "page": "Y2FtcD0wNjQwMg=="},
    {"id": "06403", "name": "Saint-Jean-de-Luz", "lat": 43.4083, "lon": -1.6817, "page": "Y2FtcD0wNjQwMw=="},
]
URL = "https://candhis.cerema.fr/_public_/campagne.php?{page}"
UA = {"User-Agent": "meteo-surf-prototype (prévisions surf, 1 requête/bouée toutes les 3 h)"}


def parse_html(html):
    """Retourne un DataFrame [time(Paris), hs, hmax, tp, dir, sst] du plus ancien au plus récent."""
    tbody = html.split("<tbody>", 1)[-1]
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", tbody, flags=re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)]
        if len(cells) < 8 or not re.match(r"\d\d/\d\d/\d{4}", cells[0]):
            continue
        num = lambda x: float(x.replace(",", ".")) if re.match(r"^-?\d+([.,]\d+)?$", x) else None
        t = pd.to_datetime(cells[0] + " " + cells[1], format="%d/%m/%Y %H:%M", utc=True)
        rows.append({"time": t.tz_convert(config.TIMEZONE).tz_localize(None), "hs": num(cells[2]),
                     "hmax": num(cells[3]), "tp": num(cells[4]), "dir": num(cells[5]), "sst": num(cells[8 - 1])})
    df = pd.DataFrame(rows)
    return df.sort_values("time").reset_index(drop=True) if len(df) else df


def circ_mean(vals):
    """Moyenne d'angles en degrés (une direction de 359° et une de 1° donnent 0°, pas 180°)."""
    v = [float(x) for x in vals if x is not None and not pd.isna(x)]
    if not v:
        return None
    sx = sum(math.sin(math.radians(a)) for a in v)
    sy = sum(math.cos(math.radians(a)) for a in v)
    return math.degrees(math.atan2(sx, sy)) % 360


def fetch_station(st):
    r = requests.get(URL.format(page=st["page"]), timeout=40, headers=UA)
    r.raise_for_status()
    df = parse_html(r.text)
    df = df.dropna(subset=["hs"])
    if df.empty:
        raise ValueError("aucune mesure lisible")
    fmt = lambda t: t.strftime("%Y-%m-%dT%H:%M")
    last = df.iloc[-1]
    nz = lambda v, d=1: None if v is None or pd.isna(v) else round(float(v), d)
    d = df.copy()
    d["hour"] = d["time"].dt.floor("h")
    hourly = d.groupby("hour").agg(hs=("hs", "mean"), tp=("tp", "mean"), hmax=("hmax", "max"), sst=("sst", "mean")).reset_index()
    hourly["dir"] = [circ_mean(d.loc[d["hour"] == h, "dir"]) for h in hourly["hour"]]
    return {
        "id": st["id"], "name": st["name"], "lat": st["lat"], "lon": st["lon"],
        "latest": {"time": fmt(last["time"]), "hs": nz(last["hs"], 2), "hmax": nz(last["hmax"]), "tp": nz(last["tp"]),
                   "dir": None if pd.isna(last["dir"]) else round(float(last["dir"])), "sst": nz(last["sst"])},
        "obs": [{"t": fmt(r.hour), "hs": round(float(r.hs), 2), "tp": nz(r.tp), "hmax": nz(r.hmax), "dir": None if r.dir is None else round(r.dir), "sst": nz(r.sst)}
                for r in hourly.itertuples()],
    }


def fetch_all():
    """Toutes les bouées lisibles ; les échecs sont renvoyés à part, sans bloquer les autres.
    Le site du Cerema répond parfois lentement : chaque bouée est retentée une fois."""
    import time
    out, errors = [], {}
    for st in STATIONS:
        for essai in (1, 2):
            try:
                out.append(fetch_station(st))
                errors.pop(st["id"], None)
                break
            except Exception as e:
                errors[st["id"]] = str(e)[:200]
                if essai == 1:
                    time.sleep(4)
    return out, errors
