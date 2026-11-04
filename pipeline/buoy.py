"""Bouée Gascogne (62001) : mesures au large, comparaison au modèle et temps de trajet vers la côte.

Une bouée mesure l'état de mer global (houle + mer du vent) à un point donné :
- WVHT : hauteur significative (comparable au wave_height des modèles) ;
- DPD : période dominante (pic), comparable à la période pic du modèle, pas à une période moyenne ;
- MWD : direction moyenne d'où viennent les vagues (souvent absente sur cette bouée).
Les données temps réel ne sont pas validées : on filtre les valeurs aberrantes.
"""
import io
import math

import numpy as np
import pandas as pd
import requests

from . import config, openmeteo

G = 9.81


def parse_ndbc(text):
    lines = [l for l in text.splitlines() if l.strip()]
    header = lines[0].lstrip("#").split()
    rows = [l.split() for l in lines if not l.startswith("#")]
    df = pd.DataFrame(rows, columns=header[:len(rows[0])])
    df.iloc[:, 5:] = df.iloc[:, 5:].replace("MM", np.nan)
    df["time"] = pd.to_datetime(dict(year=df.iloc[:, 0], month=df.iloc[:, 1], day=df.iloc[:, 2],
                                     hour=df.iloc[:, 3], minute=df.iloc[:, 4]), utc=True)
    for c in ("WVHT", "DPD", "APD", "MWD", "WTMP"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.sort_values("time")
    # Contrôles simples : valeurs physiquement plausibles et sauts brutaux.
    df.loc[(df["WVHT"] <= 0) | (df["WVHT"] > 20), "WVHT"] = np.nan
    if "DPD" in df:
        df.loc[(df["DPD"] < 2) | (df["DPD"] > 25), "DPD"] = np.nan
    jump = df["WVHT"].diff().abs() > 2.5
    df.loc[jump, "WVHT"] = np.nan
    return df


def group_speed_ms(period_s):
    """Vitesse de groupe en eau profonde : c_g = g·T / (4π) ≈ 0,78·T m/s."""
    return G * period_s / (4 * math.pi)


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def fetch(spots):
    cfg = config.GASCOGNE
    r = requests.get(cfg["url"], timeout=60, headers={"User-Agent": "meteo-surf-prototype"})
    r.raise_for_status()
    df = parse_ndbc(r.text)
    df = df[df["time"] >= df["time"].max() - pd.Timedelta("48h")]
    df["local"] = df["time"].dt.tz_convert(config.TIMEZONE).dt.tz_localize(None)

    model = openmeteo.model_at_point(cfg["lat"], cfg["lon"])
    mdf = pd.DataFrame({"local": pd.to_datetime(model["time"]), "m_hs": model["wave_height"],
                        "m_tp": model.get("swell_wave_period") or model.get("wave_period")})

    obs = df.dropna(subset=["WVHT"]).copy()
    obs["hour"] = obs["local"].dt.floor("h")
    hourly = obs.groupby("hour").agg(hs=("WVHT", "mean"), tp=("DPD", "mean")).reset_index()
    both = hourly.merge(mdf, left_on="hour", right_on="local", how="inner").dropna(subset=["hs", "m_hs"])
    recent = both[both["hour"] >= both["hour"].max() - pd.Timedelta(hours=config.BUOY_COMPARE_HOURS)] if len(both) else both
    ratio = None
    if len(recent) >= 4 and recent["m_hs"].mean() > 0.2:
        lo, hi = config.BUOY_RATIO_BOUNDS
        ratio = float(np.clip(recent["hs"].mean() / recent["m_hs"].mean(), lo, hi))

    last = obs.iloc[-1] if len(obs) else None
    if last is not None:  # période et direction : dernière valeur valide des 3 dernières heures
        win = obs[obs["time"] >= last["time"] - pd.Timedelta("3h")]
        for col in ("DPD", "MWD"):
            if col in win and win[col].notna().any():
                last = last.copy(); last[col] = win[col].dropna().iloc[-1]
    period = None
    if last is not None and np.isfinite(last.get("DPD", np.nan)):
        period = float(last["DPD"])
    elif len(mdf):
        period = float(pd.Series(mdf["m_tp"]).dropna().iloc[-1])

    eta = {}
    if period:
        speed_kmh = group_speed_ms(period) * 3.6
        for s in spots:
            eta[s["name"]] = round(haversine_km((cfg["lat"], cfg["lon"]), (s["lat"], s["lon"])) / speed_kmh, 1)

    fmt = lambda t: t.strftime("%Y-%m-%dT%H:%M")
    return {
        "id": cfg["id"], "lat": cfg["lat"], "lon": cfg["lon"],
        "latest": None if last is None else {
            "time": fmt(last["local"]), "hs": round(float(last["WVHT"]), 2),
            "tp": None if not np.isfinite(last.get("DPD", np.nan)) else round(float(last["DPD"]), 1),
            "dir": None if not np.isfinite(last.get("MWD", np.nan)) else round(float(last["MWD"])),
            "sst": None if not np.isfinite(last.get("WTMP", np.nan)) else round(float(last["WTMP"]), 1)},
        "obs": [{"t": fmt(r.hour), "hs": round(float(r.hs), 2)} for r in hourly.itertuples()],
        "model": [{"t": fmt(t), "hs": h} for t, h in zip(mdf["local"], mdf["m_hs"]) if h is not None],
        "ratio": None if ratio is None else round(ratio, 3),
        "period_used": None if period is None else round(period, 1),
        "eta_hours": eta,
    }
