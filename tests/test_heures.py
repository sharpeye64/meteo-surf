"""Contrat horaire du robot (issue #2), sans réseau.   python -m tests.test_heures

France / Portugal, changements d'heure (heure répétée d'octobre, heure absente de mars), décalage unique des séries
Open-Meteo, anciennes données sans décalage, même instant et même âge quel que soit le fuseau d'écriture.
"""
import json
import sys
from datetime import datetime, timedelta, timezone

from pipeline import config, timefmt as T

fails = []


def eq(name, got, want):
    ok = got == want
    print(f"[{'OK' if ok else 'ÉCHEC'}] {name} : {got}" + ("" if ok else f" (attendu {want})"))
    if not ok:
        fails.append(name)


Z = lambda *a: datetime(*a, tzinfo=timezone.utc)

# 1. écriture et lecture
eq("Lacanau 10 h (hiver)", T.fmt(Z(2026, 11, 27, 9), T.PARIS), "2026-11-27T10:00+01:00")
eq("même instant à Ericeira", T.fmt(Z(2026, 11, 27, 9), T.LISBON), "2026-11-27T09:00+00:00")
eq("même instant en Espagne", T.fmt(Z(2026, 11, 27, 9), T.MADRID), "2026-11-27T10:00+01:00")
eq("été à Paris", T.fmt(Z(2026, 7, 1, 8), T.PARIS), "2026-07-01T10:00+02:00")
eq("lecture avec décalage : instants égaux", T.parse("2026-11-27T10:00+01:00") == T.parse("2026-11-27T09:00+00:00"), True)
eq("ancien format = heure de Paris, explicitement", T.parse("2026-11-27T10:00") == Z(2026, 11, 27, 9), True)
eq("même âge, écrit à Paris ou à Lisbonne", round(T.age_h("2026-11-27T10:00+01:00", Z(2026, 11, 27, 12)), 3) == round(T.age_h("2026-11-27T09:00+00:00", Z(2026, 11, 27, 12)), 3) == 3.0, True)

# 2. Open-Meteo : une série écrite avec UN seul décalage (celui de la requête), qui traverse le passage à l'heure d'hiver
req_summer = 7200   # requête faite le 24/10 (heure d'été) : toute la série en +02:00, même après le changement
eq("Open-Meteo : « 03:00 » d'une requête d'été, le 25/10, est en réalité 02:00 heure d'hiver",
   T.fmt(T.from_fixed("2026-10-25T03:00", req_summer), T.PARIS), "2026-10-25T02:00+01:00")
