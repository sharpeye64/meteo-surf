"""Cache persistant des prévisions Open-Meteo et mesure de la consommation (issue #7).

Pourquoi : le robot tourne environ 50 fois par jour pour garder les BOUÉES fraîches (mesures toutes les 30 min), mais les
modèles de prévision ne publient un nouveau run que toutes les 3 à 12 h. Redemander les mêmes prévisions à chaque passage
consomme le quota Open-Meteo sans rien apporter.

Règle : une réponse Open-Meteo est réutilisée tant qu'AUCUN des modèles dont elle dépend n'a publié de nouveau run. On le
sait grâce aux métadonnées publiques d'Open-Meteo (`/data/<modèle>/static/meta.json`, « non comptées dans les limites
journalières et mensuelles » d'après https://open-meteo.com/en/docs/model-updates). On redemande aussi :
  - si les paramètres changent (spots ajoutés, variables…), au changement de jour (heure de Paris), ou après 6 h (filet) ;
  - après 1 h si les métadonnées sont illisibles (on ne sait pas : on reste prudent).
Un nouveau run d'un modèle SURVEILLÉ est pris au premier passage qui suit sa disponibilité, comme avant. S'il a moins de
10 min (délai conseillé par Open-Meteo pour que tous ses serveurs l'aient), il est redemandé une fois au passage suivant.
Limite : Open-Meteo précise que le « best match » n'est pas directement lié aux runs individuels
(https://open-meteo.com/en/docs/model-updates). Pour la requête « marine » (best match), la surveillance des modèles qui
la composent est donc une approximation, bornée par le filet de 6 h. L'âge affiché est l'âge de COLLECTE de la réponse,
pas l'âge du run du modèle.
Mode dégradé : si Open-Meteo ne répond pas, une réponse en cache de moins de 12 h est réutilisée et SIGNALÉE (âge et
provenance dans forecast.json et health.json). Au-delà, la génération échoue comme avant et le site garde sa version.

Le cache vit dans `.cache/openmeteo/` (ou METEO_CACHE_DIR) ; dans GitHub Actions il est conservé d'un passage à l'autre
par actions/cache. METEO_CACHE=0 désactive le cache : tout est redemandé à chaque passage (mais le vent reste en une requête par modèle,
contrairement à avant ce lot).
"""
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from . import config, safe

CACHE_DIR = Path(os.environ.get("METEO_CACHE_DIR") or (config.ROOT / ".cache" / "openmeteo"))
ENABLED = os.environ.get("METEO_CACHE", "1") != "0"
TTL_MAX_H = 6.0       # filet de sécurité : jamais plus de 6 h sans redemander
TTL_UNKNOWN_H = 1.0   # métadonnées illisibles : on redemande au bout d'1 h
USAGE_DIR = CACHE_DIR.parent / "usage"   # compteurs journaliers (conservés par actions/cache, au mieux : voir docs/quotas-licences.md)
STALE_MAX_H = 12.0    # mode dégradé : âge maximal d'une prévision réutilisée si Open-Meteo est en panne
SETTLE_S = 600        # Open-Meteo conseille d'attendre 10 min après la disponibilité d'un run

META_URL = {"api": "https://api.open-meteo.com/data/{m}/static/meta.json",
            "marine": "https://marine-api.open-meteo.com/data/{m}/static/meta.json"}

# Modèles dont dépend chaque groupe de requêtes (vérifiés le 27/11/2026 : tous ces fichiers de métadonnées existent).
MARINE_ALL = [("marine", m) for m in ("meteofrance_wave", "dwd_ewam", "ecmwf_wam025", "ncep_gfswave025",
                                      "meteofrance_currents", "meteofrance_sea_surface_temperature")]
