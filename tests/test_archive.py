"""Archive v2 aux points des bouées (issue #1), sans réseau.

Vérifie : anciennes archives conservées à l'octet près et lues sans doublon ; un seul enregistrement par heure ; modèles
individuels, MARC, mélanges brut et corrigé recalculables à l'identique ; valeurs absentes explicites ; instants avec décalage
(contrat horaire v2), y compris une réponse en cache d'avant un changement d'heure ; provenance et cycles des modèles sans
rien inventer ; prévision publiée inchangée (même calcul que l'ancien code de build.py).
Lancer : python -m tests.test_archive
"""
import hashlib
import json
import os
import random
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

os.environ["METEO_CACHE_DIR"] = tempfile.mkdtemp()   # cache de test, avant l'import d'omcache
os.environ.pop("GITHUB_SHA", None)
from pipeline import archive, build, config, history, melange, omcache, openmeteo, timefmt as T  # noqa: E402

fails = []


def eq(name, got, want):
    ok = got == want
    print(f"[{'OK' if ok else 'ÉCHEC'}] {name}" + ("" if ok else f" : obtenu {got!r}, attendu {want!r}"))
    if not ok:
        fails.append(name)


# ---------- 1. Le calcul extrait (melange.py) donne EXACTEMENT l'ancien calcul de build.py ----------
def old_mix(models, weights, base, times, ratio, now):
    corr = [1.0] * len(times)
    if ratio:
        for j, t in enumerate(times):
            dt = (pd.Timestamp(t) - now) / pd.Timedelta("1h")
            if 0 <= dt <= config.BUOY_CORRECTION_HOURS:
                corr[j] = 1 + (ratio - 1) * (1 - dt / config.BUOY_CORRECTION_HOURS)
    mix = []
    for j in range(len(times)):
        num = den = 0.0
        for k, arr in models.items():
            v = arr[j] if j < len(arr) else None
            if v is not None:
                num += v * weights.get(k, 0.1)
                den += weights.get(k, 0.1)
        val = num / den if den else base[j]
        mix.append(None if val is None else val * corr[j])
    return mix


rnd = random.Random(1)
times = [(datetime(2026, 11, 27) + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(168)]
W = {"marc": 0.3, "mfwam": 0.25, "ewam": 0.25, "ecmwf": 0.15, "gfs": 0.05, "autre": None}
W.pop("autre")
same = True
for trial in range(200):
    models = {k: [None if rnd.random() < 0.2 else round(rnd.uniform(0.2, 4), 2) for _ in range(rnd.choice([150, 168]))]
              for k in rnd.sample(list(W) + ["inconnu"], rnd.randint(0, 5))}
    base = [None if rnd.random() < 0.1 else round(rnd.uniform(0.2, 4), 2) for _ in times]
    ratio = rnd.choice([None, 0.8, 1.2, 1.35])
    now = pd.Timestamp(times[rnd.randint(0, 40)])
    new = melange.corrected(melange.blend(models, W, base, len(times)), melange.correction(times, ratio, now))
    same &= new == old_mix(models, W, base, times, ratio, now)
eq("1. mélange extrait = ancien calcul, à l'identique (200 tirages, valeurs manquantes, repli, correction)", same, True)

# ---------- 2. Anciennes archives (format d'avant #1, AVEC les doublons vus en production) ----------
d = Path(tempfile.mkdtemp())
(d / "runs").mkdir(); (d / "coast_runs").mkdir(); (d / "obs").mkdir(); (d / "coast_obs").mkdir()
L = lambda issued, v: {"issued": issued, "t0": issued, "models": {"mfwam": [v] * 97, "ecmwf": [v + 0.1] * 97}}
old_runs = [L("2026-11-20T09:00", 1.0), L("2026-11-20T09:00", 1.05), L("2026-11-20T12:00", 1.2)]
(d / "runs" / "2026-11.jsonl").write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in old_runs), encoding="utf-8")
C = lambda issued: {"issued": issued, "t0": issued, "b": {"03302": {"hs": [1.0] * 97, "tp": [9.0] * 97, "dir": [290.0] * 97}}}
(d / "coast_runs" / "2026-11.jsonl").write_text("".join(json.dumps(C(i), separators=(",", ":")) + "\n" for i in
                                                       ("2026-11-20T09:00", "2026-11-20T09:00", "2026-11-20T12:00")), encoding="utf-8")
