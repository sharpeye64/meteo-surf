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
print(f"\n{'TOUT OK' if not fails else 'ÉCHECS : ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
