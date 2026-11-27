"""Test du cache Open-Meteo (issue #7), sans réseau.   python -m tests.test_cache

Vérifie, avec une horloge et des métadonnées simulées, que le cache :
  - ne redemande RIEN tant qu'aucun modèle concerné n'a publié de nouveau run ;
  - redemande dès qu'un nouveau run est disponible (aucun retard), puis une fois de plus s'il n'était pas encore « posé » ;
  - ne redemande que le groupe concerné ;
  - redemande au changement de paramètres, de jour, après 6 h, ou après 1 h si les métadonnées sont illisibles ;
  - réutilise une réponse de moins de 12 h si Open-Meteo est en panne (mode dégradé signalé), et échoue au-delà ;
  - ne masque jamais une requête refusée (nom de modèle inconnu).
"""
import os
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

os.environ["METEO_CACHE_DIR"] = tempfile.mkdtemp(prefix="houlalah-cachetest-")
os.environ.pop("METEO_CACHE", None)
from pipeline import omcache  # noqa: E402

T0 = datetime(2026, 11, 27, 9, 0, tzinfo=ZoneInfo("Europe/Paris")).timestamp()
clock = {"t": T0}
omcache.time.time = lambda: clock["t"]
metas = {name: T0 - 3600 for _k, name in omcache.MARINE_ALL + omcache.WIND_ALL}   # runs disponibles depuis 1 h
broken = set()


def fake_meta(kind, name):
    return None if name in broken else {"last_run_availability_time": metas[name]}


omcache.model_meta = fake_meta
calls = []
down = {"on": False}


def fetcher(url, params):
    if down["on"]:
        raise RuntimeError("Open-Meteo : échec après 5 essais (HTTP 503)")
    calls.append(params.get("models", "best"))
    return [{"hourly": {"t": clock["t"]}}]


P = {"latitude": "44.0", "longitude": "-1.3", "hourly": "wave_height", "forecast_days": 7}


def run(group, params=P, watch=None):
    omcache._metas.clear()            # chaque passage relit les métadonnées
    n = len(calls)
    omcache.cached_get(group, "https://marine-api.open-meteo.com/v1/marine", params, fetcher, watch)
    return len(calls) - n, omcache.STATE[group]


fails = []


def expect(name, got, want):
    ok = got == want
    print(f"[{'OK' if ok else 'ÉCHEC'}] {name} : {got}")
    if not ok:
        fails.append(name)