(d / "obs" / "2026-11.json").write_text(json.dumps({"2026-11-20T09:00": {"hs": 1.0, "tp": 12}}), encoding="utf-8")
(d / "coast_obs" / "2026-11.json").write_text(json.dumps({"03302": {"2026-11-20T09:00": {"hs": 1.1, "hmax": 2, "tp": 9, "dir": 290, "sst": 15}}}), encoding="utf-8")
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
before = {f: (f.read_bytes(), sha(f)) for f in d.rglob("*") if f.is_file()}

eq("2. anciens passages lus sans doublon (runs)", [r["issued"] for r in history._read_runs(d, "2026-11-01")], ["2026-11-20T09:00", "2026-11-20T12:00"])
eq("2. premier des doublons gardé", history._read_runs(d, "2026-11-01")[0]["models"]["mfwam"][0], 1.0)
eq("2. anciens passages côtiers lus sans doublon", len(history.read_coast_runs(d)), 2)
eq("2. bilan côtier sans doublon", history.coast_summary(d)["runs"], 2)

# ---------- 3. Deux passages d'archive dans la même heure (cas réel : passages de 09:00 et 09:30 UTC) ----------
PTS = openmeteo.buoy_points()
NOW = datetime.now(timezone.utc)
MID = (NOW.astimezone(T.zone(T.PARIS)) - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)   # axe Open-Meteo (veille, minuit)
OFF = int(MID.utcoffset().total_seconds())
FACT = {"meteofrance_wave": 1.0, "ecmwf_wam": 0.9, "ncep_gfswave025": 0.8}
calls = []


