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


def fake_get(url, params, tries=5):
    calls.append(params.get("models", "best match"))
    m = params.get("models")
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
omcache.model_meta = lambda kind, name: META.get(name, {"last_run_availability_time": int(t_now - 7200), "last_run_initialisation_time": int(t_now - 9 * 3600)})
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
    wall = [openmeteo.shift_str((issued_utc + timedelta(hours=k)).strftime("%Y-%m-%dT%H:00"), OFF) for k in range(97)]
    corr = melange.correction(wall, ln["correction"]["ratio"], pd.Timestamp(T.parse(ln["correction"]["t_obs"]).astimezone(T.zone(T.PARIS)).replace(tzinfo=None)))
    ok_fin &= [None if v is None else round(v, 2) for v in melange.corrected(raw, corr)] == b["mix"]
eq("4. mélange brut recalculé depuis l'archive = archivé", ok_raw, True)
eq("4. mélange corrigé recalculé (ratio, t_obs, 24 h) = archivé", ok_fin, True)
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

print(f"\n{'TOUT OK' if not fails else 'ÉCHECS : ' + ', '.join(fails)}")
raise SystemExit(1 if fails else 0)
