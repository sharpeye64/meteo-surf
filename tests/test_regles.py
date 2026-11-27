"""Règles métier du ROBOT (issue #4) sur les cas communs tests/regles_communes.json, sans réseau :
    python -m tests.test_regles
Les mêmes cas sont joués sur le site (tests/regles_site.test.js) et l'appli (tests/regles_app.test.mjs).
Vérifie aussi ce que le robot écrit pour l'appli : cadence (« lim »), type de station (« kind »), point du spot (« pt »)."""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pipeline import appdata, bouees, candhis, config, ibi_buoys, seo, timefmt

C = json.loads((Path(__file__).parent / "regles_communes.json").read_text(encoding="utf-8"))
fails = []


def eq(name, got, want):
    ok = got == want
    print(f"[{'OK' if ok else 'ÉCHEC'}] {name} : {got!r}" + ("" if ok else f" (attendu {want!r})"))
    if not ok:
        fails.append(name)


now = datetime(2026, 11, 27, 10, 0)   # heure de Paris (naïve, comme bouees.age_h)
now_utc = now.replace(tzinfo=timefmt.zone(timefmt.PARIS)).astimezone(timezone.utc)
for f in C["fresh"]:
    if f.get("robot") is False:
        continue
    lim = f.get("lim") or bouees.station({"id": f["id"]})["lim"]
    t = (now_utc - timedelta(hours=f["age"])).astimezone(timefmt.zone(timefmt.PARIS)).isoformat(timespec="seconds")   # à la seconde : cas limites exacts
    eq(f"fraîcheur {f['id']} {f['age']} h" + (f" lim {f['lim']}" if f.get("lim") else ""), bouees.fresh_state(now, t, lim), f["want"])
eq("fraîcheur : heure illisible → muette", bouees.fresh_state(now, "n'importe quoi", 1), "off")
for x in C["sector"]:
    eq(f"secteur {x['deg']}°", seo.sector(x["deg"]), x["want"])
for w in C["wind"]:
    eq(f"vent {w['v']} km/h du {w['wdir']}° (plage vers {w['ori']}°)", seo.wind_for_spot(w["v"], w["wdir"], w["ori"]), w["want"])

# cadence : celle du robot (bouees.station) = la règle de repli du site et de l'appli (identifiant CANDHIS → 1 h, sinon 2 h)
ids = ["gascogne"] + [s["id"] for s in candhis.STATIONS + ibi_buoys.STATIONS]
eq("cadence du robot = règle de repli du site et de l'appli, pour les 22 stations",
   {i: bouees.station({"id": i})["lim"] for i in ids}, {i: (1 if re.fullmatch(r"0\d{4}", i) else 2) for i in ids})
# bouée de référence des Landes (D9) : celle que le robot écrit (« ref ») = la préférence des règles communes
for p in C["pick"]:
    if p["spot"]["region"] == "Landes":
        want = "03302" if p["spot"]["name"] != "La Gravière" else "gascogne"
        eq(f"référence Landes ({p['spot']['name']})", config.ref_buoy(p["spot"]), want)

# données de l'appli : chaque bouée porte sa cadence et son type ; un spot recalé sur la côte garde son point de prévision
pay = {"gascogne": {"lat": 45.2, "lon": -5.0, "latest": {"time": "2026-11-27T10:00+01:00", "hs": 2.0}},
       "coast": [{"id": "03302", "name": "Cap Ferret", "lat": 44.65, "lon": -1.45, "latest": {"time": "2026-11-27T10:00+01:00", "hs": 1.0}}],
       "offshore": [{"id": "6200024", "name": "Bilbao-Vizcaya", "sub": "au large, Espagne", "lat": 43.65, "lon": -3.04,
                     "latest": {"time": "2026-11-27T10:00+01:00", "hs": 1.5}, "silent": True}]}
B = {b["id"]: b for b in appdata._buoys(pay)}
eq("index de l'appli : cadence et type de chaque bouée", {k: (b["kind"], b["lim"]) for k, b in B.items()},
   {"gascogne": ("gascogne", 2), "03302": ("coast", 1), "6200024": ("offshore", 2)})
eq("index de l'appli : bouée muette signalée", B["6200024"].get("silent"), True)
# le point de prévision des spots recalés (« pt ») est vérifié sur l'index réellement écrit, dans tests/test_offline.py

print(f"\n{'TOUT OK' if not fails else 'ÉCHECS : ' + ', '.join(fails)}")
raise SystemExit(1 if fails else 0)
