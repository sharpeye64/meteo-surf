"""Test hors ligne du pipeline : toutes les sources sont simulées.  python -m tests.test_offline

Tout ce que le test génère va dans un dossier TEMPORAIRE (METEO_OUT_DIR), jamais dans web/ : des données simulées ne
peuvent plus se retrouver dans le site publié (issue #3). Elles portent en plus une marque de test refusée par tools/check_site.py."""
import os as _os
import tempfile as _tempfile
from pathlib import Path as _Path

_OUT = _tempfile.mkdtemp(prefix="houlalah-test-")
_os.environ["METEO_OUT_DIR"] = _OUT      # avant tout import de pipeline : config.OUT_DIR est lu à l'import
_os.environ["METEO_TEST"] = "1"
_os.environ["METEO_CACHE_DIR"] = _tempfile.mkdtemp(prefix="houlalah-cache-")   # cache Open-Meteo du test, vide au départ (issue #7)
_WEB = _Path(__file__).resolve().parent.parent / "web"
# instantané de TOUT web/ (chemin, taille, date) : on détecte aussi un fichier AJOUTÉ, même si web/ ne contient au départ
# aucun fichier généré (cas du robot GitHub, où web/ ne contient que les sources du site)
_snap = lambda: {str(f.relative_to(_WEB)): (f.stat().st_size, f.stat().st_mtime_ns) for f in _WEB.rglob("*") if f.is_file()}
_before = _snap()

import json
import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import xarray as xr

from pipeline import build, buoy, config, history, marc, openmeteo

assert config.OUT_DIR == _Path(_OUT) and config.TEST_RUN, "le test doit écrire dans un dossier temporaire"

