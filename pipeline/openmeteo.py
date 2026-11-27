"""Récupération des prévisions Open-Meteo (vagues multi-modèles, vent multi-modèles, eau, soleil)."""
import math
import time

import requests

from . import config, omcache

MARINE = "https://marine-api.open-meteo.com/v1/marine"
FORECAST = "https://api.open-meteo.com/v1/forecast"
session = requests.Session()
session.headers["User-Agent"] = "meteo-surf-prototype (non commercial)"


def get(url, params, tries=5):
    """Appel Open-Meteo avec reprises : 429 (quota), erreurs 5xx, coupures réseau et délais dépassés sont transitoires.
    Chaque appel est compté (issue #7) : points, variables, essais, codes HTTP (dont 429), même en cas d'échec."""
    statuses = []
    try:
        return _get(url, params, tries, statuses)
    finally:
        omcache.record(url, params, max(1, len(statuses)), statuses)


def _get(url, params, tries, statuses):
    last = "trop de requêtes"
    for attempt in range(tries):
        wait = 20 * (attempt + 1)
        try:
            r = session.get(url, params=params, timeout=60)
        except (requests.ConnectionError, requests.Timeout) as e:
            last = f"réseau : {type(e).__name__}"
            statuses.append(0)
            if attempt < tries - 1:
                time.sleep(wait)
                continue
            break
        statuses.append(r.status_code)
        if r.status_code == 429 or r.status_code >= 500:
            last = f"HTTP {r.status_code}"
            if attempt < tries - 1:
                time.sleep(wait)
                continue
            break
        if r.status_code == 400:
            raise ValueError(r.json().get("reason", "requête invalide"))
        r.raise_for_status()
        time.sleep(config.REQUEST_PAUSE_S)
        data = r.json()
        return data if isinstance(data, list) else [data]
    raise RuntimeError(f"Open-Meteo : échec après {tries} essais ({last})")


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

    base = omcache.cached_get("marine", MARINE, {**ll(sea_pts), **common, "cell_selection": "sea", "hourly": ",".join([
        "wave_height", "wave_period", "wave_direction", "swell_wave_height", "swell_wave_period",
        "swell_wave_direction", "secondary_swell_wave_height", "secondary_swell_wave_period",
        "secondary_swell_wave_direction", "wind_wave_height", "wind_wave_period", "wind_wave_direction",
        "sea_level_height_msl", "sea_surface_temperature"])}, lambda u, p: get(u, p))

    wave_models, wave_labels = {}, {}
    for key, label, _w, names in config.WAVE_MODELS:
        for name in names:
            try:
                wave_models[key] = omcache.cached_get(f"wave_{key}", MARINE, {**ll(sea_pts), **common, "cell_selection": "sea",
                                                      "hourly": "wave_height,wave_period,wave_direction", "models": name},
                                                      lambda u, p: get(u, p))
                wave_labels[key] = label
                break
            except ValueError:
                continue

    # Vent : une requête par modèle (issue #7), chacune redemandée seulement quand SON modèle publie un nouveau run ; on
    # reconstruit la réponse « plusieurs modèles » d'avant (variables suffixées par modèle). Soleil : à part, une fois par jour.
    wvars = ("wind_speed_10m", "wind_direction_10m", "wind_gusts_10m")
    wind = [{"hourly": {}} for _ in land_pts]
    for key, _label, api in config.WIND_MODELS:
        r = omcache.cached_get(f"wind_{key}", FORECAST, {**ll(land_pts), **common, "hourly": ",".join(wvars), "models": api},
                               lambda u, p: get(u, p))
        for j, pt in enumerate(r):
            h = pt["hourly"]
            wind[j]["hourly"].setdefault("time", h["time"])
            for v in wvars:
                wind[j]["hourly"][f"{v}_{api}"] = h.get(f"{v}_{api}", h.get(v))
    sun = omcache.cached_get("sun", FORECAST, {**ll(land_pts), **common, "daily": "sunrise,sunset"}, lambda u, p: get(u, p))
    for j, pt in enumerate(sun):
        wind[j]["daily"] = pt.get("daily", {})

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
    d = omcache.cached_get(f"point_{float(lat):.3f}_{float(lon):.3f}", MARINE,
                           {"latitude": lat, "longitude": lon, "timezone": config.TIMEZONE, "past_days": past_days,
                            "forecast_days": 2, "cell_selection": "sea",
                            "hourly": "wave_height,wave_period,swell_wave_period,wave_direction"},
                           lambda u, p: get(u, p), watch_key="point")[0]
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
