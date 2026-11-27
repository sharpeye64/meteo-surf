"""Archive v2 aux points des bouées (issue #1) : modèles individuels, mélanges brut et corrigé, provenance.

Une ligne par passage d'archive dans `history/buoy_runs/AAAA-MM.jsonl` (ajout seul, jamais de réécriture). Format :
  {"v": 2, "scope": "points des bouées", "issued", "generated", "t0", "step_h": 1, "n", "engine": {...},
   "weights": {clé: poids}, "correction": {...}, "sources": {clé: provenance}, "missing": {clé: raison},
   "b": {id: {"lat", "lon", "tz", "models": {clé: [Hs] | null}, "marc": {"hs", "cell", "km"} | null,
              "base": [Hs best match] | null, "mix_raw": [Hs], "mix": [Hs]}}}
- Instants : ISO 8601 avec décalage (contrat horaire v2, docs/heures.md) ; l'heure k vaut t0 + k heures EXACTES.
- Valeur absente = null, modèle absent = null + raison dans « missing ». Jamais de valeur inventée.
- « sources » : instant réel de collecte, cache ou non, et cycle du modèle (run) INFÉRÉ des métadonnées Open-Meteo relues
  avant et après la collecte (la réponse n'indique pas son run) ; null + raison sinon. Le « best match » n'a pas de run.
- « correction » : ratio, départ exact (heure murale et décalage de l'axe, tels que le calcul les compare) et facteur de chaque
  heure : le mélange corrigé se recalcule sans ambiguïté, même autour d'un changement d'heure.
- CE N'EST PAS la prévision publiée aux spots : c'est le même calcul (pipeline/melange.py), appliqué aux points des bouées,
  pour comparer prévision et mesure. Les mesures sont dans coast_obs/ et obs/ (inchangés).
"""
import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config, melange, openmeteo, timefmt

MARC_MAX_KM = 6.0   # maille MARC acceptée pour une bouée (grille ≈ 3,7 km) : au-delà, la bouée est hors de la grille
HOURS = 97
META_NAME = {"ewam": "dwd_ewam", "ecmwf_wam": "ecmwf_wam025", "gfs_wave": "ncep_gfswave025"}   # nom d'API → nom des métadonnées


def engine():
    sha = (os.environ.get("GITHUB_SHA") or "")[:7] or None
    return {"melange": melange.VERSION, "code": sha, "correction_hours": config.BUOY_CORRECTION_HOURS,
            "ratio_bounds": list(config.BUOY_RATIO_BOUNDS), "max_age_h": config.BUOY_MAX_AGE_HOURS}


def _iso_ts(ts):
    return None if ts is None else timefmt.fmt(datetime.fromtimestamp(ts, timezone.utc), timefmt.PARIS)