expect("1er passage, cache vide → requête", run("marine")[0], 1)
clock["t"] += 1800
expect("30 min plus tard, aucun nouveau run → cache", run("marine")[0], 0)
clock["t"] += 1800
metas["ecmwf_wam025"] = clock["t"] - 120            # nouveau run publié il y a 2 min (pas encore « posé »)
expect("nouveau run ECMWF WAM disponible → requête immédiate", run("marine")[0], 1)
clock["t"] += 1800
expect("passage suivant : run maintenant posé → une seule requête de plus", run("marine")[0], 1)
clock["t"] += 1800
expect("puis plus rien tant que rien ne change", run("marine")[0], 0)
expect("un autre groupe (vent ICON) sans cache → requête", run("wind_icon")[0], 1)
clock["t"] += 600
metas["dwd_icon_d2"] = clock["t"] - 900
expect("vent ECMWF : une requête puis le cache", [run("wind_ecmwf")[0], run("wind_ecmwf")[0]], [1, 0])
expect("nouveau run ICON-D2 : le vent ICON est redemandé…", run("wind_icon")[0], 1)
expect("… mais pas le vent ECMWF", run("wind_ecmwf")[0], 0)
expect("… mais pas la mer", run("marine")[0], 0)
expect("paramètres changés (spot ajouté) → requête", run("marine", {**P, "latitude": "44.0,44.1"})[0], 1)
clock["t"] += 3 * 3600
expect("3 h sans nouveau run → cache", run("marine", {**P, "latitude": "44.0,44.1"})[0], 0)
clock["t"] += 3.5 * 3600
expect("plus de 6 h → requête (filet de sécurité)", run("marine", {**P, "latitude": "44.0,44.1"})[0], 1)
broken.add("meteofrance_wave")
clock["t"] += 1800
expect("métadonnées illisibles, 30 min → cache", run("marine", {**P, "latitude": "44.0,44.1"})[0], 0)
clock["t"] += 3600
expect("métadonnées illisibles, 1 h 30 → requête", run("marine", {**P, "latitude": "44.0,44.1"})[0], 1)
broken.clear()
P2 = {**P, "latitude": "44.0,44.1"}
clock["t"] = datetime(2026, 11, 28, 21, 0, tzinfo=ZoneInfo("Europe/Paris")).timestamp()
expect("21 h (plus de 6 h après) → requête", run("marine", P2)[0], 1)
clock["t"] = datetime(2026, 11, 28, 23, 50, tzinfo=ZoneInfo("Europe/Paris")).timestamp()
expect("23 h 50, même jour, aucun nouveau run → cache", run("marine", P2)[0], 0)
clock["t"] = datetime(2026, 11, 29, 0, 5, tzinfo=ZoneInfo("Europe/Paris")).timestamp()
expect("nouveau jour (heure de Paris) → requête", run("marine", {**P, "latitude": "44.0,44.1"})[0], 1)
down["on"] = True
clock["t"] += 7 * 3600
n, st = run("marine", {**P, "latitude": "44.0,44.1"})
expect("panne Open-Meteo, cache de 7 h → mode dégradé signalé", (n, st["source"]), (0, "cache-dégradé"))
clock["t"] += 6 * 3600
try:
    run("marine", {**P, "latitude": "44.0,44.1"})
    expect("panne Open-Meteo, cache de 13 h → échec", "pas d'échec", "échec")
except RuntimeError:
    expect("panne Open-Meteo, cache de 13 h → échec (le site garde sa version)", "échec", "échec")
down["on"] = False


def refused(url, params):
    raise ValueError("modèle inconnu")


try:
    omcache.cached_get("wave_x", "u", {**P, "models": "inconnu"}, refused, "wave_mfwam")
    expect("requête refusée jamais masquée", "masquée", "levée")
except ValueError:
    expect("requête refusée jamais masquée par le cache", "levée", "levée")
clock["t"] = datetime(2026, 11, 29, 8, 0, tzinfo=ZoneInfo("Europe/Paris")).timestamp()
expect("soleil : une requête…", run("sun", {"latitude": "44", "daily": "sunrise,sunset"})[0], 1)
clock["t"] += 12 * 3600
expect("… et aucune autre dans la journée (12 h plus tard)", run("sun", {"latitude": "44", "daily": "sunrise,sunset"})[0], 0)
omcache.ENABLED = False   # équivalent de METEO_CACHE=0
expect("cache désactivé : toujours une requête", [run("marine")[0], run("marine")[0]], [1, 1])
omcache.ENABLED = True

# instrumentation : poids des requêtes selon la règle publiée (> 10 variables = fraction d'appel en plus)
omcache.reset()
omcache.record("https://api.open-meteo.com/v1/forecast", {"latitude": ",".join(["44"] * 177), "hourly": "a,b,c", "daily": "d,e", "models": "m1,m2,m3,m4", "forecast_days": 7}, 2, [429, 200])
s = omcache.summary()["openmeteo"]
expect("comptage : 177 points, 20 variables → 2 appels par requête, 354 par point, 1 reprise, 1 refus 429",
       (s["points"], s["calls_if_per_request"], s["calls_if_per_point"], s["retries"], s["http_429"]), (177, 2.0, 354.0, 1, 1))
print(f"\n{'TOUT OK' if not fails else 'ÉCHECS : ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
