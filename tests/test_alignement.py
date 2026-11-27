"""Alignement horaire des prévisions (revue de la PR #12), sans réseau.   python -m tests.test_alignement

Scénario intégré : le robot passe à 23 h 50 (cache rempli), puis à 0 h 20 le lendemain. Le changement de jour impose de tout
redemander ; le vent GFS et le soleil échouent (Open-Meteo en panne partielle) et sont repris du cache de la VEILLE, qui
commence donc 24 h plus tôt que les autres réponses. On vérifie que chaque valeur reste attachée à SON heure (la valeur
simulée encode son heure), y compris pour des réponses de longueurs différentes, que le soleil reste juste par date,
que le mode dégradé est signalé et que des prévisions qui ne couvrent pas les 48 prochaines heures sont refusées.
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

os.environ["METEO_CACHE_DIR"] = tempfile.mkdtemp(prefix="houlalah-aligntest-")
from pipeline import config, omcache, openmeteo  # noqa: E402

TZ = ZoneInfo(config.TIMEZONE)
ORIGIN = datetime(2026, 1, 1)
clock = {"now": datetime(2026, 11, 27, 23, 50, tzinfo=TZ)}
omcache.time.time = lambda: clock["now"].timestamp()
omcache.model_meta = lambda kind, name: {"last_run_availability_time": 1_700_000_000}
_cov = openmeteo.check_coverage
openmeteo.check_coverage = lambda g, r: _cov(g, r, now=clock["now"])
openmeteo.config.REQUEST_PAUSE_S = 0
failing = set()
short = {}


def code(t):            # valeur simulée = nombre d'heures depuis le 01/01/2026 : on sait à quelle heure elle appartient
    return float((datetime.strptime(t, "%Y-%m-%dT%H:%M") - ORIGIN).total_seconds() // 3600)


def fake_get(url, params):
    models = params.get("models", "")
    group = ("wind_" + {"meteofrance_seamless": "arome", "icon_seamless": "icon", "gfs_seamless": "gfs", "ecmwf_ifs025": "ecmwf"}[models]
             if "forecast" in url and models else ("sun" if "daily" in params else ("marine" if not models else "wave")))
    if group in failing:
        raise RuntimeError("Open-Meteo : échec après 5 essais (HTTP 503)")
    d0 = clock["now"].astimezone(TZ).replace(tzinfo=None, hour=0, minute=0)
    n_h = short.get(group, 24 * config.FORECAST_DAYS)
    times = [(d0 + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(n_h)]
    n = len(str(params["latitude"]).split(","))
    if group == "sun":
        days = [(d0 + timedelta(days=k)).strftime("%Y-%m-%d") for k in range(config.FORECAST_DAYS)]
        return [{"daily": {"time": days, "sunrise": [d + "T08:" + d[-2:] for d in days], "sunset": [d + "T17:" + d[-2:] for d in days]}}] * n
    if "forecast" in url:
        return [{"hourly": {"time": times, **{v: [code(t) for t in times] for v in ("wind_speed_10m", "wind_direction_10m", "wind_gusts_10m")}}}] * n
    vars_ = params["hourly"].split(",")
    return [{"hourly": {"time": times, **{v: [code(t) for t in times] for v in vars_}}}] * n


openmeteo.get = fake_get
spots = [{"name": "A", "lat": 44.0, "lon": -1.3, "ori": 270}, {"name": "B", "lat": 43.5, "lon": -1.5, "ori": 290}]
fails = []


def expect(name, ok, detail=""):
    print(f"[{'OK' if ok else 'ÉCHEC'}] {name}" + (f" : {detail}" if detail else ""))
    if not ok:
        fails.append(name)


def consistent(out):
    """Chaque valeur horaire correspond à son heure ; le soleil correspond à sa date."""
    for sp in out:
        ref = sp["marine"]["time"]
        series = [sp["marine"]["wave_height"], sp["wind"]["wind_speed_10m"]] + list(sp["wave_models"].values()) + list(sp["wind_models"].values())
        for s in series:
            if len(s) != len(ref):
                return False, "longueurs différentes"
            for t, v in zip(ref, s):
                if v is not None and v != code(t):
                    return False, f"valeur de {v} rangée à {t}"
        d = sp["daily"]
        for day, sr in zip(d["time"], d.get("sunrise") or []):
            if sr and not sr.startswith(day):
                return False, f"lever du {sr[:10]} rangé au {day}"
    return True, ""


# 1. 23 h 50 : tout est demandé, cache rempli
omcache.reset()
out, _ = openmeteo.fetch(spots)
ok, why = consistent(out)
expect("23 h 50 : séries alignées", ok, why)

# 2. 0 h 20 le lendemain : vent GFS et soleil en panne → repris du cache de la veille (commence 24 h plus tôt)
clock["now"] = datetime(2026, 11, 28, 0, 20, tzinfo=TZ)
failing = {"wind_gfs", "sun"}
short = {"wind_arome": 60}       # AROME : réponse plus courte (60 h) que les autres
omcache.reset()
out, _ = openmeteo.fetch(spots)
st = omcache.STATE
expect("0 h 20 : vent GFS et soleil en mode dégradé", st["wind_gfs"]["source"] == "cache-dégradé" and st["sun"]["source"] == "cache-dégradé")
expect("0 h 20 : axe horaire = celui du jour (réponse la plus récente)", out[0]["marine"]["time"][0] == "2026-11-28T00:00", out[0]["marine"]["time"][0])
expect("décalage de 24 h noté pour le vent GFS", st["wind_gfs"].get("shift_h") == 24.0, st["wind_gfs"].get("shift_h"))
ok, why = consistent(out)
expect("0 h 20 : chaque valeur reste à son heure (vent GFS d'hier, AROME court, mer du jour)", ok, why)
gfs = out[0]["wind_models"]["gfs"]
expect("vent GFS d'hier : valeurs présentes pour aujourd'hui, absentes au-delà de sa couverture", gfs[0] == code("2026-11-28T00:00") and gfs[-1] is None)
expect("AROME court : valeurs puis vide après 60 h", out[0]["wind_models"]["arome"][59] is not None and out[0]["wind_models"]["arome"][60] is None)
expect("soleil d'hier : lever du 28/11 bien rangé au 28/11", out[0]["daily"]["time"][0] == "2026-11-28" and out[0]["daily"]["sunrise"][0].startswith("2026-11-28"))
summ = omcache.summary()["openmeteo"]
expect("collecte des prévisions = la plus ancienne (veille, 23 h 50)", summ["forecast_fetched"] == "2026-11-27T23:50+01:00", summ["forecast_fetched"])

# 3. prévisions qui ne couvrent pas les 48 prochaines heures : refusées (le site garde sa version)
failing = set()
short = {"wave": 30}
clock["now"] = datetime(2026, 11, 28, 1, 20, tzinfo=TZ)
for f in omcache.CACHE_DIR.glob("wave_*.json"):
    f.unlink()
omcache.reset()
try:
    openmeteo.fetch(spots)
    expect("modèle de vagues sur 30 h seulement : refusé", False, "accepté")
except RuntimeError as e:
    expect("modèle de vagues sur 30 h seulement : refusé", "incomplètes" in str(e), str(e)[:80])

# 4. réponse abîmée (séries de longueurs différentes) : jamais mise en cache, jamais réutilisée
short = {}
bad = lambda url, params: [{"hourly": {"time": ["2026-11-28T00:00", "2026-11-28T01:00"], "wave_height": [1.0]}}]
try:
    omcache.cached_get("wave_test", openmeteo.MARINE, {"latitude": "44", "hourly": "wave_height"}, bad, "wave_mfwam")
    expect("réponse abîmée refusée", False, "acceptée")
except RuntimeError:
    expect("réponse abîmée refusée et non enregistrée", not (omcache.CACHE_DIR / "wave_test.json").exists())

print(f"\n{'TOUT OK' if not fails else 'ÉCHECS : ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
