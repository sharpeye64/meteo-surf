"""Construit web/data/forecast.json : toutes les données dont le site a besoin, en un seul fichier.

Lancement :  python -m pipeline.build
Chaque source est optionnelle sauf Open-Meteo : si MARC, la bouée ou les marées échouent,
le fichier est quand même produit et le site affiche ce qui est disponible.
"""
import json
import sys
import traceback
from datetime import datetime

import pandas as pd

from . import appdata, archive, buoy, candhis, config, ibi_buoys, melange, omcache, safe, seo, history, marc, openmeteo, tides, timefmt


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def r2(values, nd=2):
    return [None if v is None else round(float(v), nd) for v in values]


def keep_silent(coast, offshore, meta, d=None):
    """Bouée absente du passage (source en panne, ou bouée qui n'envoie plus rien) : on la reprend dans l'archive au lieu de la
    faire disparaître (demande de l'utilisateur, 23/11/2026).
    - Dernière mesure de moins de 48 h (souvent : le site CANDHIS ne répond pas) : bouée normale, avec ses 48 dernières heures
      archivées. Son âge réel s'affiche comme d'habitude.
    - Plus ancienne (Anglet, muette depuis le 18/11) : « silent », sans historique ; le site et l'appli la montrent grisée
      (« pas de mesure depuis le 18/11 ») et ne la choisissent jamais par défaut. Au-delà de 30 jours, elle disparaît."""
    try:
        arch = history.coast_rows([s["id"] for s in candhis.STATIONS + ibi_buoys.STATIONS], d)
        now = pd.Timestamp.now(tz=config.TIMEZONE).tz_localize(None)
        # une source peut aussi renvoyer une vieille mesure comme si elle était fraîche (CANDHIS, Anglet, 25/11/2026) :
        # toute bouée dont la dernière mesure a plus de 48 h est marquée muette, d'où qu'elle vienne
        for b in list(coast) + list(offshore):
            t = (b.get("latest") or {}).get("time")
            if t and pd.Timestamp(t) < now - pd.Timedelta(hours=48):
                b["silent"] = True
        for lst, stations, large in ((coast, candhis.STATIONS, False), (offshore, ibi_buoys.STATIONS, True)):
            have = {b["id"] for b in lst}
            for st in stations:
                rows = arch.get(st["id"])
                if st["id"] in have or not rows:
                    continue
                t = max(rows)
                if pd.Timestamp(t) < now - pd.Timedelta(days=30):
                    continue
                silent = pd.Timestamp(t) < now - pd.Timedelta(hours=48)
                pick = lambda r: {k: r.get(k) for k in ("hs", "hmax", "tp", "dir", "sst")}
                since = (pd.Timestamp(t) - pd.Timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M")
                b = {"id": st["id"], "name": st["name"], "lat": st["lat"], "lon": st["lon"], "latest": {"time": t, **pick(rows[t])},
                     "obs": [] if silent else [{"t": k, **pick(r)} for k, r in rows.items() if k >= since]}
                if silent:
                    b["silent"] = True
                if large:
                    b.update(sub=st["sub"], kind="large", model=[])
                lst.append(b)
                log(f"  bouée {'muette' if silent else 'reprise de l’archive'} : {st['name']} (dernière mesure {t})")
    except Exception as e:
        meta["errors"]["silent_buoys"] = str(e)[:300]


def archive_pass(meta, gascogne, coast, offshore, bpts, weights, marc_buoys, times, ratio, corr_start, gen_utc):
    """Archive du passage (heures UTC multiples de 3, main seulement). Issue #1 :
    - UNE requête par modèle pour toutes les bouées (avant : 21 + 4 requêtes), via le cache (#7) ;
    - anciens fichiers (runs/, coast_runs/, obs/, coast_obs/) : même format qu'avant, sans doublon ;
    - nouveau fichier buoy_runs/ (v2) : modèles, MARC, mélanges brut et corrigé, provenance (pipeline/archive.py)."""
    if not history.archiving_enabled():
        return
    d = history.history_dir()
    issued_utc = gen_utc.floor("h").to_pydatetime()
    issued_old = gen_utc.floor("h").tz_convert(config.TIMEZONE).tz_localize(None).strftime("%Y-%m-%dT%H:00")
    buoys = list(coast) + list(offshore)
    history.record_obs(gascogne.get("obs") if gascogne else None, buoys, d)   # mesures : fusion par heure, à chaque passage
    issued_v2 = timefmt.fmt(issued_utc, timefmt.PARIS)
    if archive.already(d, issued_v2) and history.already(d, issued_old):
        log("  archive : heure déjà archivée (pas de doublon)")
        return
    fc = openmeteo.buoy_forecasts(bpts)
    ids = [p["id"] for p in bpts]
    # anciens formats : contenu identique à avant (mêmes points, mêmes variables, même découpage), sans doublon
    old = {}
    for k, (_api, r) in fc["models"].items():
        h = history.slice_from(r[ids.index("gascogne")]["hourly"], issued_old)
        if h:
            old[k] = {"t0": h["t0"], "hs": h["hs"]}
    if gascogne and old:
        history.record(issued_old, old, None, d)
    live = {b["id"] for b in buoys}
    cfc = {}
    for j, bid in enumerate(ids):
        if bid in live:
            h = history.slice_from(fc["ref"][j]["hourly"], issued_old, extra=True)
            if h:
                cfc[bid] = h
    history.record_coast(issued_old, cfc, None, d)
    # v2 : modèles, MARC, mélanges brut et corrigé, provenance
    st = "appliquée" if ratio else ("mesure trop ancienne" if meta["errors"].get("gascogne_age") else "pas de rapport mesuré")
    corr_info = {"ratio": ratio or None, "ratio_measured": (gascogne or {}).get("ratio"), "start": corr_start if ratio else None,
                 "t_obs": ((gascogne or {}).get("latest") or {}).get("time") if ratio else None, "status": st}
    line = archive.build_line(issued_utc, gen_utc.to_pydatetime(), fc, bpts, weights, marc_buoys, times, corr_info)
    n = archive.write(d, line)
    nm = sum(1 for b in line["b"].values() for v in b["models"].values() if v)
    log(f"  archive v2 : {len(line['b'])} bouées, {nm} séries de modèles, MARC pour {sum(1 for b in line['b'].values() if b['marc'])} bouées, "
        f"{n / 1024:.0f} Ko ; anciens formats : {len(old)} modèles Gascogne, {len(cfc)} bouées côtières"
        + ("" if not fc["missing"] else f" ; absents : {fc['missing']}"))


def write_health(payload, spots):
    """health.json : état de la génération, SANS secret ni adresse d'API. Lu par une surveillance externe (un fichier figé
    ne peut pas signaler sa propre panne : c'est l'ancienneté de « generated », vue de l'extérieur, qui alerte)."""
    meta = payload["meta"]
    clean = lambda m: safe.public_error(m, 160)
    now = pd.Timestamp(meta["generated"])
    buoys = []
    for b in (payload.get("coast") or []) + (payload.get("offshore") or []) + ([dict(payload["gascogne"], id="gascogne", name="Gascogne")] if payload.get("gascogne") else []):
        t = (b.get("latest") or {}).get("time")
        buoys.append({"id": str(b.get("id")), "name": b.get("name"), "last": t, "age_h": round((now - pd.Timestamp(t)) / pd.Timedelta("1h"), 1) if t else None,
                      "silent": bool(b.get("silent"))})
    health = {"generated": meta["generated"], "site": config.SITE_URL, "spots_expected": len(spots), "spots": len(payload.get("spots") or []),
              "errors": {k: clean(v) for k, v in (meta.get("errors") or {}).items()}, "buoys": buoys, "api": meta.get("api")}
    if meta.get("_test"):
        health["_test"] = True
    (config.OUT_DIR / "health.json").write_text(json.dumps(health, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    spots = json.loads(config.SPOTS_FILE.read_text())
    # heure de Paris (le robot GitHub tourne en UTC) : le site et l'appli affichent « mis à jour à… » sans conversion
    gen_utc = pd.Timestamp.now(tz="UTC")   # instant exact : l'heure de Paris écrite seule est ambiguë une heure par an (issue #2)
    meta = {"generated": gen_utc.tz_convert(config.TIMEZONE).strftime("%Y-%m-%dT%H:%M"), "sources": {}, "errors": {}}
    if config.TEST_RUN:
        meta["_test"] = True   # sources simulées : le contrôle de publication refuse ces données

    omcache.reset()
    log("Open-Meteo : vagues, vent, eau, soleil")
    om, wave_labels = openmeteo.fetch(spots)
    log("  " + ", ".join(f"{g} : {s['source']}" + (f" ({s['reason']})" if s.get("reason") else f" ({s.get('age_h')} h)") for g, s in sorted(omcache.STATE.items())))
    times = om[0]["marine"]["time"]
    meta["sources"]["openmeteo"] = list(wave_labels.values())

    log("Ifremer MARC : modèle côtier")
    marc_data = None
    marc_buoys = None   # MARC aux points des bouées, pour l'archive (issue #1) ; None = indisponible
    bpts = openmeteo.buoy_points() if history.archiving_enabled() else []
    try:
        sea_pts, sea_map = openmeteo.grid([openmeteo.sea_point(s) for s in spots])
        marc_pts = marc.fetch(sea_pts + [(p["lat"], p["lon"]) for p in bpts], times)   # même lecture OPeNDAP
        marc_data = [marc_pts[sea_map[i]] for i in range(len(spots))]
        if bpts:
            marc_buoys = {p["id"]: marc_pts[len(sea_pts) + j] for j, p in enumerate(bpts)}
        meta["sources"]["marc"] = config.MARC_LABEL
    except Exception as e:
        meta["errors"]["marc"] = str(e)[:300]
        log(f"  MARC indisponible : {e}")

    log("Bouée Gascogne")
    gascogne = None
    try:
        gascogne = buoy.fetch(spots)
        if buoy.MF_ERROR:
            meta["errors"]["meteofrance"] = buoy.MF_ERROR
        meta["sources"]["gascogne"] = ("Bouée Gascogne 62001 (Météo-France)" if gascogne["source"] == "Météo-France"
                                       else f"Bouée Gascogne 62001 (Météo-France, via {gascogne['source']})")
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

    log("Bouées du large fraîches (Bilbao-Vizcaya, Donostia)")
    offshore = []
    model_offsets = {}
    try:
        offshore, oerr = ibi_buoys.fetch_all()
        for k, v in oerr.items():
            meta["errors"][f"ibi_{k}"] = v
        for b in offshore:  # prévision des modèles au point de la bouée, pour comparer à la mesure
            try:
                m = openmeteo.model_at_point(b["lat"], b["lon"])
                b["model"] = [{"t": t, "hs": h} for t, h in zip(m["time"], m["wave_height"]) if h is not None]
                model_offsets[str(b["id"])] = m.get("_utc_offset")   # pour écrire ces heures au contrat horaire (issue #2)
            except Exception as e:
                b["model"] = []
                meta["errors"][f"ibi_model_{b['id']}"] = str(e)[:200]
        if offshore:
            meta["sources"]["ibi"] = "Bouées du large Bilbao-Vizcaya (Puertos del Estado) et Donostia (Euskalmet), via Copernicus Marine"
    except Exception as e:
        meta["errors"]["ibi"] = str(e)[:300]
        log(f"  bouées du large indisponibles : {e}")

    keep_silent(coast, offshore, meta)

    # Fiabilité mesurée sur les 30 derniers jours (archive) ; l'ajout du passage en cours se fait après le mélange (issue #1).
    now_local = pd.Timestamp.now(tz=config.TIMEZONE).tz_localize(None).floor("h")
    reliability = None
    try:
        reliability = history.reliability(now_local)
    except Exception as e:
        meta["errors"]["history"] = str(e)[:300]
        log(f"  archive illisible : {e}")

    log("Marées (calcul harmonique)")
    start = times[0][:10] + "T00:00"
    tide_ports = {}
    for port in sorted({s["tide_port"] for s in spots if s["tide_port"]}):
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
    corr = melange.correction(times, ratio, now)

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
        mix = melange.corrected(melange.blend(models, weights, d["marine"]["wave_height"], len(times)), corr)
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

    try:
        archive_pass(meta, gascogne, coast, offshore, bpts, weights, marc_buoys if marc_data else None, times, ratio, now, gen_utc)
    except Exception as e:   # l'archive ne bloque jamais la publication
        meta["errors"]["history"] = str(e)[:300]
        log(f"  archive indisponible : {e}")

    meta["wave_models"] = [{"key": k, "label": labels[k]} for k in labels]
    meta["wind_models"] = [{"key": k, "label": l} for k, l, _a in config.WIND_MODELS]
    meta["buoy_correction"] = ratio
    payload = {"meta": meta, "gascogne": gascogne, "coast": coast, "offshore": offshore, "tide_coef": tide_coef, "reliability": reliability, "buoy_stats": history.buoy_stats(), "spots": out_spots}
    # consommation Open-Meteo de ce passage et provenance des prévisions (issue #7) ; mode dégradé signalé
    meta["api"] = omcache.summary()
    # heure de COLLECTE des prévisions (≠ heure de génération en mode dégradé ; ≠ heure du run du modèle)
    meta["forecast_fetched"] = meta["api"]["openmeteo"]["forecast_fetched"]
    try:
        meta["api"]["today"] = omcache.persist_daily(meta["api"], meta["generated"])
    except Exception as e:   # compteurs : jamais bloquants
        meta["errors"]["api_compteurs"] = str(e)[:200]
    degraded = {g: s for g, s in omcache.STATE.items() if s.get("source") == "cache-dégradé"}
    if degraded:
        meta["errors"]["openmeteo_cache"] = "prévisions réutilisées (Open-Meteo indisponible) : " + ", ".join(f"{g} {s['age_h']} h" for g, s in sorted(degraded.items()))
    u = meta["api"]["openmeteo"]
    log(f"Open-Meteo : {u['requests']} requêtes, {u['attempts']} tentatives ({u['attempts_429']} refus 429, {u['attempts_5xx']} 5xx, "
        f"{u['attempts_network']} réseau), {u['points']} points, {u['calls_if_per_request']} appels (par requête) / "
        f"{u['calls_if_per_point']} (par point) acceptés ; collecte des prévisions {u['forecast_fetched']}")
    if omcache.CHANGED:
        omcache.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (omcache.CACHE_DIR / "CHANGED").write_text(meta["generated"], encoding="utf-8")
    # CONTRAT HORAIRE v2 (issue #2) : tout ce qui est publié à partir d'ici (forecast.json, appli, pages, health.json) porte
    # des instants ISO 8601 avec décalage, à l'heure locale du lieu. Les calculs ci-dessus restent faits sur les heures internes.
    payload["_model_offsets"] = model_offsets
    payload["_generated_utc"] = gen_utc.isoformat()
    payload = timefmt.localize(payload, spots, openmeteo.LAST_OFFSET_S, openmeteo.LAST_SUN_OFFSET_S)
    meta = payload["meta"]
    config.OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:  # données allégées pour l'application mobile : jamais bloquant, et AVANT forecast.json pour que l'erreur y figure
        log(f"Appli mobile : {appdata.generate(spots, payload)} fiches de spots (web/data/app/)")
    except Exception as e:
        meta["errors"]["appdata"] = str(e)[:300]
        log(f"  données de l'appli non générées : {e}")
    meta["errors"] = {k: safe.public_error(v) for k, v in meta["errors"].items()}   # fichier public : jamais d'adresse complète ni de clé
    config.OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    try:
        n = seo.generate(payload)
        log(f"SEO : {n} pages de spots + sitemap.xml + robots.txt ({config.SITE_URL})")
    except Exception as e:  # signalé dans forecast.json et health.json ; le contrôle de publication décide (tools/check_site.py)
        meta["errors"]["seo"] = str(e)[:300]
        log(f"  pages SEO non générées : {e}")
    meta["errors"].update(seo.LAST_ERRORS)
    # forecast.json réécrit avec les erreurs de génération (avant, l'erreur SEO n'y figurait jamais : le fichier était déjà écrit)
    meta["errors"] = {k: safe.public_error(v) for k, v in meta["errors"].items()}   # fichier public : jamais d'adresse complète ni de clé
    config.OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    write_health(payload, spots)
    size = config.OUTPUT_FILE.stat().st_size / 1024
    log(f"OK : {config.OUTPUT_FILE} ({size:.0f} Ko) · erreurs : {list(meta['errors']) or 'aucune'}")


if __name__ == "__main__":
    # tout ce que le robot affiche (journaux GitHub) passe par safe.redact : clés, en-têtes, identifiants masqués
    sys.stdout, sys.stderr = safe.RedactingStream(sys.stdout), safe.RedactingStream(sys.stderr)
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
