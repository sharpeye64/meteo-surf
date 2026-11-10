"""Archive « prévision contre réalité » de la houle au large, pour afficher une fiabilité mesurée.

À chaque passage du robot (toutes les 3 h) on garde :
- la hauteur de vagues prévue par chaque modèle au point de la bouée Gascogne, pour les 96 prochaines heures ;
- les mesures horaires de la bouée.
On compare ensuite, pour chaque modèle et pour leur mélange, la prévision faite 24, 48, 72 et 96 h plus tôt
à la mesure réelle de l'heure visée.

Stockage : fichiers JSON dans `history/` (branche git « history » dans GitHub Actions, voir update.yml).
  history/runs/AAAA-MM.jsonl : une ligne par passage {"issued", "t0", "models": {clé: [Hs…]}}
  history/obs/AAAA-MM.json   : {"AAAA-MM-JJTHH:00": {"hs": m, "tp": s}}
Limite assumée : la bouée est au large (45,2° N, 5° O), elle vérifie les modèles de houle, pas le détail côtier.
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

LEADS = (24, 48, 72, 96)
WINDOW_DAYS = 30
MIN_FOR_STATS = 12  # nombre minimal de comparaisons à un horizon donné pour afficher un chiffre


def history_dir():
    return Path(os.environ.get("METEO_HISTORY_DIR") or config.HISTORY_DIR)


def archiving_enabled():
    return os.environ.get("METEO_ARCHIVE") == "1"


def _read_runs(d, since):
    runs = []
    for f in sorted((d / "runs").glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("issued", "") >= since:
                runs.append(r)
    return runs


def _read_obs(d):
    obs = {}
    for f in sorted((d / "obs").glob("*.json")):
        try:
            obs.update(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            continue
    return obs


def record(issued, forecasts, obs_hourly, d=None):
    """issued : heure locale « AAAA-MM-JJTHH:00 » ; forecasts : {clé: {"t0": heure, "hs": [Hs…]}} ;
    obs_hourly : [{"t": heure locale, "hs": m, "tp": s|None}]."""
    d = Path(d) if d else history_dir()
    (d / "runs").mkdir(parents=True, exist_ok=True)
    (d / "obs").mkdir(parents=True, exist_ok=True)
    if forecasts:
        t0s = {v["t0"] for v in forecasts.values()}
        line = {"issued": issued, "t0": sorted(t0s)[0],
                "models": {k: [None if x is None else round(float(x), 2) for x in v["hs"]] for k, v in forecasts.items()}}
        f = d / "runs" / f"{issued[:7]}.jsonl"
        with open(f, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, separators=(",", ":")) + "\n")
    by_month = {}
    for o in obs_hourly or []:
        if o.get("hs") is not None:
            by_month.setdefault(o["t"][:7], {})[o["t"][:13] + ":00"] = {"hs": round(float(o["hs"]), 2),
                                                                         "tp": None if o.get("tp") is None else round(float(o["tp"]), 1)}
    for month, rows in by_month.items():
        f = d / "obs" / f"{month}.json"
        cur = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        cur.update(rows)
        f.write_text(json.dumps(dict(sorted(cur.items())), separators=(",", ":")), encoding="utf-8")


def _mix(models, k):
    weights = {key: w for key, _l, w, _n in config.WAVE_MODELS}
    num = den = 0.0
    for key, arr in models.items():
        if k < len(arr) and arr[k] is not None:
            w = weights.get(key, 0.1)
            num += arr[k] * w
            den += w
    return num / den if den else None


def _stats(errs):
    e = np.array(errs, dtype=float)
    return {"n": int(len(e)), "mae": round(float(np.mean(np.abs(e))), 2), "bias": round(float(np.mean(e)), 2),
            "within30": round(float(np.mean(np.abs(e) <= 0.3)), 2)}


def reliability(now_local, d=None):
    """Écart prévision − mesure de la houle au large, par horizon et par modèle, sur les 30 derniers jours."""
    d = Path(d) if d else history_dir()
    out = {"ref": "Bouée Gascogne, au large", "window_days": WINDOW_DAYS, "leads": {}, "status": "collecting",
           "since": None, "days_collected": 0}
    if not (d / "runs").exists():
        return out
    now = pd.Timestamp(now_local)
    since = (now - pd.Timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%dT%H:00")
    runs, obs = _read_runs(d, since), _read_obs(d)
    if runs:
        out["since"] = runs[0]["issued"][:10]
        out["days_collected"] = (now.normalize() - pd.Timestamp(runs[0]["issued"]).normalize()).days + 1
    errs = {L: {} for L in LEADS}
    for r in runs:
        t0 = pd.Timestamp(r["t0"])
        for L in LEADS:
            k = L + int(round((pd.Timestamp(r["issued"]) - t0) / pd.Timedelta("1h")))  # indice de l'heure issued + L
            if k < 0:
                continue
            target = (t0 + pd.Timedelta(hours=k)).strftime("%Y-%m-%dT%H:00")
            o = obs.get(target)
            if not o:
                continue
            for key, arr in list(r["models"].items()) + [("mix", None)]:
                v = _mix(r["models"], k) if key == "mix" else (arr[k] if k < len(arr) else None)
                if v is not None:
                    errs[L].setdefault(key, []).append(v - o["hs"])
    for L in LEADS:
        e = errs[L]
        if len(e.get("mix", [])) >= MIN_FOR_STATS:
            out["leads"][str(L)] = {"mix": _stats(e["mix"]),
                                    "models": {k: _stats(v) for k, v in e.items() if k != "mix" and len(v) >= MIN_FOR_STATS}}
    if out["leads"]:
        out["status"] = "ok"
    return out


# ---------- Bouées côtières (CANDHIS) : de quoi apprendre, plus tard, « houle + période → taille près du bord » ----------
#   history/coast_runs/AAAA-MM.jsonl : une ligne par passage {"issued", "t0", "b": {id: {"hs": [...], "tp": [...], "dir": [...]}}}
#   history/coast_obs/AAAA-MM.json   : {id: {"AAAA-MM-JJTHH:00": {"hs", "hmax", "tp", "dir", "sst"}}}
def record_coast(issued, forecasts, buoys, d=None):
    """forecasts : {id: {"t0", "hs", "tp", "dir"}} ; buoys : liste de bouées telles que renvoyées par candhis.fetch_all()."""
    d = Path(d) if d else history_dir()
    (d / "coast_runs").mkdir(parents=True, exist_ok=True)
    (d / "coast_obs").mkdir(parents=True, exist_ok=True)
    if forecasts:
        t0 = sorted(v["t0"] for v in forecasts.values())[0]
        line = {"issued": issued, "t0": t0, "b": {k: {"hs": v["hs"], "tp": v.get("tp"), "dir": v.get("dir")} for k, v in forecasts.items()}}
        with open(d / "coast_runs" / f"{issued[:7]}.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, separators=(",", ":")) + "\n")
    by_month = {}
    for b in buoys or []:
        for o in b.get("obs") or []:
            if o.get("hs") is None:
                continue
            row = {k: o.get(k) for k in ("hs", "hmax", "tp", "dir", "sst")}
            by_month.setdefault(o["t"][:7], {}).setdefault(b["id"], {})[o["t"][:13] + ":00"] = row
    for month, per_buoy in by_month.items():
        f = d / "coast_obs" / f"{month}.json"
        cur = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        for bid, rows in per_buoy.items():
            cur.setdefault(bid, {}).update(rows)
            cur[bid] = dict(sorted(cur[bid].items()))
        f.write_text(json.dumps(cur, separators=(",", ":")), encoding="utf-8")


def coast_summary(d=None):
    """Combien de mesures côtières sont archivées (par bouée), et depuis quand."""
    d = Path(d) if d else history_dir()
    out = {}
    for f in sorted((d / "coast_obs").glob("*.json")) if (d / "coast_obs").exists() else []:
        for bid, rows in json.loads(f.read_text(encoding="utf-8")).items():
            o = out.setdefault(bid, {"n": 0, "first": None, "last": None})
            o["n"] += len(rows)
            ks = sorted(rows)
            if ks:
                o["first"] = min(filter(None, [o["first"], ks[0]]))
                o["last"] = max(filter(None, [o["last"], ks[-1]]))
    runs = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in (d / "coast_runs").glob("*.jsonl")) if (d / "coast_runs").exists() else 0
    return {"buoys": out, "runs": runs}


def buoy_stats(d=None, days_shown=30):
    """Records et moyennes par bouée, calculés sur toutes les mesures archivées (coast_obs).
    Retourne {id: {"since", "n", "days", "hs_max", "hs_max_t", "hmax_max", "hmax_max_t", "hs_mean", "tp_mean",
    "sst_min", "sst_max", "sst_mean", "daily": [[jour, Hs max du jour], …]}}. Rien si pas d'archive."""
    d = Path(d) if d else history_dir()
    out = {}
    folder = d / "coast_obs"
    if not folder.exists():
        return out
    rows = {}
    for f in sorted(folder.glob("*.json")):
        try:
            for bid, r in json.loads(f.read_text(encoding="utf-8")).items():
                rows.setdefault(bid, {}).update(r)
        except ValueError:
            continue
    for bid, r in rows.items():
        r = {t: v for t, v in sorted(r.items()) if v.get("hs") is not None}
        if not r:
            continue

        def mean(k):
            v = [x[k] for x in r.values() if x.get(k) is not None]
            return round(sum(v) / len(v), 2) if v else None

        tmax = max(r, key=lambda t: r[t]["hs"])
        hm = {t: v["hmax"] for t, v in r.items() if v.get("hmax") is not None}
        tm = max(hm, key=hm.get) if hm else None
        sst = [x["sst"] for x in r.values() if x.get("sst") is not None]
        daily = {}
        for t, v in r.items():
            daily[t[:10]] = max(daily.get(t[:10], 0), v["hs"])
        out[bid] = {"since": min(r)[:10], "n": len(r), "days": len(daily), "hs_max": r[tmax]["hs"], "hs_max_t": tmax,
                    "hmax_max": hm[tm] if tm else None, "hmax_max_t": tm, "hs_mean": mean("hs"), "tp_mean": mean("tp"),
                    "sst_min": min(sst) if sst else None, "sst_max": max(sst) if sst else None, "sst_mean": mean("sst"),
                    "daily": [[k, round(v, 1)] for k, v in list(daily.items())[-days_shown:]]}
    return out