start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
TIMES = [(start + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(24 * config.FORECAST_DAYS)]


def fake_get(url, params, tries=3):
    n = len(str(params["latitude"]).split(","))
    if "marine" in url:
        past = params.get("past_days", 0)
        tt = [(start + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(-24 * past, 48)] if past else TIMES
        f = {"meteofrance_wave": 1.0, "ewam": 1.1, "ecmwf_wam": 0.9, "ncep_gfswave025": 0.8}.get(params.get("models"), 1.0)
        if params.get("models") == "dwd_ewam":
            raise ValueError("bad model")
        hourly = {"time": tt, "wave_height": [round(f * (1.2 + 0.3 * math.sin(i / 10)), 2) for i in range(len(tt))],
                  "wave_period": [9] * len(tt), "wave_direction": [295] * len(tt), "swell_wave_height": [1.0] * len(tt),
                  "swell_wave_period": [12] * len(tt), "swell_wave_direction": [295] * len(tt),
                  "secondary_swell_wave_height": [0.4] * len(tt), "secondary_swell_wave_period": [8] * len(tt),
                  "secondary_swell_wave_direction": [235] * len(tt), "wind_wave_height": [0.2] * len(tt),
                  "wind_wave_period": [5] * len(tt), "wind_wave_direction": [270] * len(tt),
                  "sea_level_height_msl": [math.sin(i / 12.42 * 2 * math.pi) for i in range(len(tt))],
                  "sea_surface_temperature": [16.8] * len(tt)}
        res = [{"hourly": hourly}] * n
        if params.get("models") == "ncep_gfswave025":  # maille « terre » : 0,00 m sur tout le premier point, et au point de Gascogne
            lats = str(params["latitude"]).split(",")
            res = [{"hourly": {**hourly, "wave_height": [0.0] * len(tt)}} if (j == 0 or float(la) == config.GASCOGNE["lat"]) else r
                   for j, (la, r) in enumerate(zip(lats, res))]
        return res
    hourly = {"time": TIMES}
    models = [m for m in str(params.get("models", "")).split(",") if m]
    for _k, _l, api in config.WIND_MODELS:
        if api not in models:
            continue
        sfx = f"_{api}" if len(models) > 1 else ""   # comme l'API : un seul modèle demandé = variables sans suffixe
        hourly[f"wind_speed_10m{sfx}"] = [10 + i % 12 for i in range(len(TIMES))]
        if api == "meteofrance_seamless":  # AROME s'arrête avant la fin : le vent doit être complété par un autre modèle
            hourly[f"wind_speed_10m{sfx}"][-48:] = [None] * 48
        hourly[f"wind_direction_10m{sfx}"] = [100 if i % 24 < 12 else 280 for i in range(len(TIMES))]
        hourly[f"wind_gusts_10m{sfx}"] = [20] * len(TIMES)
    if "daily" not in params:
        return [{"hourly": hourly}] * n
    if not models:   # requête « soleil » sans modèle (issue #7) : variables sans suffixe, comme l'API
        return [{"daily": {"time": [d[:10] for d in TIMES[::24]], "sunrise": [d[:10] + "T08:05" for d in TIMES[::24]],
                           "sunset": [d[:10] + "T17:50" for d in TIMES[::24]]}}] * n
    # Comme l'API réelle avec plusieurs modèles : lever/coucher suffixés par modèle
    daily = {"time": [TIMES[i][:10] for i in range(0, len(TIMES), 24)],
             "sunrise_meteofrance_seamless": [d[:10] + "T08:05" for d in TIMES[::24]],
             "sunset_meteofrance_seamless": [d[:10] + "T17:50" for d in TIMES[::24]],
             "sunrise_icon_seamless": [d[:10] + "T08:06" for d in TIMES[::24]],
             "sunset_icon_seamless": [d[:10] + "T17:51" for d in TIMES[::24]]}
    return [{"hourly": hourly, "daily": daily}] * n


def fake_marc():
    t = pd.date_range(start - timedelta(hours=6), periods=70, freq="3h").tz_localize(config.TIMEZONE).tz_convert("UTC").tz_localize(None)
    lat, lon = np.arange(43.1, 45.3, 0.033), np.arange(-2.4, -0.8, 0.033)
    hs = 1.3 + 0.2 * np.sin(np.arange(len(t)))[:, None, None] * np.ones((len(t), len(lat), len(lon)))
    hs[:, :, lon > -1.35] = np.nan  # « terre »
    return xr.Dataset({"hs": (("time", "latitude", "longitude"), hs), "tp": (("time", "latitude", "longitude"), np.full(hs.shape, 12.5)),
                       "dp": (("time", "latitude", "longitude"), np.full(hs.shape, 290.0))},
                      coords={"time": t, "latitude": lat, "longitude": lon})


class FakeResp:
    def __init__(self, text="", content=b"", status_code=200):
        self.text, self.content, self.status_code = text, content, status_code
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def fake_copernicus_nc():
    """Fichier au format Copernicus In Situ : variables (TIME, DEPTH) + drapeaux QC."""
    import os, tempfile
    now = pd.Timestamp.now("UTC").floor("h").tz_localize(None)
    t = pd.date_range(now - pd.Timedelta(hours=47), now, freq="h")
    n = len(t)
    hs = np.array([1.6 + 0.05 * math.sin(h) for h in range(n)])[:, None]
    hs_qc = np.ones((n, 1), dtype="int8"); hs_qc[5] = 4  # une valeur rejetée par le QC
    tp = np.where(np.arange(n) % 3 == 0, np.nan, 13.0)[:, None]
    tp[-2] = 2.0  # période pic incohérente (< période moyenne) : doit être rejetée
    ds = xr.Dataset({"VGHS": (("TIME", "DEPTH"), hs), "VGHS_QC": (("TIME", "DEPTH"), hs_qc),
                     "VTPK": (("TIME", "DEPTH"), tp), "VGTA": (("TIME", "DEPTH"), np.full((n, 1), 5.0)),
"VDIR": (("TIME", "DEPTH"), np.full((n, 1), 290.0)),
                     "TEMP": (("TIME", "DEPTH"), np.full((n, 1), 16.5)),
                     "TIME_QC": (("TIME",), np.ones(n, dtype="int8"))}, coords={"TIME": t})
    fd, path = tempfile.mkstemp(suffix=".nc"); os.close(fd)
    ds.to_netcdf(path)
    data = open(path, "rb").read(); os.remove(path)
    return data


def fake_ibi_nc():
    """Fichier Copernicus d'une bouée du large livrée toutes les heures (variables VHM0, VTPK, VMDR, TEMP, VZMX)."""
    import os, tempfile
    now = pd.Timestamp.now("UTC").floor("h").tz_localize(None)
    t = pd.date_range(now.normalize(), now, freq="h")
    n = len(t)
    col = lambda v: np.full((n, 1), v, dtype=float)
    ds = xr.Dataset({"VHM0": (("TIME", "DEPTH"), col(0.9)), "VTPK": (("TIME", "DEPTH"), col(11.0)), "VMDR": (("TIME", "DEPTH"), col(285.0)),
                     "TEMP": (("TIME", "DEPTH"), col(17.0)), "VZMX": (("TIME", "DEPTH"), col(1.5)),
                     "TIME_QC": (("TIME",), np.ones(n, dtype="int8"))}, coords={"TIME": t})
    fd, path = tempfile.mkstemp(suffix=".nc"); os.close(fd)
    ds.to_netcdf(path)
    data = open(path, "rb").read(); os.remove(path)
    return data


def fake_candhis_html(*a, **k):
    now = pd.Timestamp.now("UTC").floor("30min")
    rows = "".join(
        f"<tr><td><span>{(now - pd.Timedelta(minutes=30 * i)):%d/%m/%Y} </span></td><td><span>{(now - pd.Timedelta(minutes=30 * i)):%H:%M} </span></td>"
        f"<td><span>{1.2 + 0.1 * math.sin(i / 3):.1f} </span></td><td><span>2.0 </span></td><td><span>9.5 </span></td><td><span>290 </span></td><td><span>20 </span></td><td><span>16.5 </span></td></tr>"
        for i in range(96))
    return FakeResp("<table><thead><tr><th>Date</th></tr></thead><tbody>" + rows + "</tbody></table>")


def fake_buoy_get(url, *a, **k):
    if "IR_TS_MO" in url:  # bouées du large fraîches : seul le fichier du jour existe
        today = pd.Timestamp.now("UTC").strftime("%Y%m%d")
        return FakeResp(content=fake_ibi_nc()) if today in url else FakeResp(status_code=404)
    if "candhis" in url:
        return fake_candhis_html()
    if "cloudferro" in url:  # Copernicus : seul le fichier du jour existe
        today = pd.Timestamp.now("UTC").strftime("%Y%m%d")
        return FakeResp(content=fake_copernicus_nc()) if today in url else FakeResp(status_code=404)
    return fake_ndbc()


def fake_ndbc(*a, **k):
    now = pd.Timestamp.now('UTC').floor("h")
    lines = ["#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS PTDY  TIDE",
             "#yr  mo dy hr mn degT m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC  nmi  hPa    ft"]
    for h in range(0, 48):
        t = now - pd.Timedelta(hours=h)
        lines.append(f"{t:%Y %m %d %H} 00 270 8.0 10.0 {1.6 + 0.05 * math.sin(h):.1f} {'13' if h % 3 else 'MM'} 8.0 MM 1020.0 14.0 16.5 MM MM MM MM")
    return FakeResp("\n".join(lines))


import os, tempfile
_hist = tempfile.mkdtemp()
os.environ["METEO_HISTORY_DIR"] = _hist     # archive de test : jamais dans le vrai dossier history/
os.environ["METEO_ARCHIVE"] = "1"
openmeteo.get = fake_get
from pipeline import omcache as _omc
_omc.model_meta = lambda kind, name, fresh=False: {"last_run_availability_time": 1_700_000_000}   # métadonnées simulées, sans réseau
marc.open_dataset = fake_marc
buoy.requests.get = fake_buoy_get
build.main()
data = json.loads(config.OUTPUT_FILE.read_text())
s = data["spots"][0]
print("modèles :", [m["key"] for m in data["meta"]["wave_models"]], "· correction bouée :", data["meta"]["buoy_correction"])
print("bouée :", data["gascogne"]["latest"], "· trajet vers", s["name"], ":", data["gascogne"]["eta_hours"][s["name"]], "h")
print("mix 1res heures :", s["marine"]["wave_height"][:4], "· erreurs :", data["meta"]["errors"])
assert data["gascogne"]["source"] == "Copernicus Marine", data["meta"]["errors"]
# --- Météo-France (réponse réelle du 09/11/2026, raccourcie) : la Gascogne est triée, convertie, sans les autres bouées
from pipeline import meteofrance
_mf = meteofrance.parse_rows([
    {"geo_id_wmo": "4100230", "validity_time": "2026-11-09T13:00:00Z", "haut_vag": 1.1, "per_moy_vag": 6.0, "dir_vag": 30.0, "tmer": 302.55},
    {"geo_id_wmo": "6200001", "validity_time": "2026-11-09T13:00:00Z", "haut_vag": 1.6, "per_moy_vag": 6.0, "dir_vag": 206.0, "tmer": 290.75},
    {"geo_id_wmo": "6200001", "validity_time": "2026-11-09T12:00:00Z", "haut_vag": 1.5, "per_moy_vag": 6.0, "dir_vag": 213.0, "tmer": 290.85},
    {"geo_id_wmo": "6200001", "validity_time": "2026-11-09T12:00:00Z", "haut_vag": 1.5, "per_moy_vag": 6.0, "dir_vag": 213.0, "tmer": 290.85},
    {"geo_id_wmo": "6101035", "validity_time": "2026-11-09T13:00:00Z", "haut_vag": None, "tmer": 294.15}])
assert list(_mf["WVHT"]) == [1.5, 1.6] and abs(_mf["WTMP"].iloc[-1] - 17.6) < 0.01 and _mf["MWD"].iloc[-1] == 206.0, _mf
w0 = data["spots"][0]["wind"]["wind_speed_10m"]
assert all(v is not None for v in w0), "le vent doit être complété quand AROME s'arrête"
assert data["spots"][0]["marine"]["secondary_swell_wave_height"][0] == 0.4
d0 = data["spots"][0]["daily"]
assert d0["sunrise"][0][11:16] == "08:05" and d0["sunset"][0][11:16] == "17:50" and len(d0) == 3, d0.keys()
# --- archive prévision/réalité : le passage a été enregistré, la fiabilité est « en cours de collecte »
from pathlib import Path
from pipeline import history
runs = list((Path(_hist) / "runs").glob("*.jsonl")); obsf = list((Path(_hist) / "obs").glob("*.json"))
assert runs and obsf, "l'archive doit contenir le passage et les mesures de la bouée"
rec = json.loads(runs[0].read_text().splitlines()[0]); assert {"mfwam", "ecmwf"} <= set(rec["models"]) and "gfs" not in rec["models"], rec["models"].keys()  # gfs : maille terre simulée au point de la bouée
assert data["reliability"]["status"] == "collecting", data["reliability"]

# --- fiabilité : biais connus → chiffres attendus (mfwam +0,2 m, gfs −0,4 m par rapport à la mesure)
_d2 = tempfile.mkdtemp(); T0 = pd.Timestamp("2026-10-01 00:00")
truth = lambda t: 1.5 + 0.5 * math.sin(t / 10)
hours = [T0 + pd.Timedelta(hours=h) for h in range(24 * 12)]
history.record("2026-10-12T00:00", None, [{"t": t.strftime("%Y-%m-%dT%H:%M"), "hs": truth(i)} for i, t in enumerate(hours)], _d2)
for r in range(0, 24 * 6, 3):
    issued = T0 + pd.Timedelta(hours=r)
    fc = {"mfwam": {"t0": issued.strftime("%Y-%m-%dT%H:00"), "hs": [truth(r + k) + 0.2 for k in range(97)]},
          "gfs": {"t0": issued.strftime("%Y-%m-%dT%H:00"), "hs": [truth(r + k) - 0.4 for k in range(97)]}}
    history.record(issued.strftime("%Y-%m-%dT%H:00"), fc, None, _d2)
rel = history.reliability("2026-10-08 00:00", _d2)
l24 = rel["leads"]["24"]
assert rel["status"] == "ok" and rel["days_collected"] == 8, rel
assert abs(l24["models"]["mfwam"]["bias"] - 0.2) < 0.02 and l24["models"]["mfwam"]["within30"] == 1.0, l24
assert abs(l24["models"]["gfs"]["bias"] + 0.4) < 0.02 and l24["models"]["gfs"]["within30"] == 0.0, l24
assert 0.04 < l24["mix"]["bias"] < 0.14, l24["mix"]   # (0,25×0,2 + 0,05×(−0,4)) / 0,30 ≈ +0,10
print("fiabilité OK · mix 24 h :", l24["mix"])

coef = data["tide_coef"]
assert coef and len(coef) >= 6 and all(20 <= c <= 125 for v in coef.values() for c in v), coef
print("coefficients :", {d[5:]: v for d, v in list(coef.items())[:3]})
names = [s["name"] for s in data["spots"]]
assert "gfs" not in data["spots"][0]["wave_models"], "un modèle à 0,00 m partout (maille terre) doit être écarté"
assert any("gfs" in s["wave_models"] for s in data["spots"][1:]), "GFS doit rester là où il est valide"
assert any("marc" in s["wave_models"] for s in data["spots"]), "MARC doit être présent"
print("vent complété sur", len(w0), "heures · houle secondaire présente")
assert data["gascogne"]["latest"]["hs"] > 0 and len(data["gascogne"]["obs"]) >= 24

assert len(data["coast"]) == 7, data["meta"]["errors"]
_cs = history.coast_summary(_hist)
from pipeline import candhis as _cd, ibi_buoys as _ib
assert set(_cs["buoys"]) == {s["id"] for s in _cd.STATIONS} | {s["id"] for s in _ib.STATIONS} and all(_cs["buoys"][k]["n"] >= 40 for k in ("03302", "06402", "06403")) and _cs["runs"] == 1, _cs
_co = json.loads(sorted((__import__("pathlib").Path(_hist) / "coast_obs").glob("*.json"))[0].read_text())["06402"]
assert any(r["dir"] is not None and r["hmax"] is not None for r in _co.values()), "direction et Hmax horaires attendus"
print("archive côtière OK :", _cs)
c0 = data["coast"][1]
assert c0["name"] == "Anglet" and c0["latest"]["hs"] > 0 and c0["latest"]["tp"] == 9.5 and len(c0["obs"]) >= 40
assert [b["name"] for b in data["offshore"]] == [s["name"] for s in _ib.STATIONS], data["meta"]["errors"]
_o = data["offshore"][0]
assert _o["latest"]["hs"] == 0.9 and _o["latest"]["tp"] == 11.0 and _o["latest"]["dir"] == 285 and len(_o["obs"]) >= 1 and _o["model"], _o["latest"]
assert "6200024" in history.coast_summary(_hist)["buoys"], "les bouées du large doivent aussi être archivées"
print("bouées du large OK :", [(b["name"], b["latest"]["hs"], b["latest"]["tp"]) for b in data["offshore"]])
print("CANDHIS OK :", [b["name"] for b in data["coast"]], c0["latest"])

import re as _re
from pipeline import pages as _content_pages
sm = (config.OUT_DIR / "sitemap.xml").read_text(encoding="utf-8")
_nb = len(data["coast"]) + len(data["offshore"]) + (1 if (data.get("gascogne") or {}).get("latest") else 0)   # pages individuelles des bouées (Gascogne comprise)
assert sm.count("<url>") == len(data["spots"]) + 3 + len(_content_pages.ALL) + _nb + 12, sm.count("<url>")
assert "Sitemap:" in (config.OUT_DIR / "robots.txt").read_text()
pg = (config.OUT_DIR / "spots" / "lacanau" / "index.html").read_text(encoding="utf-8")
assert "<h1>Prévisions surf à Lacanau</h1>" in pg and "application/ld+json" in pg and 'rel="canonical"' in pg and "<table>" in pg
assert "Houlalah" in (config.OUT_DIR / "spots" / "index.html").read_text(encoding="utf-8")
for _slug in ("comment-ca-marche", "mentions-legales", "confidentialite"):
    assert "<h1>" in (config.OUT_DIR / _slug / "index.html").read_text(encoding="utf-8"), _slug
bp = (config.OUT_DIR / "bouees" / "cap-ferret" / "index.html").read_text(encoding="utf-8")
# houlographe CANDHIS : vrai nom de l'appareil, numéro de station, source, Dataset ; liens vers les pages de spots (pas l'application)
assert "<h1>Bouée houlographe du Cap Ferret</h1>" in bp and "CANDHIS 03302" in bp and "Historique des mesures" in bp and "Source des mesures" in bp, "page bouée"
assert '"@type": "Dataset"' in bp and "../../spots/" in bp and "?spot=" not in bp.split("Spots autour")[1].split("Bouées voisines")[0]
assert "Heure par heure" in pg and "Marées à Lacanau" in pg, "page spot : heure par heure et marées"
assert "Les bouées" in (config.OUT_DIR / "bouees" / "index.html").read_text(encoding="utf-8")
# GEO : mesure datée, source visible et distinction entre mer au large et vagues au bord.
assert '<time datetime="' in bp and "heure de Paris" in bp and "Date / heure (Paris)" in bp
# Non-régression revue PR #17 (C) : bouée portugaise à l'heure du Portugal, décalage ISO 8601 conservé dans <time datetime>
import re as _re
_lx = (config.OUT_DIR / "bouees" / "leixoes" / "index.html").read_text(encoding="utf-8")
_m = _re.search(r'<time datetime="([^"]+)">[^<]*</time> \(([^)]+)\)', _lx)
assert _m and _m.group(1).endswith("+00:00") and _m.group(2) == "heure du Portugal", ("Leixões", _m and _m.groups())
assert "Date / heure (Portugal)" in _lx and "heure de Paris" not in _lx and "(Paris)" not in _lx, "Leixões : libellés à l'heure du Portugal"
_m2 = _re.search(r'<time datetime="([^"]+)">', bp)
assert _m2 and _re.search(r"[+-]\d\d:\d\d$", _m2.group(1)), ("Cap Ferret : décalage dans <time>", _m2 and _m2.group(1))
assert "Dernière mesure disponible" in bp and "la méthode Houlalah" in bp
assert "pas la hauteur des vagues au bord" in bp
_method = (config.OUT_DIR / "comment-ca-marche" / "index.html").read_text(encoding="utf-8")
assert "ne font pas l'objet de la même moyenne pondérée" in _method
assert "ne constituent pas une validation" in _method
_guide = (config.OUT_DIR / "guide" / "lire-une-bouee" / "index.html").read_text(encoding="utf-8")
assert "Comment lire une bouée houlographe ?" in _guide
assert "../../bouees/" in _guide and "../../brand/symbol.svg" in _guide
assert "/guide/lire-une-bouee/" in (config.OUT_DIR / "sitemap.xml").read_text(encoding="utf-8")
assert "guide/lire-une-bouee/" in _method
# Les liens contextuels doivent apparaître dans le contenu et viser des pages générées.
for _source, _target in [("bouees/cap-ferret", "guide/lire-une-bouee"), ("spots/lacanau", "guide/comprendre-la-houle")]:
    _source_dir = config.OUT_DIR / _source
    _main = (_source_dir / "index.html").read_text(encoding="utf-8").split("<footer>", 1)[0]
    _href = f"../../{_target}/"
    assert f'<a href="{_href}">' in _main, (_source, _href)
    assert (_source_dir / _href / "index.html").is_file(), _href
from html.parser import HTMLParser
from urllib.parse import urlsplit
class _GuideLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href and not urlsplit(href).scheme and not href.startswith("#"):
                self.links.append(href)
for _spec in _content_pages.ALL:
    if not _spec["slug"].startswith("guide"):
        continue
    _dir = config.OUT_DIR / _spec["slug"]
    _html = (_dir / "index.html").read_text(encoding="utf-8")
    assert _html.count("<h1>") == 1
    assert f'/{_spec["slug"]}/' in sm
    assert f'/{_spec["slug"]}/"' in _html
    assert _spec["h1"] in _html
    _links = _GuideLinks()
    _links.feed(_html)
    for _href in _links.links:
        _target = (_dir / urlsplit(_href).path).resolve()
        # La racine statique reste dans web/ pendant le test, seuls les HTML générés sont dans OUT_DIR.
        if _target == config.OUT_DIR.resolve():
            assert (_WEB / "index.html").is_file()
        else:
            assert _target.is_dir() and (_target / "index.html").exists(), (_spec["slug"], _href)

print("SEO OK :", len(data["spots"]), "pages de spots + index + sitemap ;", _nb, "pages de bouées")

# Secours : Copernicus indisponible → NOAA NDBC.
buoy.requests.get = lambda url, *a, **k: FakeResp(status_code=503) if "cloudferro" in url else fake_ndbc()
g = buoy.fetch([{"name": "x", "lat": 43.5, "lon": -1.5}])
assert g["source"] == "NOAA NDBC" and g["latest"]["hs"] > 0
print("bouée OK (Copernicus + secours NDBC)")

# Records et moyennes des bouées (archive locale du test)
_bs = history.buoy_stats(_hist)
assert _bs["06402"]["n"] >= 40 and _bs["06402"]["hs_max"] >= _bs["06402"]["hs_mean"] > 0, _bs["06402"]
print("records bouées OK :", {k: (v["days"], v["hs_max"]) for k, v in _bs.items()})

# Images de partage : une par spot et par bouée, annoncées dans les balises og:image
_root = config.OUT_DIR
assert (_root / "og" / "spots" / "lacanau.png").stat().st_size > 20000, "image de partage du spot absente"
assert (_root / "og" / "bouees" / "cap-ferret.png").stat().st_size > 20000, "image de partage de la bouée absente"
assert "/og/spots/lacanau.png" in (_root / "spots" / "lacanau" / "index.html").read_text(encoding="utf-8")
assert "/og/bouees/cap-ferret.png" in (_root / "bouees" / "cap-ferret" / "index.html").read_text(encoding="utf-8")
print("images de partage OK :", len(list((_root / "og" / "spots").glob("*.png"))), "spots,", len(list((_root / "og" / "bouees").glob("*.png"))), "bouées")

# Pages par zone
for _z in ("gironde", "landes", "pays-basque"):
    _h = (_root / f"meteo-surf-{_z}" / "index.html").read_text(encoding="utf-8")
    assert "<h1>Météo surf" in _h and "Les conditions du jour" in _h and "La semaine" in _h and "/spots/" in _h, _z
assert "Météo surf Landes : 25 spots" in (_root / "meteo-surf-landes" / "index.html").read_text(encoding="utf-8")
print("pages par zone OK")

# Bouée absente du passage : reprise de l'archive (source en panne, mesure récente) ou « muette » (plus de 48 h sans mesure)
from pipeline import build as _build
_coast = [b for b in _cd.fetch_all()[0] if b["id"] != "06402"]
_meta = {"errors": {}}
_build.keep_silent(_coast, [], _meta, _hist)
_a = next((b for b in _coast if b["id"] == "06402"), None)
assert _a and not _a.get("silent") and len(_a["obs"]) >= 10 and _a["latest"]["hs"] > 0 and not _meta["errors"], (_a, _meta)
assert sum(1 for b in _coast if b["id"] == "06402") == 1
print("bouée reprise de l'archive OK :", _a["name"], _a["latest"]["time"], len(_a["obs"]), "mesures")
_old = tempfile.mkdtemp(); os.makedirs(os.path.join(_old, "coast_obs"))
_t = (pd.Timestamp.now(tz=config.TIMEZONE).tz_localize(None) - pd.Timedelta(days=5)).strftime("%Y-%m-%dT%H:00")
open(os.path.join(_old, "coast_obs", _t[:7] + ".json"), "w").write(json.dumps({"06402": {_t: {"hs": 1.8, "tp": 8.1}}}))
_coast = [b for b in _coast if b["id"] != "06402"]
_build.keep_silent(_coast, [], _meta, _old)
_a = next(b for b in _coast if b["id"] == "06402")
assert _a["silent"] and _a["obs"] == [] and _a["latest"]["time"] == _t, _a
print("bouée muette OK :", _a["name"], _a["latest"]["time"])
_stale = [{"id": "x", "name": "Vieille", "lat": 43.5, "lon": -1.6, "obs": [], "latest": {"time": _t, "hs": 1.8}}]
_build.keep_silent(_stale, [], _meta, _old)
assert _stale[0].get("silent"), _stale[0]
print("vieille mesure renvoyée par la source → muette OK")

# Titres et descriptions dans les limites de Google (sinon il les coupe) sur toutes les pages générées
import html as _html, re as _re
_long = []
for _f in _root.rglob("index.html"):
    _t = _f.read_text(encoding="utf-8")
    _ti = _re.search(r"<title>(.*?)</title>", _t, _re.S)
    _de = _re.search(r'<meta name="description" content="(.*?)"', _t)
    if _ti and len(_html.unescape(_ti.group(1))) > 60: _long.append(("titre", _f.parent.name, _html.unescape(_ti.group(1))))
    if _de and len(_html.unescape(_de.group(1))) > 160: _long.append(("desc", _f.parent.name, len(_html.unescape(_de.group(1)))))
assert not _long, _long[:5]
print("titres ≤ 60 et descriptions ≤ 160 OK :", len(list(_root.rglob("index.html"))), "pages")

# Éditeur, page « À propos », pays des spots, robots des IA et llms.txt
_ap = (_root / "a-propos" / "index.html").read_text(encoding="utf-8")
assert '"@type": "AboutPage"' in _ap and '"@type": "Organization"' in _ap and "contact@houlalah.fr" in _ap
_lk = (_root / "spots" / "lacanau" / "index.html").read_text(encoding="utf-8")
assert '"publisher": {"@id": "https://houlalah.fr/#org"}' in _lk and '"addressCountry": "FR"' in _lk and "a-propos/" in _lk
_es = next(_f for _f in (_root / "spots").glob("*/index.html") if "Espagne" in _f.read_text(encoding="utf-8")[:6000])
assert '"addressCountry": "ES"' in _es.read_text(encoding="utf-8"), _es
_rb = (_root / "robots.txt").read_text(encoding="utf-8")
assert "OAI-SearchBot" in _rb and "Claude-SearchBot" in _rb and "Sitemap:" in _rb
_ll = (_root / "llms.txt").read_text(encoding="utf-8")
assert _ll.startswith("# Houlalah") and "/bouees/" in _ll and "/meteo-surf-landes/" in _ll
print("éditeur, à propos, pays, robots IA et llms.txt OK")

# Isolation (issue #3) : le test n'a rien écrit dans web/, et tout ce qu'il a produit porte la marque de test.
_after = _snap()
_diff = sorted(set(_before.items()) ^ set(_after.items()))
assert not _diff, f"le test a modifié web/ ({len(_diff)} fichier(s), ex. {_diff[:3]}) : il ne doit écrire que dans le dossier temporaire"
assert all(json.loads(f.read_text(encoding="utf-8")).get("_test") is True for f in (config.OUT_DIR / "data" / "app" / "spots").glob("*.json"))
assert json.loads((config.OUT_DIR / "data" / "forecast.json").read_text())["meta"].get("_test") is True
assert json.loads((config.OUT_DIR / "data" / "app" / "index.json").read_text(encoding="utf-8")).get("_test") is True
assert 'name="houlalah-test"' in (config.OUT_DIR / "spots" / "lacanau" / "index.html").read_text(encoding="utf-8")
assert json.loads((config.OUT_DIR / "health.json").read_text(encoding="utf-8")).get("_test") is True
# le contrôle de publication refuse ce site de test (marques de test, données simulées)
from tools import check_site as _cs
_ok, _rep = _cs.check(config.OUT_DIR, max_age_h=None)
assert not _ok and any("test" in x for x in _rep["errors"]), "le contrôle de publication doit refuser un site de test"
print("isolation OK :", len(_before), "fichiers de web/ inchangés, aucun ajouté ; site de test refusé par le contrôle (", len(_rep["errors"]), "motifs )")

# Issue #1 (revue de la PR #20, point 5) : la prévision PUBLIÉE est identique, archive activée ou désactivée.
# Empreintes normalisées des séries des 214 spots (tools/compare_forecast.py, utilisable aussi entre deux commits).
from tools import compare_forecast as _cf
from pipeline import appdata as _ad, seo as _seo
_with = json.loads((config.OUT_DIR / "data" / "forecast.json").read_text())
(_Path(_hist) / "forecast_archive_on.json").write_text(json.dumps(_with), encoding="utf-8")   # pour comparer à un autre commit
print("forecast.json (archive activée) gardé pour comparaison :", _Path(_hist) / "forecast_archive_on.json")
_os.environ["METEO_ARCHIVE"] = "0"
_seo.generate, _ad.generate = (lambda payload: 0), (lambda spots, payload: 0)   # pages déjà vérifiées plus haut : on gagne du temps
build.main()
_without = json.loads((config.OUT_DIR / "data" / "forecast.json").read_text())
_r = _cf.compare(_with, _without)
assert not _r["diffs"] and _r["spots"] == (214, 214) and _r["global"][0] == _r["global"][1], _r["diffs"][:5]
print("prévision publiée identique archive activée / désactivée :", _r["spots"][0], "spots, empreinte", _r["global"][0][:16])
