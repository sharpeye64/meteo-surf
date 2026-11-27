"""Compare la prévision PUBLIÉE de deux forecast.json, série par série (issue #1 : l'archive ne doit pas la changer).

Usage : python -m tools.compare_forecast A/forecast.json B/forecast.json
Pour chaque spot : empreinte SHA-256 de ses séries normalisées (JSON trié, valeurs telles que publiées), hors métadonnées du
passage (heure de génération, compteurs). Affiche l'empreinte globale des deux fichiers et les séries qui diffèrent.
Code de sortie 0 si toutes les séries des spots sont identiques.
"""
import hashlib
import json
import sys

KEYS = ("marine", "wave_models", "wind", "wind_models", "daily", "tide")


def spot_digest(sp):
    return {k: hashlib.sha256(json.dumps(sp.get(k), sort_keys=True, separators=(",", ":")).encode()).hexdigest() for k in KEYS}


def digests(payload):
    """{nom du spot: {série: empreinte}} + empreinte globale (spots triés par nom) + réglages publiés du mélange."""
    per = {sp["name"]: spot_digest(sp) for sp in payload["spots"]}
    extra = {k: payload["meta"].get(k) for k in ("buoy_correction", "wave_models", "wind_models")}
    glob = hashlib.sha256(json.dumps([per, extra], sort_keys=True).encode()).hexdigest()
    return per, glob


def compare(a, b):
    pa, ga = digests(a)
    pb, gb = digests(b)
    diffs = [(n, k) for n in sorted(set(pa) | set(pb)) for k in KEYS if (pa.get(n) or {}).get(k) != (pb.get(n) or {}).get(k)]
    return {"spots": (len(pa), len(pb)), "global": (ga, gb), "diffs": diffs}


def main(fa, fb):
    a, b = (json.load(open(f, encoding="utf-8")) for f in (fa, fb))
    r = compare(a, b)
    print(f"spots : {r['spots'][0]} / {r['spots'][1]}")
    print(f"empreinte globale A : {r['global'][0]}")
    print(f"empreinte globale B : {r['global'][1]}")
    if r["diffs"]:
        print(f"{len(r['diffs'])} séries différentes, par exemple : {r['diffs'][:10]}")
        return 1
    print(f"identiques : {r['spots'][0]} spots × {len(KEYS)} séries ({', '.join(KEYS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