def hs_at(utc_dt, f, j):   # valeur simulée = fonction de l'INSTANT (pour vérifier l'alignement)
    return round(f * (1.0 + 0.01 * (int(utc_dt.timestamp() // 3600) % 50) + 0.001 * j), 3)


FAIL = set()      # requêtes à faire échouer (panne) : "best match" ou un nom de modèle
ON_FETCH = {}     # action déclenchée PENDANT une requête (ex. : un nouveau run publié pendant la collecte)


def fake_get(url, params, tries=5):
    calls.append(params.get("models", "best match"))
    m = params.get("models")
    if params.get("models", "best match") in FAIL:
        raise RuntimeError("Open-Meteo : échec après 5 essais (HTTP 503)")
    if m in ON_FETCH:
        ON_FETCH.pop(m)()
    if m in ("ewam", "dwd_ewam"):
        raise ValueError("modèle refusé")   # EWAM absent : doit être nul et expliqué
    f = FACT.get(m, 1.1)
    # ECMWF : réponse « d'avant un changement d'heure » (décalage différent, heures écrites décalées d'autant)
    off = OFF + (3600 if m == "ecmwf_wam" else 0)
    n = len(str(params["latitude"]).split(","))
    lats = [float(x) for x in str(params["latitude"]).split(",")]
    out = []
    for j in range(n):
        utc0 = MID.astimezone(timezone.utc)
        tt = [utc0 + timedelta(hours=h) for h in range(24 * 6)]
        wall = [(x + timedelta(seconds=off)).strftime("%Y-%m-%dT%H:%M") for x in tt]
        hs = [hs_at(x, f, j) for x in tt]
        if m == "ncep_gfswave025" and lats[j] == config.GASCOGNE["lat"]:
            hs = [0.0] * len(tt)   # maille « terre » au point de Gascogne : exclue (valid_hs), série nulle explicite
        hourly = {"time": wall, "wave_height": hs}
        if "wave_period" in params["hourly"]:
            hourly.update(wave_period=[9.0] * len(tt), wave_direction=[290.0] * len(tt))
        out.append({"utc_offset_seconds": off, "hourly": hourly})
    return out


openmeteo.get = fake_get
t_now = NOW.timestamp()
META = {"meteofrance_wave": {"last_run_availability_time": int(t_now - 3600), "last_run_initialisation_time": int(t_now - 6 * 3600),
                             "temporal_resolution_seconds": 10800},
        "ncep_gfswave025": {"last_run_availability_time": int(t_now - 60), "last_run_initialisation_time": int(t_now - 5 * 3600),
                            "temporal_resolution_seconds": 3600},
        "ecmwf_wam025": None}
omcache.model_meta = lambda kind, name, fresh=False: META.get(name, {"last_run_availability_time": int(t_now - 7200), "last_run_initialisation_time": int(t_now - 9 * 3600)})
omcache.reset()
openmeteo.LAST_OFFSET_S = OFF
os.environ["METEO_HISTORY_DIR"] = str(d)
os.environ["METEO_ARCHIVE"] = "1"
gen = pd.Timestamp(NOW).floor("min")
gas_obs_t = gen.tz_convert(config.TIMEZONE).tz_localize(None).floor("h") - pd.Timedelta(hours=2)
gascogne = {"ratio": 1.2, "latest": {"time": gas_obs_t.strftime("%Y-%m-%dT%H:%M")}, "obs": [{"t": gas_obs_t.strftime("%Y-%m-%dT%H:%M"), "hs": 2.0, "tp": 12}]}
coast = [{"id": "03302", "obs": [{"t": gas_obs_t.strftime("%Y-%m-%dT%H:%M"), "hs": 1.3, "hmax": 2.1, "tp": 9, "dir": 290, "sst": 15}]},
         {"id": "06402", "obs": []}]
offshore = [{"id": "6200024", "obs": []}]
cf = next(p for p in PTS if p["id"] == "03302")
mtimes = [(MID.replace(tzinfo=None) + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(24 * 7)]
marc_buoys = {"03302": {"hs": [1.5] * len(mtimes), "cell": [cf["lat"] + 0.02, cf["lon"]]},          # 2,2 km : retenue
              "gascogne": {"hs": [1.5] * len(mtimes), "cell": [45.3, -2.4]}}                        # 200 km : hors grille
weights = {"marc": config.MARC_WEIGHT, **{k: w for k, _l, w, _n in config.WAVE_MODELS}}
meta = {"errors": {}}
for _ in range(2):
    build.archive_pass(meta, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen)
lines = archive.read(d)
eq("3. deux passages dans la même heure → une seule ligne v2", len(lines), 1)
eq("3. … et un seul ajout dans chaque ancien fichier", (len(history._read_runs(d, "2026-01-01")), len((d / "runs" / f"{gen.tz_convert(config.TIMEZONE):%Y-%m}.jsonl").read_text().splitlines()) - (3 if f"{gen.tz_convert(config.TIMEZONE):%Y-%m}" == "2026-11" else 0)),
   (3 if f"{gen.tz_convert(config.TIMEZONE):%Y-%m}" == "2026-11" else 1, 1))
eq("3. requêtes : une par modèle pour les 22 bouées (best match + MF + 2 noms EWAM refusés + ECMWF + GFS), 2e passage : aucune",
   calls, ["best match", "meteofrance_wave", "ewam", "dwd_ewam", "ecmwf_wam", "ncep_gfswave025"])
jl = {f: b for f, (b, _h) in before.items() if f.suffix == ".jsonl"}
eq("3. anciens passages (runs/, coast_runs/) conservés à l'octet près : ajouts seulement", all(f.read_bytes().startswith(b) for f, b in jl.items()), True)
def _flat(o, pre=""):
    return {pre + k: v for k, v in o.items()} if not any(isinstance(v, dict) and all(isinstance(x, dict) for x in v.values()) for v in o.values())         else {f"{k}/{t}": r for k, v in o.items() for t, r in v.items()}
old_obs = all(set(_flat(json.loads(b))) <= set(_flat(json.loads(f.read_text(encoding="utf-8")))) for f, (b, _h) in before.items() if f.suffix == ".json")
eq("3. anciennes mesures (obs/, coast_obs/) toutes conservées (fusion par heure, comme avant)", old_obs, True)

omcache.STATE["marine"] = {"source": "cache", "fetched": t_now + 600, "age_h": 0.0}   # prévision publiée collectée APRÈS l'archive
eq("3. l'heure de collecte des prévisions publiées ignore les groupes de l'archive",
   omcache.summary()["openmeteo"]["forecast_fetched"], T.fmt(datetime.fromtimestamp(t_now + 600, timezone.utc), T.PARIS))
omcache.STATE.pop("marine")

def replay_factors(line):
    """Facteurs de correction recalculés UNIQUEMENT depuis la ligne archivée (aucune donnée du passage)."""
    c = line["correction"]
    if not c["ratio"]:
        return [1.0] * line["n"]
    t0 = T.parse(line["t0"]).astimezone(timezone.utc)
    wall = [openmeteo.shift_str((t0 + timedelta(hours=k)).strftime("%Y-%m-%dT%H:00"), c["axis_offset_s"]) for k in range(line["n"])]
    return melange.correction(wall, c["ratio"], pd.Timestamp(c["start_axis"][:16]))


# ---------- 4. Contenu de la ligne v2 ----------
ln = lines[0]
issued_utc = gen.floor("h").to_pydatetime()
eq("4. t0 / issued : instant exact avec décalage", (T.parse(ln["t0"]) == issued_utc, ln["t0"][-6:] in ("+01:00", "+02:00")), (True, True))
eq("4. aucune heure sans décalage dans la ligne v2", T.naive_strings(ln), [])
eq("4. 22 bouées, 97 heures chacune", (len(ln["b"]), {len(b["base"]) for b in ln["b"].values()}), (22, {97}))
g = ln["b"]["gascogne"]
eq("4. modèle absent (EWAM refusé) : null partout + raison", (all(b["models"]["ewam"] is None for b in ln["b"].values()), "ewam" in ln["missing"]), (True, True))
eq("4. GFS sur maille « terre » à Gascogne : null explicite ; présent ailleurs", (g["models"]["gfs"], ln["b"]["03302"]["models"]["gfs"] is not None), (None, True))
j = [p["id"] for p in PTS].index("03302")
want = [round(hs_at(issued_utc + timedelta(hours=k), 0.9, j), 2) for k in range(97)]
eq("4. ECMWF en cache d'avant changement d'heure : aligné par INSTANT", ln["b"]["03302"]["models"]["ecmwf"], want)
eq("4. MARC retenu à 2 km du Cap Ferret, refusé à Gascogne (hors grille)", (ln["b"]["03302"]["marc"]["km"], g["marc"]), (2.2, None))
# mélanges recalculables à l'identique depuis les ingrédients archivés
ok_raw = ok_fin = True
for bid, b in ln["b"].items():
    used = {k: v for k, v in b["models"].items() if v}
    if b["marc"]:
        used = {"marc": b["marc"]["hs"], **used}
    raw = melange.blend(used, ln["weights"], b["base"], 97)
    ok_raw &= [None if v is None else round(v, 2) for v in raw] == b["mix_raw"]
    ok_fin &= [None if v is None else round(v, 2) for v in melange.corrected(raw, replay_factors(ln))] == b["mix"]
eq("4. mélange brut recalculé depuis l'archive = archivé", ok_raw, True)
eq("4. mélange corrigé recalculé (ratio, départ et décalage de l'axe archivés) = archivé", ok_fin, True)
eq("4. facteurs de correction archivés = facteurs recalculés", [round(x, 6) for x in replay_factors(ln)], ln["correction"]["factors"])
cfb = ln["b"]["03302"]
eq("4. correction : mélange corrigé ≠ brut au début, = brut après 24 h", (cfb["mix"][0] != cfb["mix_raw"][0], cfb["mix"][40] == cfb["mix_raw"][40]), (True, True))
eq("4. correction notée", (ln["correction"]["ratio"], ln["correction"]["status"], ln["correction"]["hours"]), (1.2, "appliquée", 24))
# provenance : cycle seulement s'il est connu et disponible au moment de la collecte, sinon null avec la raison
s = ln["sources"]
eq("4. MF-WAM : cycle des métadonnées Open-Meteo, pas de 3 h natif",
   (s["mfwam"]["run"] == T.fmt(datetime.fromtimestamp(int(t_now - 6 * 3600), timezone.utc), T.PARIS), s["mfwam"]["native_step_h"]), (True, 3.0))
eq("4. GFS publié < 10 min avant la collecte : cycle non affirmé", (s["gfs"]["run"], "10 min" in s["gfs"].get("run_note", "")), (None, True))
eq("4. ECMWF : métadonnées illisibles → cycle null", s["ecmwf"]["run"], None)
eq("4. best match : jamais de cycle", (s["base"]["run"], "best match" in s["base"]["run_note"]), (None, True))
eq("4. MARC : pas d'heure de run inventée", s["marc"]["run"], None)
eq("4. chaque cycle absent a sa raison ; chaque cycle présent est marqué « inféré »",
   (all(v.get("run_note") for v in s.values() if not v.get("run")), all("inféré" in v["run_basis"] for v in s.values() if v.get("run"))), (True, True))
eq("4. départ de la correction : instant exact, avec décalage", (T.parse(ln["correction"]["start_axis"]) == T.parse(ln["correction"]["start"]),
   ln["correction"]["start_axis"][-6:] == ("+01:00" if OFF == 3600 else "+02:00")), (True, True))
eq("4. version du moteur notée", ln["engine"]["melange"], melange.VERSION)
eq("4. pas la prévision publiée : périmètre écrit", ln["scope"].startswith("points des bouées"), True)

# ---------- 5. Anciens formats : même contenu qu'avant (mêmes règles de découpe) ----------
rec = [json.loads(x) for x in (d / "runs").glob("*.jsonl").__next__().read_text().splitlines()][-1]
eq("5. runs/ : Gascogne, modèles présents (GFS terre exclu comme avant)", sorted(rec["models"]), ["ecmwf", "mfwam"])
crec = history.read_coast_runs(d)[-1]
eq("5. coast_runs/ : bouées vivantes seulement, hauteur/période/direction", (sorted(crec["b"]), sorted(crec["b"]["03302"])), (["03302", "06402", "6200024"], ["dir", "hs", "tp"]))
eq("5. coast_runs/ : heure de départ au format d'avant (heure de Paris sans décalage)", T.NAIVE.match(crec["t0"]) is not None, True)
eq("5. mesures fusionnées", json.loads((d / "coast_obs" / f"{gas_obs_t:%Y-%m}.json").read_text())["03302"][gas_obs_t.strftime("%Y-%m-%dT%H:00")]["hs"], 1.3)

# ---------- 6. Lecture v2 : doublon ajouté à la main ignoré ; archive désactivée = rien d'écrit ----------
f = archive.path(d, ln["issued"])
with open(f, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(ln) + "\n")
eq("6. doublon v2 ignoré à la lecture", len(archive.read(d)), 1)
eq("6. write() refuse un doublon", archive.write(d, ln), 0)
os.environ["METEO_ARCHIVE"] = "0"
n_before = sum(1 for _ in d.rglob("*.jsonl"))
build.archive_pass(meta, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen + pd.Timedelta(hours=3))
eq("6. hors heure d'archive : rien d'écrit", (sum(1 for _ in d.rglob("*.jsonl")), len(archive.read(d))), (n_before, 1))

# ---------- 7. Fiabilité : un passage en double ne compte plus deux fois ----------
d3 = Path(tempfile.mkdtemp())
hours = [datetime(2026, 10, 1) + timedelta(hours=h) for h in range(24 * 8)]
history.record(None, None, [{"t": t.strftime("%Y-%m-%dT%H:%M"), "hs": 1.0} for t in hours], d3)
(d3 / "runs").mkdir(exist_ok=True)
with open(d3 / "runs" / "2026-10.jsonl", "w", encoding="utf-8") as fh:
    for k in range(20):
        iss = (datetime(2026, 10, 1) + timedelta(hours=3 * k)).strftime("%Y-%m-%dT%H:00")
        line = json.dumps({"issued": iss, "t0": iss, "models": {"mfwam": [1.5] * 97}}) + "\n"
        fh.write(line + (line.replace("1.5", "2.5") if k % 2 else ""))   # un passage sur deux en double (valeur différente)
rel = history.reliability("2026-10-07 00:00", d3)
eq("7. fiabilité : 20 passages uniques comptés, premier des doublons gardé", (rel["leads"]["24"]["mix"]["n"], rel["leads"]["24"]["mix"]["bias"]), (20, 0.5))

# ---------- 8. Anciens formats : mêmes sorties que l'ancien code, et alignés par INSTANT (revue PR #20, point 2) ----------
def old_slice(hourly, from_local, hours=97, extra=False):   # l'ancien découpage (models_at_point / coast_forecast, avant #1)
    t = hourly["time"]
    i = next((j for j, x in enumerate(t) if x >= from_local), None)
    hs = openmeteo.valid_hs(hourly["wave_height"][i:i + hours])
    out = {"t0": t[i], "hs": hs}
    if extra:
        sl = lambda k: [None if x is None else round(float(x), 2) for x in hourly.get(k, [])[i:i + hours]]
        out.update(tp=sl("wave_period"), dir=sl("wave_direction"))
    return out


ids = [p["id"] for p in PTS]
issued_old = gen.floor("h").tz_convert(config.TIMEZONE).tz_localize(None).strftime("%Y-%m-%dT%H:00")
fresh = {"ref": fake_get("", {"latitude": ",".join(str(p["lat"]) for p in PTS), "hourly": "wave_height,wave_period,wave_direction"}),
         "models": {"mfwam": ("meteofrance_wave", fake_get("", {"latitude": ",".join(str(p["lat"]) for p in PTS), "hourly": "wave_height", "models": "meteofrance_wave"})),
                    "ecmwf": ("ecmwf_wam", fake_get("", {"latitude": ",".join(str(p["lat"]) for p in PTS), "hourly": "wave_height", "models": "ecmwf_wam"}))},
         "missing": {}}
lg = archive.legacy_gascogne(fresh, ids, issued_utc, issued_old)
og = old_slice(fresh["models"]["mfwam"][1][ids.index("gascogne")]["hourly"], issued_old)
eq("8. runs/ : sortie identique à l'ancien code pour une réponse au décalage du moment", (lg["mfwam"]["t0"], lg["mfwam"]["hs"]), (og["t0"], og["hs"]))
lc = archive.legacy_coast(fresh, ids, {"03302"}, issued_utc, issued_old)["03302"]
oc = old_slice(fresh["ref"][ids.index("03302")]["hourly"], issued_old, extra=True)
eq("8. coast_runs/ : sortie identique à l'ancien code (hauteur, période, direction)", lc, oc)
want_g = [round(hs_at(issued_utc + timedelta(hours=k), 0.9, ids.index("gascogne")), 3) for k in range(97)]
old_naive = old_slice(fresh["models"]["ecmwf"][1][ids.index("gascogne")]["hourly"], issued_old)["hs"]
eq("8. réponse d'un autre décalage (cache d'avant changement d'heure) : ancien découpage décalé d'1 h, nouveau aligné par instant",
   (old_naive[1:] == want_g[:96], lg["ecmwf"]["hs"] == want_g), (True, True))
eq("8. ligne runs/ écrite par le passage = alignée par instant", rec["models"]["ecmwf"] == [round(v, 2) for v in want_g], True)

# ---------- 9. Provenance : collecte, cache, métadonnées avant / après (revue PR #20, point 1) ----------
w = [("marine", "a"), ("marine", "b"), ("marine", "c"), ("marine", "d"), ("marine", "e")]
mk = lambda av, ini: {"last_run_availability_time": av, "last_run_initialisation_time": ini}
st0 = 2_000_000_000
cy = omcache._cycles(w, {"a": mk(st0 - 3600, st0 - 7200), "b": None, "c": mk(st0 - 60, st0 - 7200), "d": mk(st0 - 3600, st0 - 7200), "e": mk(st0 + 5, st0)},
                     {"a": mk(st0 - 3600, st0 - 7200), "b": None, "c": mk(st0 - 60, st0 - 7200), "d": mk(st0 + 30, st0), "e": mk(st0 + 5, st0)}, st0)
eq("9. cycle affirmé seulement si stable avant et après la collecte",
   {k: (v["init"] is not None, (v["note"] or "")[:18]) for k, v in cy.items()},
   {"a": (True, ""), "b": (False, "métadonnées illisi"), "c": (False, "run publié moins d"), "d": (False, "nouveau run publié"),
    "e": (False, "run annoncé après ")})
# intégration : un nouveau run MF-WAM publié PENDANT la requête, cache désactivé (les métadonnées sont relues avant et après)
d4 = Path(tempfile.mkdtemp()); os.environ["METEO_HISTORY_DIR"] = str(d4); os.environ["METEO_ARCHIVE"] = "1"
omcache.ENABLED = False
omcache.reset(); calls.clear()
ON_FETCH["meteofrance_wave"] = lambda: META.update(meteofrance_wave={"last_run_availability_time": int(t_now - 30), "last_run_initialisation_time": int(t_now - 3 * 3600)})
build.archive_pass(meta, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen)
s4 = archive.read(d4)[0]["sources"]
eq("9. cache désactivé + nouveau run pendant la collecte : cycle non affirmé", (s4["mfwam"]["run"], "pendant la collecte" in s4["mfwam"]["run_note"]), (None, True))
omcache.ENABLED = True
# une réponse réutilisée garde la provenance de SA collecte (le cache du §3 a été écrit avec l'ancien run MF-WAM)
META["meteofrance_wave"] = {"last_run_availability_time": int(t_now - 3600), "last_run_initialisation_time": int(t_now - 6 * 3600), "temporal_resolution_seconds": 10800}
omcache.reset(); d5 = Path(tempfile.mkdtemp()); os.environ["METEO_HISTORY_DIR"] = str(d5)
build.archive_pass(meta, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen)
s5 = archive.read(d5)[0]["sources"]
eq("9. réponse en cache : collecte et cycle d'origine conservés", (s5["mfwam"]["from"], s5["mfwam"]["fetched"], s5["mfwam"]["run"]),
   ("cache", ln["sources"]["mfwam"]["fetched"], ln["sources"]["mfwam"]["run"]))

# ---------- 10. Pannes : best match en échec, tout en échec, reprise partielle (revue PR #20, point 3) ----------
omcache.CACHE_DIR = Path(tempfile.mkdtemp()); omcache.reset(); calls.clear()
d6 = Path(tempfile.mkdtemp()); os.environ["METEO_HISTORY_DIR"] = str(d6)
FAIL.add("best match")
build.archive_pass(meta, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen)
l6 = archive.read(d6)
eq("10. best match en échec : la ligne v2 est écrite, modèles gardés, best match null avec la raison",
   (len(l6), l6[0]["b"]["03302"]["base"], l6[0]["b"]["03302"]["models"]["mfwam"] is not None, "503" in l6[0]["missing"].get("base", "")), (1, None, True, True))
eq("10. … mélange calculé sur les modèles disponibles", l6[0]["b"]["03302"]["mix_raw"][0] is not None, True)
eq("10. … runs/ (Gascogne) écrit, coast_runs/ absent (il ne vient que du best match)",
   ((d6 / "runs").exists() and bool(history._read_runs(d6, "2000")), len(history.read_coast_runs(d6))), (True, 0))
FAIL.update({"meteofrance_wave", "ecmwf_wam", "ncep_gfswave025"})
omcache.CACHE_DIR = Path(tempfile.mkdtemp()); omcache.reset(); calls.clear(); meta7 = {"errors": {}}
d7 = Path(tempfile.mkdtemp()); os.environ["METEO_HISTORY_DIR"] = str(d7)
build.archive_pass(meta7, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen)
eq("10. tout en échec : rien d'écrit (le passage suivant de l'heure réessaie), erreur notée",
   (len(archive.read(d7)), (d7 / "runs").exists() and bool(history._read_runs(d7, "2000")), "aucune prévision" in meta7["errors"].get("history", "")), (0, False, True))
FAIL.clear(); calls.clear()
build.archive_pass(meta7, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen)
eq("10. … le passage suivant de la même heure réessaie et écrit", (len(archive.read(d7)), len(calls) > 0), (1, True))
# reprise partielle : anciens formats déjà écrits, v2 absente (passage interrompu) → v2 écrite, anciens formats sans doublon
archive.path(d7, archive.read(d7)[0]["issued"]).unlink()
n_runs, n_coast = len((d7 / "runs" / f"{issued_old[:7]}.jsonl").read_text().splitlines()), len(history.read_coast_runs(d7))
build.archive_pass(meta7, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen)
eq("10. reprise partielle : v2 réécrite, anciens fichiers sans nouvelle ligne",
   (len(archive.read(d7)), len((d7 / "runs" / f"{issued_old[:7]}.jsonl").read_text().splitlines()), len(history.read_coast_runs(d7))), (1, n_runs, n_coast))
calls.clear()
build.archive_pass(meta7, gascogne, coast, offshore, PTS, weights, marc_buoys, mtimes, 1.2, gas_obs_t, gen)
eq("10. heure déjà dans buoy_runs/ : aucune requête", calls, [])

# ---------- 11. Correction recalculable avec un axe écrit à un AUTRE décalage (revue PR #20, point 4) ----------
for off in (OFF, OFF + 3600, OFF - 3600):
    openmeteo.LAST_OFFSET_S = off
    l11 = archive.build_line(issued_utc, gen.to_pydatetime(), fresh, PTS, weights, None, mtimes,
                             {"ratio": 1.3, "ratio_measured": 1.3, "start": gas_obs_t, "t_obs": gas_obs_t.strftime("%Y-%m-%dT%H:%M"), "status": "appliquée"})
    b11 = l11["b"]["03302"]
    raw = melange.blend({k: v for k, v in b11["models"].items() if v}, l11["weights"], b11["base"], 97)
    eq(f"11. axe au décalage {off // 3600:+d} h : facteurs et mélange corrigé recalculés depuis la ligne seule",
       ([round(x, 6) for x in replay_factors(l11)] == l11["correction"]["factors"],
        [None if v is None else round(v, 2) for v in melange.corrected(raw, replay_factors(l11))] == b11["mix"],
        T.parse(l11["correction"]["start_axis"]) == T.parse(l11["correction"]["start"])), (True, True, True))
openmeteo.LAST_OFFSET_S = OFF

print(f"\n{'TOUT OK' if not fails else 'ÉCHECS : ' + ', '.join(fails)}")
raise SystemExit(1 if fails else 0)
