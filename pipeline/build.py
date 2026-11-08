"""Construit web/data/forecast.json : toutes les données dont le site a besoin, en un seul fichier.

Lancement :  python -m pipeline.build
Chaque source est optionnelle sauf Open-Meteo : si MARC, la bouée ou les marées échouent,
le fichier est quand même produit et le site affiche ce qui est disponible.
"""
import json
import traceback
from datetime import datetime

import pandas as pd

from . import buoy, candhis, config, history, marc, openmeteo, tides


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def r2(values, nd=2):
    return [None if v is None else round(float(v), nd) for v in values]


def main():
    spots = json.loads(config.SPOTS_FILE.read_text())
    meta = {"generated": datetime.now().strftime("%Y-%m-%dT%H:%M"), "sources": {}, "errors": {}}

    log("Open-Meteo : vagues, vent, eau, soleil")
    om, wave_labels = openmeteo.fetch(spots)
    times = om[0]["marine"]["time"]
    meta["sources"]["openmeteo"] = list(wave_labels.values())

    log("Ifremer MARC : modèle côtier")
    marc_data = None
    try:
        sea_pts, sea_map = openmeteo.grid([openmeteo.sea_point(s) for s in spots])
        marc_pts = marc.fetch(sea_pts, times)
        marc_data = [marc_pts[sea_map[i]] for i in range(len(spots))]
        meta["sources"]["marc"] = config.MARC_LABEL
    except Exception as e:
        meta["errors"]["marc"] = str(e)[:300]
        log(f"  MARC indisponible : {e}")

    log("Bouée Gascogne")
    gascogne = None
    try:
        gascogne = buoy.fetch(spots)
        meta["sources"]["gascogne"] = f"Bouée Gascogne 62001 (Météo-France, via {gascogne['source']})"
    except Exception as e:
        meta["errors"]["gascogne"] = str(e)[:300]
        log(f"  bouée indisponible : {e}")

    log("Bouées côtières CANDHIS")
    coast = []
    try:
        coast, cerr = candhis.fetch_all()
        for k, v in cerr.items():
            meta["errors"][f"candhis_{k}"] = v
        if coast:
            meta["sources"]["candhis"] = "Bouées côtières CANDHIS (Cerema, Licence Ouverte 2.0, temps réel non validé)"
    except Exception as e:
        meta["errors"]["candhis"] = str(e)[:300]
        log(f"  CANDHIS indisponible : {e}")

    # Archive prévision/réalité : fiabilité mesurée sur les 30 derniers jours, puis ajout du passage en cours.
    now_local = pd.Timestamp.now(tz=config.TIMEZONE).tz_localize(None).floor("h")
    reliability = None
    try:
        reliability = history.reliability(now_local)
        if history.archiving_enabled() and gascogne:
            fc = openmeteo.models_at_point(gascogne["lat"], gascogne["lon"], now_local.strftime("%Y-%m-%dT%H:00"))
            history.record(now_local.strftime("%Y-%m-%dT%H:00"), fc, gascogne.get("obs"))
            log(f"  archive : {len(fc)} modèles, {len(gascogne.get('obs') or [])} mesures de la bouée")
    except Exception as e:
        meta["errors"]["history"] = str(e)[:300]
        log(f"  archive indisponible : {e}")

    log("Marées (calcul harmonique)")
    start = times[0][:10] + "T00:00"
    tide_ports = {}
    for port in sorted({s["tide_port"] for s in spots}):
        try:
            t = tides.predict(port, start, config.FORECAST_DAYS)
            if t:
                tide_ports[port] = t
            else:
                meta["errors"][f"tide_{port}"] = "constantes absentes : lancer tools/fit_tides.py"
        except Exception as e:
            meta["errors"][f"tide_{port}"] = str(e)[:300]
    tide_coef = None
    try:
        tide_coef = tides.coefficients(start, config.FORECAST_DAYS)
        if tide_coef is None:
            meta["errors"]["tide_coef"] = "constantes de Brest absentes : lancer tools/get_refmar.py brest puis fit_tides"
    except Exception as e:
        meta["errors"]["tide_coef"] = str(e)[:300]
    if tide_ports:
        meta["sources"]["tides"] = "Calcul harmonique indépendant à partir des mesures REFMAR (© Shom, Licence Ouverte)"

    # Correction bouée : décroît de la valeur mesurée à 0 sur BUOY_CORRECTION_HOURS.
    now = pd.Timestamp.now(tz=config.TIMEZONE).tz_localize(None).floor("h")  # heure locale, comme les prévisions
    ratio = gascogne and gascogne.get("ratio")
    # La correction part de l'heure de la dernière mesure (pas de « maintenant ») : une mesure déjà ancienne
    # ne corrige donc que les heures qui la suivent.
    if ratio and gascogne.get("latest"):
        t_obs = pd.Timestamp(gascogne["latest"]["time"]).floor("h")
        if (now - t_obs) / pd.Timedelta("1h") > config.BUOY_MAX_AGE_HOURS:
            ratio = None
            meta["errors"]["gascogne_age"] = "mesure de la bouée trop ancienne : modèles non corrigés"
        else:
            now = t_obs
    corr = [1.0] * len(times)
    if ratio:
        for j, t in enumerate(times):
            dt = (pd.Timestamp(t) - now) / pd.Timedelta("1h")
            if 0 <= dt <= config.BUOY_CORRECTION_HOURS:
                corr[j] = 1 + (ratio - 1) * (1 - dt / config.BUOY_CORRECTION_HOURS)

    weights = {k: w for k, _l, w, _n in config.WAVE_MODELS}
    labels = dict(wave_labels)
    if marc_data:
        weights["marc"] = config.MARC_WEIGHT
        labels = {"marc": config.MARC_LABEL, **labels}

    out_spots = []
    for i, s in enumerate(spots):
        d = om[i]
        models = {k: v for k, v in d["wave_models"].items() if v and any(x is not None for x in v)}
        if marc_data and any(v is not None for v in marc_data[i]["hs"]):
            models = {"marc": marc_data[i]["hs"], **models}
        mix = []
        for j in range(len(times)):
            num = den = 0.0
            for k, arr in models.items():
                v = arr[j] if j < len(arr) else None
                if v is not None:
                    num += v * weights.get(k, 0.1)
                    den += weights.get(k, 0.1)
            base = d["marine"]["wave_height"][j]
            val = num / den if den else base
            mix.append(None if val is None else val * corr[j])
        marine = dict(d["marine"])
        marine["wave_height"] = mix
        port = s["tide_port"]
        tide = tides.shift(tide_ports.get(port), s.get("tide_offset_min", 0))
        if tide:
            marine["sea_level_height_msl"] = tide["hourly"][:len(times)]
        out_spots.append({
            "name": s["name"],
            "marine": {k: (r2(v) if k != "time" and isinstance(v, list) else v) for k, v in marine.items()},
            "wave_models": {k: r2(v) for k, v in models.items()},
            "wind": {k: (r2(v, 1) if k != "time" else v) for k, v in d["wind"].items()},
            "wind_models": {k: r2(v, 1) for k, v in d["wind_models"].items()},
            "daily": d["daily"],
            "tide": None if not tide else {"port": port, "label": tide["label"], "extremes": tide["extremes"]},
        })

    meta["wave_models"] = [{"key": k, "label": labels[k]} for k in labels]
    meta["wind_models"] = [{"key": k, "label": l} for k, l, _a in config.WIND_MODELS]
    meta["buoy_correction"] = ratio
    payload = {"meta": meta, "gascogne": gascogne, "coast": coast, "tide_coef": tide_coef, "reliability": reliability, "spots": out_spots}
    config.OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    size = config.OUTPUT_FILE.stat().st_size / 1024
    log(f"OK : {config.OUTPUT_FILE.relative_to(config.ROOT)} ({size:.0f} Ko) · erreurs : {list(meta['errors']) or 'aucune'}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
