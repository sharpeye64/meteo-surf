"""Récupération des prévisions Open-Meteo (vagues multi-modèles, vent multi-modèles, eau, soleil)."""
import math
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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


LAST_OFFSET_S = None       # décalage (s) des heures de la dernière série publiée : instant = heure écrite − décalage
LAST_SUN_OFFSET_S = None


def offset_of(resp):
    """utc_offset_seconds d'une réponse ; à défaut, décalage de Paris à sa première heure (comme Open-Meteo à la requête)."""
    o = (resp[0] if resp else {}).get("utc_offset_seconds")
    if o is not None:
        return int(o)
    t = ((resp[0].get("hourly") or resp[0].get("daily") or {}).get("time") or ["2026-01-01T00:00"])[0]
    return int(datetime.strptime(t[:16] if len(t) > 10 else t + "T12:00", "%Y-%m-%dT%H:%M").replace(tzinfo=ZoneInfo(config.TIMEZONE)).utcoffset().total_seconds())


def shift_str(t, seconds):
    return (datetime.strptime(t[:16], "%Y-%m-%dT%H:%M") + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M")


def check_coverage(groups, ref, now=None, hours=48):
    """Chaque groupe doit couvrir l'heure actuelle et les 48 h suivantes (heure de Paris), sinon les prévisions ne sont pas
    publiables : la génération échoue et le site garde sa version. Le décalage de chaque groupe est noté (mode dégradé)."""
    now = (now or datetime.now(ZoneInfo(config.TIMEZONE))).strftime("%Y-%m-%dT%H:00")
    want = [t for t in ref if t >= now][:hours]
    if len(want) < hours:
        raise RuntimeError(f"Open-Meteo : l'axe horaire ne couvre pas les {hours} prochaines heures")
    for g, r in groups.items():
        times = r[0]["hourly"]["time"]
        have = set(times)
        if any(t not in have for t in want):
            raise RuntimeError(f"Open-Meteo : prévisions « {g} » incomplètes pour les {hours} prochaines heures")
        shift = (datetime.strptime(ref[0], "%Y-%m-%dT%H:%M") - datetime.strptime(times[0], "%Y-%m-%dT%H:%M")).total_seconds() / 3600
        if shift and g in omcache.STATE:
            omcache.STATE[g]["shift_h"] = shift


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

    # Vent : une requête par modèle (issue #7), chacune redemandée seulement quand SON modèle publie un nouveau run. Soleil : à part.
    wvars = ("wind_speed_10m", "wind_direction_10m", "wind_gusts_10m")
    wind_raw = {api: omcache.cached_get(f"wind_{key}", FORECAST, {**ll(land_pts), **common, "hourly": ",".join(wvars), "models": api},
                                        lambda u, p: get(u, p))
                for key, _label, api in config.WIND_MODELS}
    sun = omcache.cached_get("sun", FORECAST, {**ll(land_pts), **common, "daily": "sunrise,sunset"}, lambda u, p: get(u, p))

    # ALIGNEMENT SUR LES HEURES RÉELLES (revue de la PR #12) : en mode dégradé, une réponse en cache peut dater de la veille
    # (elle commence alors 24 h plus tôt) alors qu'une autre est du jour. Plus aucune série n'est combinée par position :
    # tout est replacé sur un même axe horaire, celui de la réponse la plus récente, heure par heure (par date pour le soleil).
    hourly_groups = {"marine": base, **{f"wave_{k}": v for k, v in wave_models.items()},
                     **{f"wind_{k}": wind_raw[api] for k, _l, api in config.WIND_MODELS}}
    # Décalage horaire de chaque réponse (issue #2) : Open-Meteo écrit TOUTE une série avec le décalage du moment de la requête.
    # Une réponse en cache d'avant un changement d'heure a donc un autre décalage : on ramène toutes les heures à celui de la mer.
    global LAST_OFFSET_S, LAST_SUN_OFFSET_S
    ref_off = offset_of(base)
    for g, r in hourly_groups.items():
        off = offset_of(r)
        if off != ref_off:
            for pt in r:
                pt["hourly"] = {**pt["hourly"], "time": [shift_str(t, ref_off - off) for t in pt["hourly"]["time"]]}
    LAST_OFFSET_S = ref_off
    LAST_SUN_OFFSET_S = offset_of(sun)
    t0 = max(r[0]["hourly"]["time"][0] for r in hourly_groups.values())
    start = datetime.strptime(t0, "%Y-%m-%dT%H:%M")
    ref = [(start + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(24 * config.FORECAST_DAYS)]
    check_coverage(hourly_groups, ref)

    def align(times, values):
        pos = {t: i for i, t in enumerate(times or [])}
        values = values or []
        return [values[pos[t]] if t in pos and pos[t] < len(values) else None for t in ref]

    days = sorted({t[:10] for t in ref})

    def align_daily(d):
        pos = {t: i for i, t in enumerate(d.get("time") or [])}
        out = {"time": days}
        for k, v in d.items():
            if k != "time" and isinstance(v, list):
                out[k] = [v[pos[t]] if t in pos and pos[t] < len(v) else None for t in days]
        return out

    out = []
    for i, _s in enumerate(spots):
        m = base[sea_map[i]]["hourly"]
        wh = {"time": ref}
        for api, r in wind_raw.items():
            h = r[land_map[i]]["hourly"]
            for v in wvars:
                wh[f"{v}_{api}"] = align(h["time"], h.get(f"{v}_{api}", h.get(v)))

        def pick(var):
            return fill_wind(wh, var)

        out.append({
            "marine": {"time": ref, **{k: align(m["time"], m.get(k)) for k in m if k != "time"}},
            "wave_models": {k: valid_hs(align(v[sea_map[i]]["hourly"]["time"], v[sea_map[i]]["hourly"]["wave_height"]))
                            for k, v in wave_models.items()},
            "wind": {"time": ref, "wind_speed_10m": pick("wind_speed_10m"),
                     "wind_direction_10m": pick("wind_direction_10m"), "wind_gusts_10m": pick("wind_gusts_10m")},
            "wind_models": {k: wh.get(f"wind_speed_10m_{api}") for k, _l, api in config.WIND_MODELS
                            if any(x is not None for x in wh.get(f"wind_speed_10m_{api}") or [])},
            "daily": clean_daily(align_daily(sun[land_map[i]].get("daily", {}))),
        })
    return out, wave_labels


def buoy_points():
    """Points de TOUTES les bouées suivies, dans un ordre fixe (la requête groupée reste la même d'un passage à l'autre)."""
    from . import candhis, ibi_buoys
    return ([{"id": s["id"], "lat": s["lat"], "lon": s["lon"]} for s in candhis.STATIONS + ibi_buoys.STATIONS]
            + [{"id": "gascogne", "lat": config.GASCOGNE["lat"], "lon": config.GASCOGNE["lon"]}])


def buoy_forecasts(points):
    """Prévisions aux points des bouées pour l'archive (issue #1) : UNE requête par modèle pour TOUTES les bouées (avant : une
    par bouée), via le cache (#7) : redemandée seulement quand le modèle publie un nouveau run.
    Retourne {"ref": réponse best match (hauteur, période, direction) ou None, "models": {clé: (nom d'API, réponse)},
    "missing": {clé: raison}}. Chaque requête est indépendante : un échec (best match compris) ne fait perdre que sa série."""
    from . import safe
    common = {"latitude": ",".join(str(p["lat"]) for p in points), "longitude": ",".join(str(p["lon"]) for p in points),
              "timezone": config.TIMEZONE, "forecast_days": 6, "cell_selection": "sea"}
    out = {"ref": None, "models": {}, "missing": {}}
    try:
        out["ref"] = omcache.cached_get("buoys_marine", MARINE, {**common, "hourly": "wave_height,wave_period,wave_direction"},
                                        lambda u, p: get(u, p), cycles=True)
    except Exception as e:
        out["missing"]["base"] = safe.public_error(str(e), 160)
    for key, _label, _w, names in config.WAVE_MODELS:
        why = "nom de modèle refusé"
        for name in names:
            try:
                out["models"][key] = (name, omcache.cached_get(f"buoys_wave_{key}", MARINE, {**common, "hourly": "wave_height", "models": name},
                                                               lambda u, p: get(u, p), cycles=True))
                break
            except ValueError:
                continue
            except Exception as e:
                why = safe.public_error(str(e), 160)
                break
        if key not in out["models"]:
            out["missing"][key] = why
    return out


def model_at_point(lat, lon, past_days=2):
    """Prévision de vagues (mix par défaut) au point de la bouée, avec les jours passés pour comparer."""
    d = omcache.cached_get(f"point_{float(lat):.3f}_{float(lon):.3f}", MARINE,
                           {"latitude": lat, "longitude": lon, "timezone": config.TIMEZONE, "past_days": past_days,
                            "forecast_days": 2, "cell_selection": "sea",
                            "hourly": "wave_height,wave_period,swell_wave_period,wave_direction"},
                           lambda u, p: get(u, p), watch_key="point")[0]
    return {**d["hourly"], "_utc_offset": d.get("utc_offset_seconds")}
