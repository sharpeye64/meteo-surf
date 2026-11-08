"""Test hors ligne du pipeline : toutes les sources sont simulées.  python -m tests.test_offline"""
import json
import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import xarray as xr

from pipeline import build, buoy, config, marc, openmeteo

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
        return [{"hourly": hourly}] * n
    hourly = {"time": TIMES}
    for _k, _l, api in config.WIND_MODELS:
        hourly[f"wind_speed_10m_{api}"] = [10 + i % 12 for i in range(len(TIMES))]
        if api == "meteofrance_seamless":  # AROME s'arrête avant la fin : le vent doit être complété par un autre modèle
            hourly[f"wind_speed_10m_{api}"][-48:] = [None] * 48
        hourly[f"wind_direction_10m_{api}"] = [100 if i % 24 < 12 else 280 for i in range(len(TIMES))]
        hourly[f"wind_gusts_10m_{api}"] = [20] * len(TIMES)
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


def fake_buoy_get(url, *a, **k):
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


openmeteo.get = fake_get
marc.open_dataset = fake_marc
buoy.requests.get = fake_buoy_get
build.main()
data = json.loads(config.OUTPUT_FILE.read_text())
s = data["spots"][0]
print("modèles :", [m["key"] for m in data["meta"]["wave_models"]], "· correction bouée :", data["meta"]["buoy_correction"])
print("bouée :", data["gascogne"]["latest"], "· trajet vers", s["name"], ":", data["gascogne"]["eta_hours"][s["name"]], "h")
print("mix 1res heures :", s["marine"]["wave_height"][:4], "· erreurs :", data["meta"]["errors"])
assert data["gascogne"]["source"] == "Copernicus Marine", data["meta"]["errors"]
w0 = data["spots"][0]["wind"]["wind_speed_10m"]
assert all(v is not None for v in w0), "le vent doit être complété quand AROME s'arrête"
assert data["spots"][0]["marine"]["secondary_swell_wave_height"][0] == 0.4
d0 = data["spots"][0]["daily"]
assert d0["sunrise"][0].endswith("T08:05") and d0["sunset"][0].endswith("T17:50") and len(d0) == 3, d0.keys()
print("vent complété sur", len(w0), "heures · houle secondaire présente")
assert data["gascogne"]["latest"]["hs"] > 0 and len(data["gascogne"]["obs"]) >= 24

# Secours : Copernicus indisponible → NOAA NDBC.
buoy.requests.get = lambda url, *a, **k: FakeResp(status_code=503) if "cloudferro" in url else fake_ndbc()
g = buoy.fetch([{"name": "x", "lat": 43.5, "lon": -1.5}])
assert g["source"] == "NOAA NDBC" and g["latest"]["hs"] > 0
print("bouée OK (Copernicus + secours NDBC)")
