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
    return clean(df)


# Copernicus → noms NDBC utilisés dans la suite du code (premier nom présent retenu).
COPERNICUS_VARS = {"WVHT": ("VGHS", "VHM0", "VAVH"), "DPD": ("VTPK",), "APD": ("VGTA", "VTM02"),
                   "MWD": ("VDIR", "VMDR"), "WTMP": ("TEMP",)}


def _copernicus_series(ds, names):
    """Série temporelle d'une variable, sans les valeurs mal notées (QC Copernicus : 1 = bon, 2 = probablement bon)."""
    for n in names:
        if n not in ds:
            continue
        da = ds[n]
        if f"{n}_QC" in ds:
            da = da.where(ds[f"{n}_QC"].isin([1, 2]))
        # Les autres dimensions (profondeur) : on garde le premier niveau renseigné à chaque heure.
        a = da.transpose("TIME", ...).values.astype(float).reshape(da.sizes["TIME"], -1)
        first = np.argmax(np.isfinite(a), axis=1)
        return a[np.arange(len(a)), first]
    return None


def parse_copernicus(path):
    import xarray as xr
    with xr.open_dataset(path) as ds:
        out = pd.DataFrame({"time": pd.to_datetime(ds["TIME"].values).tz_localize("UTC")})
        for col, names in COPERNICUS_VARS.items():
            v = _copernicus_series(ds, names)
            out[col] = np.nan if v is None else v
        if "TIME_QC" in ds:  # heures marquées comme fausses
            out = out[np.isin(ds["TIME_QC"].values, [0, 1, 2])]
    return out


def load_copernicus(days=3):
    """Fichiers journaliers des `days` derniers jours ; les jours absents (pas encore publiés) sont ignorés."""
    import os
    import tempfile
    cfg = config.GASCOGNE
    frames = []
    today = pd.Timestamp.now("UTC").normalize()
    for k in range(days):
        d = (today - pd.Timedelta(days=k)).strftime("%Y%m%d")
        url = f"{cfg['copernicus_base']}/{d}/GL_TS_MO_{cfg['copernicus_code']}_{d}.nc"
        r = requests.get(url, timeout=60, headers={"User-Agent": "meteo-surf-prototype"})
        if r.status_code == 404:
            continue
        r.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".nc")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(r.content)
            frames.append(parse_copernicus(path))
        finally:
            os.remove(path)
    if not frames:
        raise RuntimeError("Copernicus : aucun fichier de la bouée sur les derniers jours")
    df = pd.concat(frames).drop_duplicates("time", keep="last")
    if "WVHT" not in df or df["WVHT"].notna().sum() == 0:
        raise RuntimeError("Copernicus : pas de hauteur de vagues valide")
    return clean(df)


def load():
    """Météo-France (frais, si clé) complétée par Copernicus (plus long, plus tardif), NDBC en secours.
    Renvoie (mesures, nom de la source)."""
    from . import meteofrance
    try:
        df_mf = meteofrance.load()
    except Exception:
        df_mf = None
    if df_mf is not None:
        try:
            df_c = load_copernicus()
            df = pd.concat([df_c, df_mf]).drop_duplicates("time", keep="last")  # Météo-France prioritaire
            return clean(df), "Météo-France"
        except Exception:
            return clean(df_mf), "Météo-France"
    try:
        return load_copernicus(), "Copernicus Marine"
    except Exception as e_cop:
        try:
            r = requests.get(config.GASCOGNE["url"], timeout=60, headers={"User-Agent": "meteo-surf-prototype"})
            r.raise_for_status()
            return parse_ndbc(r.text), "NOAA NDBC"
        except Exception as e_ndbc:
            raise RuntimeError(f"{e_cop} | NDBC : {e_ndbc}") from None


def clean(df):
    df = df.sort_values("time").reset_index(drop=True)
    # Contrôles simples : valeurs physiquement plausibles et sauts brutaux.
    df.loc[(df["WVHT"] <= 0) | (df["WVHT"] > 20), "WVHT"] = np.nan
    if "DPD" in df:
        df.loc[(df["DPD"] < 2) | (df["DPD"] > 25), "DPD"] = np.nan
        # La période pic ne peut pas être plus courte que la période moyenne (vu sur 62001 : Tp 2 s, Tmoy 5 s).
        if "APD" in df:
            df.loc[df["DPD"] < df["APD"], "DPD"] = np.nan
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
    df, source = load()
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
        "id": cfg["id"], "source": source, "lat": cfg["lat"], "lon": cfg["lon"],
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