ax = [T.fmt(T.from_fixed((datetime(2026, 10, 25) + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M"), req_summer), T.PARIS) for h in range(5)]
eq("série Open-Meteo convertie : l'heure 02 h apparaît deux fois, avec deux décalages", ax,
   ["2026-10-25T00:00+02:00", "2026-10-25T01:00+02:00", "2026-10-25T02:00+02:00", "2026-10-25T02:00+01:00", "2026-10-25T03:00+01:00"])

# 3. heures murales (mesures, marées) : heure répétée déduite de l'ORDRE, heure absente comptée, jamais devinée en silence
st = {}
seq = T.wall_seq(["2026-10-25T01:30", "2026-10-25T02:00", "2026-10-25T02:30", "2026-10-25T02:00", "2026-10-25T02:30", "2026-10-25T03:00"], T.PARIS, st)
inst = [a.astimezone(timezone.utc) for a in seq]
eq("heure répétée : instants strictement croissants", all(b > a for a, b in zip(inst, inst[1:])), True)
eq("heure répétée : 1re occurrence +02:00, 2de +01:00", [T.fmt(a, T.PARIS)[16:] for a in seq], ["+02:00", "+02:00", "+02:00", "+01:00", "+01:00", "+01:00"])
st2 = {}
T.wall_seq(["2026-03-29T01:00", "2026-03-29T02:00", "2026-03-29T03:00"], T.PARIS, st2)
eq("heure absente du 29/03 : comptée (nonexistent)", st2.get("nonexistent"), 1)
eq("heure ambiguë isolée : repérée", T.ambiguous("2026-10-25T02:15"), True)

# 4. fuseaux des lieux
spots = json.loads(config.SPOTS_FILE.read_text(encoding="utf-8"))
from collections import Counter  # noqa: E402
c = Counter(T.spot_tz(s) for s in spots)
eq("spots : Portugal → Lisbonne, Espagne → Madrid, France → Paris",
   (c[T.LISBON], c[T.MADRID], c[T.PARIS]), (sum(s["region"].startswith("Portugal") for s in spots), sum(s["region"] in ("Espagne Nord", "Galice") for s in spots),
                                             sum(not s["region"].startswith("Portugal") and s["region"] not in ("Espagne Nord", "Galice") for s in spots)))
from pipeline import candhis, ibi_buoys  # noqa: E402
bt = {b.get("name") or b.get("id"): T.place_tz(b["lat"], b["lon"]) for b in candhis.STATIONS + ibi_buoys.STATIONS}
eq("bouées : Leixões, Nazaré, Sines, Faro à Lisbonne ; Cabo Silleiro à Madrid ; Anglet à Paris",
   [bt.get(k) for k in ("Leixões", "Nazaré (large)", "Sines", "Faro", "Cabo Silleiro", "Anglet")],
   [T.LISBON] * 4 + [T.MADRID, T.PARIS])
eq("bouée Gascogne (au large, Météo-France) : Paris", T.place_tz(45.2, -5.0), T.PARIS)

# 5. forecast.json : un spot français et un spot portugais, mêmes instants, axe portugais commençant à minuit LOCAL
axis = [(datetime(2026, 11, 27) + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(48)]
mk = lambda name: {"name": name, "marine": {"time": axis, "wave_height": list(range(48))}, "wind": {"time": axis, "wind_speed_10m": list(range(48))},
                   "wave_models": {"mfwam": list(range(48))}, "wind_models": {"gfs": list(range(48))},
                   "daily": {"time": ["2026-11-27", "2026-11-28"], "sunrise": ["2026-11-27T08:17", "2026-11-28T08:18"], "sunset": ["2026-11-27T17:20", None]},
                   "tide": {"extremes": [{"t": "2026-11-27T06:01", "type": "PM", "h": 4.3}]}}
pay = {"meta": {"generated": "2026-11-27T10:39", "forecast_fetched": "2026-11-27T10:00", "errors": {}},
       "gascogne": {"lat": 45.2, "lon": -5.0, "latest": {"time": "2026-11-27T10:00"}, "obs": [{"t": "2026-11-27T09:00"}, {"t": "2026-11-27T10:00"}],
                    "model": [{"t": "2026-11-27T00:00", "hs": 1}]},
       "coast": [], "offshore": [{"id": "6200084", "lat": 41.32, "lon": -8.98, "latest": {"time": "2026-11-27T10:00"}, "obs": [{"t": "2026-11-27T10:00"}],
                                  "model": [{"t": "2026-11-27T00:00", "hs": 1}]}],
       "buoy_stats": {"x": {"hs_max_t": "2026-11-19T18:00"}}, "spots": [mk("Lacanau"), mk("Ericeira")]}
cfg = [{"name": "Lacanau", "region": "Gironde"}, {"name": "Ericeira", "region": "Portugal Centre"}]
out = T.localize(pay, cfg, 3600, 3600)
fr_, pt_ = out["spots"]
eq("spot français : axe inchangé (48 h, minuit de Paris)", (len(fr_["marine"]["time"]), fr_["marine"]["time"][0]), (48, "2026-11-27T00:00+01:00"))
eq("spot portugais : axe à minuit de Lisbonne (23 h de la veille retirée)", (len(pt_["marine"]["time"]), pt_["marine"]["time"][0]), (47, "2026-11-27T00:00+00:00"))
eq("spot portugais : toutes ses séries coupées pareil", {len(pt_["wind"]["time"]), len(pt_["wind"]["wind_speed_10m"]), len(pt_["wave_models"]["mfwam"]), len(pt_["wind_models"]["gfs"]), len(pt_["marine"]["wave_height"])}, {47})
eq("même valeur ↔ même instant (Ericeira[0] = Lacanau[1])", (pt_["marine"]["wave_height"][0], T.parse(pt_["marine"]["time"][0]) == T.parse(fr_["marine"]["time"][1])), (1, True))
eq("soleil d'Ericeira à l'heure de Lisbonne", pt_["daily"]["sunrise"][0], "2026-11-27T07:17+00:00")
eq("marée à l'heure du spot", (fr_["tide"]["extremes"][0]["t"], pt_["tide"]["extremes"][0]["t"]), ("2026-11-27T06:01+01:00", "2026-11-27T05:01+00:00"))
eq("bouée portugaise à l'heure de Lisbonne, fuseau indiqué", (out["offshore"][0]["latest"]["time"], out["offshore"][0]["tz"]), ("2026-11-27T09:00+00:00", T.LISBON))
eq("heures du modèle au point de la bouée (décalage Open-Meteo)", out["offshore"][0]["model"][0]["t"], "2026-11-26T23:00+00:00")
eq("génération à l'heure de Paris, contrat v2", (out["meta"]["generated"], out["meta"]["time"]["version"]), ("2026-11-27T10:39+01:00", 2))
eq("plus aucune heure sans décalage", T.naive_strings(out), [])
eq("l'original n'est pas modifié (calculs internes du robot)", pay["spots"][1]["marine"]["time"][0], "2026-11-27T00:00")

# ===== Non-régression : revue de la PR #17 (ChatGPT Work, commit 3ab85d9) =====
# A. pipeline/bouees.py (spot_forecasts, graphique) : rapprochement par INSTANT, pas par heure écrite.
#    Scénario : à 10 h (Paris), la prévision « du moment » d'un spot portugais doit être celle de 9 h à Lisbonne (même
#    instant), pas celle de 10 h à Lisbonne (une heure plus tard). Valeurs simulées = n° d'heure absolue.
from pipeline import bouees  # noqa: E402
_orig = bouees.json.loads
ax2 = [(datetime(2026, 11, 27) + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(48)]
mk2 = lambda name: {"name": name, "marine": {"time": ax2, "wave_height": [float(h) for h in range(48)]}, "wind": {"time": ax2},
                    "wave_models": {}, "wind_models": {}, "daily": {}, "tide": None}
loc = T.localize({"meta": {"generated": "2026-11-27T10:00", "errors": {}}, "coast": [], "offshore": [], "spots": [mk2("Lacanau"), mk2("Supertubos")]},
                 [{"name": "Lacanau", "region": "Gironde"}, {"name": "Supertubos", "region": "Portugal Centre"}], 3600)
res = {r["name"]: r["h"] for r in bouees.spot_forecasts(loc, datetime(2026, 11, 27, 10, 0))}
eq("A. prévision « du moment » à 10 h de Paris : même instant pour Lacanau et Supertubos", (res.get("Lacanau"), res.get("Supertubos")), (10.0, 10.0))
eq("A. clé horaire absolue : 10 h Paris = 9 h Lisbonne ; 10 h Lisbonne = 11 h Paris",
   (T.hour_key("2026-11-27T10:00+01:00") == T.hour_key("2026-11-27T09:00+00:00"), T.hour_key("2026-11-27T10:00+00:00") == T.hour_key("2026-11-27T11:00+01:00")), (True, True))
obs = [{"t": "2026-11-27T09:00+00:00"}, {"t": "2026-11-27T10:00+00:00"}]                      # Leixões (Lisbonne)
model = [{"t": "2026-11-27T10:00+01:00", "hs": 1.0}, {"t": "2026-11-27T11:00+01:00", "hs": 2.0}]  # prévision écrite à l'heure de Paris
by = {T.hour_key(m["t"]): m["hs"] for m in model}
eq("A. graphique bouée : mesure 9 h Lisbonne ↔ prévision 10 h Paris (même instant)", [by.get(T.hour_key(o["t"])) for o in obs], [1.0, 2.0])

# B. pipeline/build.py : heure de génération pendant l'heure répétée d'octobre. 03:30 heure d'été (01:30 UTC) et 02:30 heure
#    d'hiver s'écrivent toutes deux « 02:30 » en heure de Paris : seul l'instant exact transmis par le robot lève l'ambiguïté.
for utc, want in (("2026-10-25T00:30:00+00:00", "2026-10-25T02:30+02:00"), ("2026-10-25T01:30:00+00:00", "2026-10-25T02:30+01:00")):
    o = T.localize({"meta": {"generated": "2026-10-25T02:30", "errors": {}, "api": {"today": {"last": "2026-10-25T02:30"}}}, "spots": [],
                    "_generated_utc": utc}, [], 3600)
    eq(f"B. génération à {utc[11:16]} UTC → {want} (et compteur du jour identique)", (o["meta"]["generated"], o["meta"]["api"]["today"]["last"], "_generated_utc" in o), (want, want, False))

# C. pipeline/bouees.py : libellé du fuseau de la bouée (Leixões n'est pas « heure de Paris »)
eq("C. libellés", [T.tz_label(T.place_tz(41.32, -8.98)), T.tz_label(T.place_tz(43.53, -1.62)), T.tz_label(T.place_tz(43.6, -2.0))],
   ["heure du Portugal", "heure de Paris", "heure d'Espagne"])
# D. pipeline/appdata.py (_now_index, index de l'appli) : créneau de l'heure courante choisi en UTC (2e revue PR #17)
from pipeline import appdata  # noqa: E402
_at = lambda ax, n: ax[appdata._now_index(ax, datetime.fromisoformat(n))]
ax = ["2026-11-27T10:00+01:00", "2026-11-27T11:00+01:00", "2026-11-27T12:00+01:00"]
eq("D. à 11:59:01+01:00 → créneau 11:00+01:00 (pas 12:00)", _at(ax, "2026-11-27T11:59:01+01:00"), "2026-11-27T11:00+01:00")
eq("D. à 11:00:00+01:00 pile → 11:00+01:00", _at(ax, "2026-11-27T11:00:00+01:00"), "2026-11-27T11:00+01:00")
oct25 = ["2026-10-25T01:00+02:00", "2026-10-25T02:00+02:00", "2026-10-25T02:00+01:00", "2026-10-25T03:00+01:00"]
eq("D. au second 02:30+01:00 → second 02:00 (02:00+01:00)", _at(oct25, "2026-10-25T02:30+01:00"), "2026-10-25T02:00+01:00")
eq("D. au premier 02:30+02:00 → premier 02:00 (02:00+02:00)", _at(oct25, "2026-10-25T02:30+02:00"), "2026-10-25T02:00+02:00")
# horloge réelle Europe/Paris (comme timefmt.now()) : second 02:30 = fold=1. L'ancien calcul « now - 59 min » se faisait en
# heure murale (01:31+02:00) et retombait sur le premier 02:00.
_par = datetime(2026, 10, 25, 2, 30, fold=1, tzinfo=T.zone(T.PARIS))
eq("D. horloge de Paris, second 02:30 (fold=1) → 02:00+01:00", oct25[appdata._now_index(oct25, _par)], "2026-10-25T02:00+01:00")
_par = datetime(2026, 11, 27, 11, 59, 1, tzinfo=T.zone(T.PARIS))
eq("D. horloge de Paris, 11:59:01 → 11:00+01:00", ax[appdata._now_index(ax, _par)], "2026-11-27T11:00+01:00")
pt = ["2026-11-27T09:00+00:00", "2026-11-27T10:00+00:00", "2026-11-27T11:00+00:00"]
eq("D. spot portugais : 11:59 à Paris → 10:00+00:00", _at(pt, "2026-11-27T11:59:01+01:00"), "2026-11-27T10:00+00:00")
print(f"\n{'TOUT OK' if not fails else 'ÉCHECS : ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