def _ukey(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H")


def _by_instant(times, values, offset_s):
    """{instant UTC « AAAA-MM-JJTHH »: valeur} : chaque réponse Open-Meteo a SON décalage (cache d'avant un changement d'heure)."""
    return {_ukey(timefmt.from_fixed(t, offset_s)): v for t, v in zip(times or [], values or [])}


def grid(issued_utc, hours=HOURS):
    """Axe de l'archive : clés UTC des `hours` heures exactes à partir du passage."""
    return [_ukey(issued_utc + timedelta(hours=k)) for k in range(hours)]


def on_grid(resp_point, var, offset_s, keys):
    """Série d'une réponse replacée sur l'axe par INSTANT, coupée là où la réponse s'arrête (comme l'ancien découpage)."""
    h = resp_point["hourly"]
    by = _by_instant(h["time"], h.get(var), offset_s)
    vals = [by.get(k) for k in keys]
    last = max((i for i, k in enumerate(keys) if k in by), default=-1)
    return vals[:last + 1]


def _with_offset(wall, offset_s):
    sign, m = ("+" if offset_s >= 0 else "-"), abs(int(offset_s)) // 60
    return f"{wall}{sign}{m // 60:02d}:{m % 60:02d}"


def _km(a, b):
    r = math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot((a[0] - b[0]) * 111.2, (a[1] - b[1]) * 111.2 * r)


def _r2(v):
    return None if v is None else round(float(v), 2)


def _source(group, api=None):
    from . import omcache
    st = omcache.STATE.get(group) or {}
    d = {"group": group, "api": api, "fetched": _iso_ts(st.get("fetched")), "from": st.get("source")}
    if group not in omcache.CYCLES:
        d.update(run=None, run_note="requête non effectuée")
        return d
    cyc = omcache.CYCLES.get(group)
    if api is None:   # best match : pas de run unique (https://open-meteo.com/en/docs/model-updates)
        d.update(run=None, run_note="best match : non lié à un run unique")
        return d
    c = (cyc or {}).get(META_NAME.get(api, api))
    if cyc is None:
        note = "cycle inconnu (réponse en cache d'avant l'archive v2)"
    elif c is None:
        note = "modèle absent des métadonnées surveillées"
    else:
        note = c.get("note")
    d["run"] = _iso_ts(c["init"]) if c and c.get("init") else None
    d["run_basis"] = omcache.CYCLE_BASIS if d["run"] else None
    d["run_note"] = None if d["run"] else (note or "métadonnées illisibles")
    d["run_available"] = _iso_ts(c.get("available")) if c else None
    d["native_step_h"] = round(c["step_s"] / 3600, 2) if c and c.get("step_s") else None
    return d


def build_line(issued_utc, generated_utc, fc, points, weights, marc_rows, marc_axis, corr_info):
    """Ligne d'archive v2. issued_utc : début de l'heure du passage (datetime UTC). fc : openmeteo.buoy_forecasts().
    marc_rows : {id: {"hs", "cell"}} sur l'axe marc_axis (heures Open-Meteo au décalage openmeteo.LAST_OFFSET_S), ou None.
    corr_info : {"ratio" (appliqué), "ratio_measured", "start" (pd.Timestamp sans fuseau, comme build.py), "t_obs", "status"}."""
    keys = grid(issued_utc)
    axis_off = openmeteo.LAST_OFFSET_S or 0
    # heures « murales » au décalage de l'axe des spots : la correction est calculée EXACTEMENT comme pour la prévision publiée
    wall = [openmeteo.shift_str((issued_utc + timedelta(hours=k)).strftime("%Y-%m-%dT%H:00"), axis_off) for k in range(HOURS)]
    start = corr_info.get("start")
    corr = melange.correction(wall, corr_info.get("ratio"), start)
    ref = fc["ref"]
    ref_off = openmeteo.offset_of(ref) if ref else None
    mods = {k: (api, r, openmeteo.offset_of(r)) for k, (api, r) in fc["models"].items()}
    b = {}
    for i, p in enumerate(points):
        base = None
        if ref:
            s = openmeteo.valid_hs(on_grid(ref[i], "wave_height", ref_off, keys))
            base = [_r2(v) for v in s] + [None] * (HOURS - len(s))
        models = {}
        for k, (_api, r, off) in mods.items():
            s = openmeteo.valid_hs(on_grid(r[i], "wave_height", off, keys))
            models[k] = ([_r2(v) for v in s] + [None] * (HOURS - len(s))) if any(v is not None for v in s) else None
        for k in fc["missing"]:
            if k != "base":
                models[k] = None
        marc = None
        m = (marc_rows or {}).get(p["id"])
        if m and m.get("cell"):
            km = _km((p["lat"], p["lon"]), m["cell"])
            if km <= MARC_MAX_KM:
                s = [_by_instant(marc_axis, m["hs"], axis_off).get(x) for x in keys]
                if any(v is not None for v in s):
                    marc = {"hs": [_r2(v) for v in s], "cell": m["cell"], "km": round(km, 1)}
        used = {k: v for k, v in models.items() if v}
        if marc and "marc" in weights:
            used = {"marc": marc["hs"], **used}   # même ordre que build.py (MARC d'abord)
        raw = melange.blend(used, weights, base, HOURS)
        fin = melange.corrected(raw, corr)
        tz = "Europe/Paris" if p["id"] == "gascogne" else timefmt.place_tz(p["lat"], p["lon"])
        b[p["id"]] = {"lat": p["lat"], "lon": p["lon"], "tz": tz, "models": models, "marc": marc, "base": base,
                      "mix_raw": [_r2(v) for v in raw], "mix": [_r2(v) for v in fin]}
    sources = {"base": _source("buoys_marine")}
    for k, (api, _r, _o) in mods.items():
        sources[k] = _source(f"buoys_wave_{k}", api)
    if marc_rows is not None:
        sources["marc"] = {"api": "Ifremer MARC (OPeNDAP)", "fetched": timefmt.fmt(generated_utc, timefmt.PARIS), "run": None,
                           "run_note": "série agrégée sans heure de run", "max_km": MARC_MAX_KM}
    missing = dict(fc["missing"])
    if marc_rows is None:
        missing["marc"] = "MARC indisponible pour ce passage"
    correction = {k: corr_info.get(k) for k in ("ratio", "ratio_measured", "status")}
    correction.update({
        "t_obs": timefmt.fmt(timefmt.parse(corr_info["t_obs"]), timefmt.PARIS) if corr_info.get("t_obs") else None,
        "hours": config.BUOY_CORRECTION_HOURS,
        # départ EXACT tel que le calcul le compare : l'heure murale de départ écrite AVEC le décalage de l'axe des prévisions
        # (« start_axis »), donc un instant ISO 8601 exact ; « start » = le même instant à l'heure de Paris
        "start_axis": _with_offset(start.strftime("%Y-%m-%dT%H:%M"), axis_off) if start is not None else None,
        "axis_offset_s": axis_off,
        "start": timefmt.fmt(timefmt.from_fixed(start.strftime("%Y-%m-%dT%H:%M"), axis_off), timefmt.PARIS) if start is not None else None,
        "factors": [round(c, 6) for c in corr],
    })
    return {"v": 2, "scope": "points des bouées (pas la prévision publiée aux spots)",
            "issued": timefmt.fmt(issued_utc, timefmt.PARIS), "generated": timefmt.fmt(generated_utc, timefmt.PARIS),
            "t0": timefmt.fmt(issued_utc, timefmt.PARIS), "step_h": 1, "n": HOURS, "engine": engine(),
            "weights": {k: weights[k] for k in (["marc"] if "marc" in weights else []) + [k for k in fc["models"]] if k in weights},
            "correction": correction, "sources": sources, "missing": missing, "b": b}


# ---------- anciens formats (runs/, coast_runs/), alimentés depuis les mêmes requêtes, sur la grille d'instants ----------
def legacy_gascogne(fc, ids, issued_utc, issued_old):
    """{clé: {"t0", "hs"}} au point de Gascogne, comme l'ancien models_at_point : t0 = heure de Paris du passage (sans décalage,
    format d'avant), valeurs aux heures EXACTES t0 + k (une réponse en cache d'un autre décalage est réalignée)."""
    out, j, keys = {}, ids.index("gascogne"), grid(issued_utc)
    for k, (_api, r) in fc["models"].items():
        hs = openmeteo.valid_hs(on_grid(r[j], "wave_height", openmeteo.offset_of(r), keys))
        if any(x is not None for x in hs):
            out[k] = {"t0": issued_old, "hs": hs}
    return out


def legacy_coast(fc, ids, live, issued_utc, issued_old):
    """{id: {"t0", "hs", "tp", "dir"}} best match aux bouées vivantes, comme l'ancien coast_forecast, sur la grille d'instants."""
    ref = fc["ref"]
    if not ref:
        return {}
    off, keys, out = openmeteo.offset_of(ref), grid(issued_utc), {}
    for j, bid in enumerate(ids):
        if bid not in live:
            continue
        hs = openmeteo.valid_hs(on_grid(ref[j], "wave_height", off, keys))
        if not any(x is not None for x in hs):
            continue
        sl = lambda v: [None if x is None else round(float(x), 2) for x in on_grid(ref[j], v, off, keys)]
        out[bid] = {"t0": issued_old, "hs": hs, "tp": sl("wave_period"), "dir": sl("wave_direction")}
    return out


def _issued_in(f, issued):
    """Passage déjà archivé ? (le robot passe 2 fois dans l'heure d'archive : avant ce lot, 40 % des passages étaient en double)"""
    if not f.exists():
        return False
    needle = f'"issued":"{issued}"'
    with open(f, encoding="utf-8") as fh:
        return any(needle in line for line in fh)


def path(d, issued):
    return Path(d) / "buoy_runs" / f"{issued[:7]}.jsonl"


def already(d, issued):
    return _issued_in(path(d, issued), issued)


def write(d, line):
    """Ajoute la ligne (sans doublon). Retourne la taille écrite en octets, ou 0 si le passage était déjà archivé."""
    f = path(d, line["issued"])
    if _issued_in(f, line["issued"]):
        return 0
    f.parent.mkdir(parents=True, exist_ok=True)
    s = json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n"
    with open(f, "a", encoding="utf-8") as fh:
        fh.write(s)
    return len(s.encode("utf-8"))


def read(d, since=None):
    """Lecture des lignes v2 (doublons ignorés : premier passage gardé)."""
    out, seen = [], set()
    folder = Path(d) / "buoy_runs"
    for f in sorted(folder.glob("*.jsonl")) if folder.exists() else []:
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("v") != 2 or r["issued"] in seen or (since and timefmt.parse(r["issued"]) < timefmt.parse(since)):
                continue
            seen.add(r["issued"])
            out.append(r)
    return out
