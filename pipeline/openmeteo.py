"""Récupération des prévisions Open-Meteo (vagues multi-modèles, vent multi-modèles, eau, soleil)."""
import math
import time

import requests

from . import config

MARINE = "https://marine-api.open-meteo.com/v1/marine"
FORECAST = "https://api.open-meteo.com/v1/forecast"
session = requests.Session()
session.headers["User-Agent"] = "meteo-surf-prototype (non commercial)"


def get(url, params, tries=3):
    for attempt in range(tries):
        r = session.get(url, params=params, timeout=60)
        if r.status_code == 429 and attempt < tries - 1:
            time.sleep(20 * (attempt + 1))
            continue
        if r.status_code == 400:
            raise ValueError(r.json().get("reason", "requête invalide"))
        r.raise_for_status()
        time.sleep(config.REQUEST_PAUSE_S)
        data = r.json()
        return data if isinstance(data, list) else [data]
    raise RuntimeError("Open-Meteo : trop de requêtes")


def sea_point(spot, km=3.0):
    """Point à quelques km au large, dans l'axe de la plage, pour viser une maille « mer »."""
    d = km / 111.0
    ori = math.radians(spot["ori"])
    return (spot["lat"] + d * math.cos(ori),
            spot["lon"] + d * math.sin(ori) / math.cos(math.radians(spot["lat"])))


def grid(points, step=0.03):
    """Regroupe les points qui tombent dans la même maille de modèle."""
    uniq, index, mapping = [], {}, []
    for p in points:
        key = (round(p[0] / step), round(p[1] / step))
        if key not in index:
            index[key] = len(uniq)
            uniq.append(p)
        mapping.append(index[key])
    return uniq, mapping


def ll(points):
    return {"latitude": ",".join(f"{p[0]:.4f}" for p in points),
            "longitude": ",".join(f"{p[1]:.4f}" for p in points)}


WIND_FALLBACK = ("meteofrance_seamless", "icon_seamless", "ecmwf_ifs025", "gfs_seamless")


def fill_wind(wh, var):
    """Vent d'AROME ; quand il s'arrête (environ 4 jours), heure par heure : ICON, puis ECMWF, puis GFS."""
    series = [wh.get(f"{var}_{m}") for m in WIND_FALLBACK]
    series = [s for s in series if s] or [wh.get(var)]
    n = len(series[0] or [])
    return [next((s[i] for s in series if s and i < len(s) and s[i] is not None), None) for i in range(n)]


def valid_hs(values):
    """Hauteur de vagues = 0,00 m sur toute une série : maille « terre » du modèle (surtout GFS-Wave près de la côte),
    pas une mer plate. On l'écarte pour ne pas tirer le mélange vers le bas."""
    return [None if (v is not None and v <= 0.0) else v for v in values]


def clean_daily(daily):
    """Avec plusieurs modèles, Open-Meteo suffixe lever/coucher (sunrise_icon_seamless…) : on garde une seule série."""
    out = {"time": daily.get("time", [])}
    for var in ("sunrise", "sunset"):
        key = var if daily.get(var) else next((k for k in daily if k.startswith(var + "_") and daily[k]), None)
        if key:
            out[var] = daily[key]
    return out


def fetch(spots):
    common = {"timezone": config.TIMEZONE, "forecast_days": config.FORECAST_DAYS}
    sea_pts, sea_map = grid([sea_point(s) for s in spots])
    land_pts, land_map = grid([(s["lat"], s["lon"]) for s in spots])

    base = get(MARINE, {**ll(sea_pts), **common, "cell_selection": "sea", "hourly": ",".join([
        "wave_height", "wave_period", "wave_direction", "swell_wave_height", "swell_wave_period",
        "swell_wave_direction", "secondary_swell_wave_height", "secondary_swell_wave_period",
        "secondary_swell_wave_direction", "wind_wave_height", "wind_wave_period", "wind_wave_direction",
        "sea_level_height_msl", "sea_surface_temperature"])})

    wave_models, wave_labels = {}, {}
    for key, label, _w, names in config.WAVE_MODELS:
        for name in names:
            try:
                wave_models[key] = get(MARINE, {**ll(sea_pts), **common, "cell_selection": "sea",
                                                "hourly": "wave_height,wave_period,wave_direction", "models": name})
                wave_labels[key] = label
                break
            except ValueError:
                continue

    wind = get(FORECAST, {**ll(land_pts), **common, "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                          "daily": "sunrise,sunset", "models": ",".join(m[2] for m in config.WIND_MODELS)})

    out = []
    for i, _s in enumerate(spots):
        m = base[sea_map[i]]["hourly"]
        w_raw = wind[land_map[i]]
        wh = w_raw["hourly"]

        def pick(var):
            return fill_wind(wh, var)

        out.append({
            "marine": {k: m.get(k) for k in m},
            "wave_models": {k: valid_hs(v[sea_map[i]]["hourly"]["wave_height"]) for k, v in wave_models.items()},
            "wind": {"time": wh["time"], "wind_speed_10m": pick("wind_speed_10m"),
                     "wind_direction_10m": pick("wind_direction_10m"), "wind_gusts_10m": pick("wind_gusts_10m")},
            "wind_models": {k: wh.get(f"wind_speed_10m_{api}") for k, _l, api in config.WIND_MODELS
                            if wh.get(f"wind_speed_10m_{api}")},
            "daily": clean_daily(w_raw.get("daily", {})),
        })
    return out, wave_labels


def models_at_point(lat, lon, from_local, hours=97):
    """Hauteur de vagues prévue par chaque modèle au point de la bouée, à partir de `from_local` (archive de fiabilité)."""
    out = {}
    for key, _label, _w, names in config.WAVE_MODELS:
        for name in names:
            try:
                h = get(MARINE, {"latitude": lat, "longitude": lon, "timezone": config.TIMEZONE, "forecast_days": 6,
                                 "cell_selection": "sea", "hourly": "wave_height", "models": name})[0]["hourly"]
            except ValueError:
                continue
            i = next((j for j, t in enumerate(h["time"]) if t >= from_local), None)
            hs = valid_hs(h["wave_height"][i:i + hours]) if i is not None else []
            if any(x is not None for x in hs):
                out[key] = {"t0": h["time"][i], "hs": hs}
            break
    return out


def model_at_point(lat, lon, past_days=2):
    """Prévision de vagues (mix par défaut) au point de la bouée, avec les jours passés pour comparer."""
    d = get(MARINE, {"latitude": lat, "longitude": lon, "timezone": config.TIMEZONE, "past_days": past_days,
                     "forecast_days": 2, "cell_selection": "sea",
                     "hourly": "wave_height,wave_period,swell_wave_period,wave_direction"})[0]
    return d["hourly"]


def coast_forecast(lat, lon, from_local, hours=97):
    """Hauteur, période et direction de la houle prévues (modèle par défaut) au point d'une bouée côtière, pour l'archive."""
    h = get(MARINE, {"latitude": lat, "longitude": lon, "timezone": config.TIMEZONE, "forecast_days": 6, "cell_selection": "sea",
                     "hourly": "wave_height,wave_period,wave_direction"})[0]["hourly"]
    i = next((j for j, t in enumerate(h["time"]) if t >= from_local), None)
    if i is None:
        return None
    sl = lambda k: [None if x is None else round(float(x), 2) for x in h.get(k, [])[i:i + hours]]
    hs = valid_hs(h["wave_height"][i:i + hours])
    if not any(x is not None for x in hs):
        return None
    return {"t0": h["time"][i], "hs": hs, "tp": sl("wave_period"), "dir": sl("wave_direction")}