WATCH = {
    "marine": MARINE_ALL,                       # « best match » marine : vagues, houle, niveau de la mer, eau
    "wave_mfwam": [("marine", "meteofrance_wave")],
    "wave_ewam": [("marine", "dwd_ewam")],
    "wave_ecmwf": [("marine", "ecmwf_wam025")],
    "wave_gfs": [("marine", "ncep_gfswave025")],
    # vent : une requête PAR MODÈLE, redemandée seulement quand CE modèle publie (les « seamless » enchaînent plusieurs grilles)
    "wind_arome": [("api", "meteofrance_arome_france_hd"), ("api", "meteofrance_arpege_europe")],
    "wind_icon": [("api", "dwd_icon_d2"), ("api", "dwd_icon_eu"), ("api", "dwd_icon")],
    "wind_gfs": [("api", "ncep_gfs013"), ("api", "ncep_gfs025")],
    "wind_ecmwf": [("api", "ecmwf_ifs025")],
    "sun": [],                                  # lever et coucher du soleil : calcul astronomique, une fois par jour
    "point": MARINE_ALL,                        # prévision au point d'une bouée (comparaison mesure / modèle)
}
WIND_ALL = [w for g in ("wind_arome", "wind_icon", "wind_gfs", "wind_ecmwf") for w in WATCH[g]]
TTL_H = {"sun": 24.0}   # durée maximale propre à un groupe (sinon TTL_MAX_H) ; le changement de jour s'applique toujours

USAGE = []        # une ligne par requête HTTP de DONNÉES envoyée à Open-Meteo (rempli par openmeteo.get)
STATE = {}        # par groupe : provenance (api / cache / cache-dégradé), âge, raison
CHANGED = False   # vrai si le cache a été modifié pendant ce passage (le workflow ne le sauvegarde que dans ce cas)
_metas = {}
META_CHECKS = {"ok": 0, "failed": 0}


def reset():
    global CHANGED
    USAGE.clear(); STATE.clear(); _metas.clear()
    META_CHECKS.update(ok=0, failed=0)
    CHANGED = False


def model_meta(kind, name):
    """Métadonnées publiques d'un modèle (heure de disponibilité du dernier run). None si illisibles."""
    k = (kind, name)
    if k not in _metas:
        try:
            r = requests.get(META_URL[kind].format(m=name), timeout=20, headers={"User-Agent": "houlalah (non commercial)"})
            r.raise_for_status()
            _metas[k] = r.json()
            META_CHECKS["ok"] += 1
        except Exception:
            _metas[k] = None
            META_CHECKS["failed"] += 1
    return _metas[k]


def _snapshot(watch, now):
    """Heure de disponibilité du dernier run de chaque modèle, seulement s'il est « posé » (10 min passées)."""
    snap = {}
    for kind, name in watch:
        m = model_meta(kind, name)
        a = (m or {}).get("last_run_availability_time")
        snap[name] = int(a) if a and now >= a + SETTLE_S else None
    return snap


