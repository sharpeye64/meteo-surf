"""Prototype issue #6 : aucune requête réseau ni écriture de production.
Usage : python -m tools.benchmark_home_index chemin/forecast.json
Compare le poids brut et gzip ; conserve les valeurs sources sans arrondi.
"""
import gzip
import json
import sys
from pathlib import Path


def compact(payload):
    times = []
    time_ids = {}
    spots = []
    for spot in payload["spots"]:
        m, w = spot["marine"], spot["wind"]
        t = tuple(m["time"])
        if t not in time_ids:
            time_ids[t] = len(times)
            times.append(list(t))
        rows = []
        def get(obj, key, i):
            a = obj.get(key) or []
            return a[i] if i < len(a) else None
        for i in range(len(t)):
            H = get(m, "wave_height", i)
            sw = get(m, "swell_wave_height", i)
            swp = get(m, "swell_wave_period", i)
            swd = get(m, "swell_wave_direction", i)
            dom = sw is not None and bool(H) and sw >= .4 * H and swp is not None
            T = swp if dom else get(m, "wave_period", i)
            D = swd if dom and swd is not None else get(m, "wave_direction", i)
            rows.append([H, T, D, get(w, "wind_speed_10m", i), get(w, "wind_direction_10m", i)])
        spots.append({"name": spot["name"], "tz": spot.get("tz"), "time": time_ids[t], "rows": rows})
    def buoy(b):
        return {k: v for k, v in b.items() if k not in ("obs", "model")}
    return {"v": 1, "meta": payload["meta"], "columns": ["H", "T", "D", "v", "wd"],
            "times": times, "spots": spots,
            "coast": [buoy(b) for b in payload.get("coast") or []],
            "offshore": [buoy(b) for b in payload.get("offshore") or []],
            "gascogne": buoy(payload["gascogne"]) if payload.get("gascogne") else None}


def encode(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def benchmark(payload):
    a, b = encode(payload), encode(compact(payload))
    return {"full_bytes": len(a), "index_bytes": len(b),
            "full_gzip_bytes": len(gzip.compress(a)), "index_gzip_bytes": len(gzip.compress(b))}


if __name__ == "__main__":
    print(json.dumps(benchmark(json.loads(Path(sys.argv[1]).read_text())), indent=2))
