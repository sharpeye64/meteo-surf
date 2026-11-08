"""Modèle côtier Ifremer MARC (WAVEWATCH III, Golfe de Gascogne), lu via OPeNDAP.

Le fichier est un NetCDF distant : on ne charge que la zone Lacanau → Hendaye et la fenêtre
de temps utile, puis on prend pour chaque spot la maille « mer » valide la plus proche.
"""
import numpy as np
import pandas as pd
import xarray as xr

from . import config

HS = ["hs", "HS", "swh", "VHM0"]
TP = ["tp", "TP", "t0m1", "t02", "VTPK"]
FP = ["fp", "FP"]  # fréquence pic (Hz), convertie en période
DIR = ["dp", "dir", "DIR", "VMDR", "mdir"]
BBOX = dict(lat=(43.1, 45.3), lon=(-2.4, -0.8))


def _first(ds, names):
    return next((n for n in names if n in ds.variables), None)


def _coord(ds, names):
    return next(n for n in names if n in ds.coords or n in ds.variables)


def open_dataset():
    last = None
    for url in config.MARC_OPENDAP_URLS:
        try:
            return xr.open_dataset(url, decode_times=True)
        except Exception as e:  # serveur indisponible, URL changée…
            last = e
    raise RuntimeError(f"MARC inaccessible : {last}")


def fetch(sea_points, target_times_local):
    """Retourne, pour chaque point, hs/période/direction interpolés sur les heures locales demandées."""
    ds = open_dataset()
    lat_n, lon_n = _coord(ds, ["latitude", "lat"]), _coord(ds, ["longitude", "lon"])
    hs_n, dir_n = _first(ds, HS), _first(ds, DIR)
    tp_n, fp_n = _first(ds, TP), _first(ds, FP)
    if not hs_n:
        raise RuntimeError(f"variable hauteur introuvable, variables : {list(ds.variables)}")

    t_local = pd.to_datetime(target_times_local).tz_localize(config.TIMEZONE, ambiguous="NaT", nonexistent="shift_forward")
    t_utc = t_local.tz_convert("UTC").tz_localize(None)
    lat = ds[lat_n]
    lat_slice = slice(*BBOX["lat"]) if float(lat[0]) < float(lat[-1]) else slice(*BBOX["lat"][::-1])
    sub = ds.sel({lat_n: lat_slice, lon_n: slice(*BBOX["lon"]),
                  "time": slice(t_utc.min() - pd.Timedelta("3h"), t_utc.max() + pd.Timedelta("3h"))})
    keep = [v for v in (hs_n, tp_n, fp_n, dir_n) if v]
    sub = sub[keep].load()

    lats, lons = sub[lat_n].values, sub[lon_n].values
    valid = np.isfinite(sub[hs_n].isel(time=0).values)
    out = []
    for la, lo in sea_points:
        dist = (lats[:, None] - la) ** 2 + ((lons[None, :] - lo) * np.cos(np.radians(la))) ** 2
        dist = np.where(valid, dist, np.inf)
        iy, ix = np.unravel_index(np.argmin(dist), dist.shape)
        cell = sub.isel({lat_n: iy, lon_n: ix})
        src_t = pd.to_datetime(cell["time"].values)
        # Même unité de temps des deux côtés (xarray récent décode en s/ms/µs, pas forcément en ns).
        x_src = np.asarray(src_t.values, dtype="datetime64[ns]").astype("int64")
        x_dst = np.asarray(t_utc.values, dtype="datetime64[ns]").astype("int64")

        def interp(values, angle=False):
            v = np.asarray(values, dtype=float)
            ok = np.isfinite(v)
            if ok.sum() < 2:
                return [None] * len(x_dst)
            if angle:  # interpolation des directions via sinus/cosinus
                s = np.interp(x_dst, x_src[ok], np.sin(np.radians(v[ok])))
                c = np.interp(x_dst, x_src[ok], np.cos(np.radians(v[ok])))
                res = (np.degrees(np.arctan2(s, c)) + 360) % 360
            else:
                res = np.interp(x_dst, x_src[ok], v[ok])
            res[(x_dst < x_src[ok].min()) | (x_dst > x_src[ok].max())] = np.nan
            return [None if not np.isfinite(r) else round(float(r), 2) for r in res]

        if tp_n:
            period = cell[tp_n].values
        elif fp_n:
            with np.errstate(divide="ignore"):
                period = 1.0 / cell[fp_n].values
        else:
            period = np.full(len(src_t), np.nan)
        out.append({"hs": interp(cell[hs_n].values), "tp": interp(period),
                    "dir": interp(cell[dir_n].values, angle=True) if dir_n else None,
                    "cell": [round(float(lats[iy]), 4), round(float(lons[ix]), 4)]})
    return out
