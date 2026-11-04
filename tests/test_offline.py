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
                  "sea_level_height_msl": [math.sin(i / 12.42 * 2 * math.pi) for i in range(len(tt))],
                  "sea_surface_temperature": [16.8] * len(tt)}
        return [{"hourly": hourly}] * n
    hourly = {"time": TIMES}
    for _k, _l, api in config.WIND_MODELS:
        hourly[f"wind_speed_10m_{api}"] = [10 + i % 12 for i in range(len(TIMES))]
        hourly[f"wind_direction_10m_{api}"] = [100 if i % 24 < 12 else 280 for i in range(len(TIMES))]
        hourly[f"wind_gusts_10m_{api}"] = [20] * len(TIMES)
    daily = {"time": [TIMES[i][:10] for i in range(0, len(TIMES), 24)], "sunrise": [d[:10] + "T08:05" for d in TIMES[::24]],
             "sunset": [d[:10] + "T17:50" for d in TIMES[::24]]}
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
    def __init__(self, text): self.text = text
    def raise_for_status(self): pass


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
buoy.requests.get = fake_ndbc
build.main()
data = json.loads(config.OUTPUT_FILE.read_text())
s = data["spots"][0]
print("modèles :", [m["key"] for m in data["meta"]["wave_models"]], "· correction bouée :", data["meta"]["buoy_correction"])
print("bouée :", data["gascogne"]["latest"], "· trajet vers", s["name"], ":", data["gascogne"]["eta_hours"][s["name"]], "h")
print("mix 1res heures :", s["marine"]["wave_height"][:4], "· erreurs :", data["meta"]["errors"])