def _key(url, params):
    return hashlib.sha1((url + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:16]


def _day(ts):
    return datetime.fromtimestamp(ts, ZoneInfo(config.TIMEZONE)).date()


def why_refresh(entry, key, watch, now, ttl_h=TTL_MAX_H):
    """Raison de redemander à Open-Meteo, ou None si la réponse en cache est encore la plus récente possible."""
    if entry is None:
        return "pas de cache"
    if entry.get("key") != key:
        return "paramètres changés"
    age_h = (now - entry["fetched"]) / 3600
    if _day(now) != _day(entry["fetched"]):
        return "nouveau jour"
    if age_h > ttl_h:
        return f"âge > {ttl_h:g} h"
    old = entry.get("runs") or {}
    unknown = False
    for kind, name in watch:
        m = model_meta(kind, name)
        a = (m or {}).get("last_run_availability_time")
        if not a:
            unknown = True
            continue
        # pris DÈS sa disponibilité (aucun retard par rapport à avant) ; s'il n'était pas encore « posé » au moment de la
        # requête, l'instantané vaut None et la réponse est redemandée au passage suivant (une fois stabilisée)
        if old.get(name) != int(a):
            return f"nouveau run {name}"
    if unknown and age_h > TTL_UNKNOWN_H:
        return f"métadonnées illisibles et âge > {TTL_UNKNOWN_H:g} h"
    return None


def _path(group):
    return CACHE_DIR / f"{group}.json"


def valid(data):
    """Réponse exploitable : liste non vide de lieux, chacun avec des séries de la même longueur que son axe « time »."""
    if not isinstance(data, list) or not data:
        return False
    for pt in data:
        blocks = [pt.get(k) for k in ("hourly", "daily") if isinstance(pt, dict) and pt.get(k) is not None]
        if not blocks:
            return False
        for b in blocks:
            t = b.get("time") if isinstance(b, dict) else None
            if not isinstance(t, list) or not t:
                return False
            if any(isinstance(v, list) and len(v) != len(t) for k, v in b.items() if k != "time"):
                return False
    return True


def max_age_h(group):
    """Âge maximal publiable d'une réponse : 24 h pour le soleil (calcul astronomique), 12 h pour la météo (mode dégradé)."""
    return TTL_H.get(group, STALE_MAX_H)


def _load(group):
    try:
        e = json.loads(_path(group).read_text(encoding="utf-8"))
        return e if valid(e.get("data")) else None   # cache abîmé : ignoré, comme s'il n'existait pas
    except Exception:
        return None


def cached_get(group, url, params, fetcher, watch_key=None):
    """Comme fetcher(url, params), mais réutilise la dernière réponse si aucun modèle concerné n'a publié depuis."""
    global CHANGED
    if not ENABLED:
        STATE[group] = {"source": "api", "reason": "cache désactivé"}
        return fetcher(url, params)
    watch = WATCH[watch_key or group]
    now = time.time()
    key = _key(url, params)
    entry = _load(group)
    reason = why_refresh(entry, key, watch, now, TTL_H.get(watch_key or group, TTL_MAX_H))
    if reason is None:
        STATE[group] = {"source": "cache", "fetched": entry["fetched"], "age_h": round((now - entry["fetched"]) / 3600, 2)}
        return entry["data"]
    try:
        data = fetcher(url, params)
        if not valid(data):
            raise RuntimeError("Open-Meteo : réponse incomplète (séries vides ou de longueurs différentes)")
    except ValueError:
        raise   # requête refusée (nom de modèle inconnu…) : pas de repli, l'appelant essaie le nom suivant
    except Exception as e:
        if entry and entry.get("key") == key and (now - entry["fetched"]) / 3600 <= max_age_h(watch_key or group):
            age = round((now - entry["fetched"]) / 3600, 2)
            STATE[group] = {"source": "cache-dégradé", "fetched": entry["fetched"], "age_h": age,
                            "reason": safe.public_error(f"Open-Meteo indisponible ({e})", 160)}
            return entry["data"]
        raise
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _path(group).with_suffix(".tmp")
    tmp.write_text(json.dumps({"key": key, "fetched": now, "runs": _snapshot(watch, now), "data": data}, separators=(",", ":")), encoding="utf-8")
    tmp.replace(_path(group))
    CHANGED = True
    STATE[group] = {"source": "api", "fetched": now, "age_h": 0.0, "reason": reason}
    return data


def weight(params):
    """Coût d'une requête selon la règle publiée par Open-Meteo pour UN lieu : plus de 10 variables ou plus de 14 jours
    comptent en fraction d'appel supplémentaire. Retourne (variables, jours, poids pour un lieu)."""
    n_models = len([m for m in str(params.get("models", "")).split(",") if m]) or 1
    n_vars = sum(len([v for v in str(params.get(k, "")).split(",") if v]) for k in ("hourly", "daily", "current")) * n_models
    days = int(params.get("forecast_days", 7)) + int(params.get("past_days", 0))
    return n_vars, days, max(1.0, n_vars / 10) * max(1.0, days / 14)


def record(url, params, attempts, statuses):
    """Instrumentation d'une requête HTTP de données (appelée par openmeteo.get)."""
    n_vars, days, w = weight(params)
    pts = len(str(params.get("latitude", "")).split(","))
    USAGE.append({"api": "marine" if "marine" in url else "forecast", "points": pts, "variables": n_vars, "days": days,
                  "models": params.get("models") or "best_match", "attempts": attempts, "statuses": statuses,
                  "w_request": round(w, 2), "w_points": round(w * pts, 2)})


def summary():
    """Résumé public (sans adresse ni paramètre ; raisons passées par safe.public_error) : forecast.json (meta.api) et health.json.
    « requests » = requêtes logiques ; « attempts » = tentatives HTTP réellement envoyées (reprises comprises). Les poids sont
    séparés selon l'issue de chaque tentative : on ne suppose PAS qu'un refus 429 ou une coupure réseau soit facturé."""
    u = USAGE
    att = [(x, st) for x in u for st in (x["statuses"] or [0])]
    ok = [(x, st) for x, st in att if st == 200]
    from datetime import timezone as _utc
    from . import timefmt
    loc = lambda ts: timefmt.fmt(datetime.fromtimestamp(ts, _utc.utc), timefmt.PARIS)   # contrat horaire (issue #2)
    groups = {}
    for g, st in sorted(STATE.items()):
        d = {k: (safe.public_error(v, 160) if k == "reason" else v) for k, v in st.items() if k != "fetched"}
        if st.get("fetched"):
            d["fetched"] = loc(st["fetched"])
        groups[g] = d
    weather = [st["fetched"] for g, st in STATE.items() if g != "sun" and st.get("fetched")]
    return {
        "openmeteo": {
            "requests": len(u),                          # requêtes logiques
            "http_requests": len(u),                     # (ancien nom, gardé) = requêtes logiques
            "attempts": len(att),                        # tentatives HTTP envoyées, reprises comprises
            "attempts_ok": len(ok),
            "attempts_429": sum(st == 429 for _x, st in att),
            "attempts_5xx": sum(isinstance(st, int) and st >= 500 for _x, st in att),
            "attempts_network": sum(st == 0 for _x, st in att),
            "points": sum(x["points"] for x in u),
            "calls_if_per_request": round(sum(x["w_request"] for x, _st in ok), 1),    # H1, tentatives acceptées
            "calls_if_per_point": round(sum(x["w_points"] for x, _st in ok), 1),       # H2, tentatives acceptées
            "calls_if_per_point_refused": round(sum(x["w_points"] for x, st in att if st != 200), 1),   # si les refus comptaient
            "retries": len(att) - len(u),
            "http_429": sum(st == 429 for _x, st in att),
            "http_5xx": sum(isinstance(st, int) and st >= 500 for _x, st in att),
            "meta_checks": dict(META_CHECKS),
            "cache": "on" if ENABLED else "off",
            "forecast_fetched": loc(min(weather)) if weather else None,   # collecte la plus ANCIENNE des prévisions météo
            "groups": groups,
        }
    }


def persist_daily(summary_, generated):
    """Compteurs du jour (heure de Paris), cumulés d'un passage à l'autre dans USAGE_DIR ; 31 jours gardés.
    Conservés par actions/cache : au mieux (un cache peut être évincé)."""
    om = summary_["openmeteo"]
    day = generated[:10]
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    f = USAGE_DIR / f"{day}.json"
    try:
        cur = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        cur = {"day": day, "runs": 0}
    cur["runs"] += 1
    for k in ("requests", "attempts", "attempts_ok", "attempts_429", "attempts_5xx", "attempts_network", "points",
              "calls_if_per_request", "calls_if_per_point", "calls_if_per_point_refused"):
        cur[k] = round(cur.get(k, 0) + (om.get(k) or 0), 1)
    cur["last"] = generated
    f.write_text(json.dumps(cur, separators=(",", ":")), encoding="utf-8")
    for old in sorted(USAGE_DIR.glob("*.json"))[:-31]:
        old.unlink()
    return cur
