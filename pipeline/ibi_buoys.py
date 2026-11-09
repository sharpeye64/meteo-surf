"""Bouées du large « fraîches » du produit Copernicus IBI : Bilbao-Vizcaya (Puertos del Estado) et Donostia (Euskalmet).

Même produit que la bouée Gascogne (voir buoy.py), mais ces stations sont livrées toutes les heures, avec ≈ 30 à 45 min de retard
(la Gascogne, elle, n'est livrée qu'une fois par jour, vers 21 h 50 UTC). Fichiers `IR_TS_MO_<nom>_AAAAMMJJ.nc` dans le dossier du jour.
Données Copernicus Marine, gratuites : mention « Puertos del Estado, Euskalmet, via Copernicus Marine ».
"""
import os
import tempfile
import time

import numpy as np
import pandas as pd
import requests

from . import config
from .buoy import _copernicus_series

STATIONS = [
    {"id": "6200024", "file": "IR_TS_MO_6200024", "name": "Bilbao-Vizcaya", "lat": 43.65, "lon": -3.04, "sub": "au large, Espagne"},
    {"id": "donostia", "file": "IR_TS_MO_Donostia-buoy", "name": "Donostia", "lat": 43.57, "lon": -2.01, "sub": "au large, Saint-Sébastien"},
]
VARS = {"hs": ("VHM0", "VAVH", "VGHS"), "tp": ("VTPK",), "dir": ("VMDR", "VPED", "VDIR"), "sst": ("TEMP",), "hmax": ("VZMX", "VEMH")}
UA = {"User-Agent": "meteo-surf-prototype (prévisions surf, 1 requête par bouée toutes les 3 h)"}


def _load_day(st, day):
    cfg = config.GASCOGNE
    url = f"{cfg['copernicus_base']}/{day}/{st['file']}_{day}.nc"
    r = requests.get(url, timeout=60, headers=UA)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    import xarray as xr
    fd, path = tempfile.mkstemp(suffix=".nc")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(r.content)
        with xr.open_dataset(path) as ds:
            out = pd.DataFrame({"time": pd.to_datetime(ds["TIME"].values).tz_localize("UTC")})
            for col, names in VARS.items():
                v = _copernicus_series(ds, names)
                out[col] = np.nan if v is None else v
            if "TIME_QC" in ds:
                out = out[np.isin(ds["TIME_QC"].values, [0, 1, 2])]
        return out
    finally:
        os.remove(path)


def fetch_station(st):
    today = pd.Timestamp.now("UTC").normalize()
    frames = []
    for k in range(3):  # aujourd'hui, hier, avant-hier : de quoi couvrir 48 h
        f = _load_day(st, (today - pd.Timedelta(days=k)).strftime("%Y%m%d"))
        if f is not None:
            frames.append(f)
    if not frames:
        raise ValueError("aucun fichier récent")
    df = pd.concat(frames).drop_duplicates("time", keep="last").sort_values("time")
    df = df.dropna(subset=["hs"])
    df = df[df["hs"].between(0, 25)]
    if df.empty:
        raise ValueError("aucune hauteur valide")
    df = df[df["time"] >= df["time"].max() - pd.Timedelta("48h")]
    df["local"] = df["time"].dt.tz_convert(config.TIMEZONE).dt.tz_localize(None)
    fmt = lambda t: t.strftime("%Y-%m-%dT%H:%M")
    nz = lambda v, d=1: None if v is None or pd.isna(v) else round(float(v), d)
    last = df.iloc[-1]
    win = df[df["time"] >= last["time"] - pd.Timedelta("3h")]
    tp = win["tp"].dropna()
    tp = float(tp.iloc[-1]) if len(tp) else None
    if tp is not None and tp < 2.5:  # période pic incohérente : on préfère ne pas l'afficher
        tp = None
    di = win["dir"].dropna()
    return {
        "id": st["id"], "name": st["name"], "sub": st["sub"], "lat": st["lat"], "lon": st["lon"], "kind": "large",
        "latest": {"time": fmt(last["local"]), "hs": nz(last["hs"], 2), "hmax": nz(last["hmax"]), "tp": nz(tp),
                   "dir": None if not len(di) else round(float(di.iloc[-1])), "sst": nz(last["sst"])},
        "obs": [{"t": fmt(r.local), "hs": round(float(r.hs), 2), "tp": nz(r.tp) if (r.tp is not None and r.tp >= 2.5) else None,
                 "hmax": nz(r.hmax), "dir": None if pd.isna(r.dir) else round(float(r.dir)), "sst": nz(r.sst)}
                for r in df.itertuples()],
    }


def fetch_all():
    """Bouées lisibles ; les échecs sont renvoyés à part (une relance par bouée), sans bloquer les autres."""
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
