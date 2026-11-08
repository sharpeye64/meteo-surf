"""Télécharge 1 an de hauteurs d'eau validées d'un marégraphe REFMAR (Shom, Licence Ouverte), sans compte.

    python -m tools.get_refmar socoa      # écrit tides/raw/socoa.txt
    python -m tools.get_refmar boucau     # écrit tides/raw/boucau.txt
    python -m tools.get_refmar brest      # écrit tides/raw/brest.txt (sert au coefficient de marée)

Données « validées temps différé » (une mesure toutes les 10 min, heure UTC). Elles sont publiées avec
quelques mois de retard : par défaut on prend les 12 mois qui se terminent il y a 90 jours.
Ensuite : python -m tools.fit_tides tides/raw/socoa.txt socoa 43.395
"""
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
URL = "https://services.data.shom.fr/maregraphie/observation/json/{}"
STATIONS = {"socoa": 95, "boucau": 94, "brest": 3}  # numéros REFMAR : Socoa, Bayonne Boucau, Brest (port de référence des coefficients)
SOURCE_VALIDEE_10MIN = 3


def main(port, end=None, days=364):
    if port not in STATIONS:
        raise SystemExit(f"Port inconnu : {port}. Choix : {', '.join(STATIONS)}")
    end = end or date.today() - timedelta(days=90)
    start = end - timedelta(days=days)
    out = ROOT / "tides" / "raw" / f"{port}.txt"
    n, cur = 0, start
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# REFMAR station {STATIONS[port]}, validées temps différé (10 min), UTC. © Shom, Licence Ouverte.\n")
        while cur <= end:
            stop = min(cur + timedelta(days=30), end)
            for attempt in range(3):
                r = requests.get(URL.format(STATIONS[port]), timeout=90,
                                 params={"sources": SOURCE_VALIDEE_10MIN, "dtStart": cur.isoformat(), "dtEnd": stop.isoformat()},
                                 headers={"User-Agent": "meteo-surf-prototype (non commercial)"})
                if r.status_code == 200:
                    break
                time.sleep(5)
            r.raise_for_status()
            for p in r.json()["data"]:
                if p["value"] is not None:
                    f.write(p["timestamp"].replace("/", "-") + ";" + str(p["value"]) + "\n")
                    n += 1
            print(f"  {cur} → {stop} : {n} mesures", flush=True)
            cur = stop + timedelta(days=1)
            time.sleep(1)
    if n < 30 * 24 * 6:
        raise SystemExit(f"Seulement {n} mesures reçues : période sans données validées ? Essaie un autre port ou plus tôt.")
    print(f"OK : {out.relative_to(ROOT)} ({n} mesures, {start} → {end})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage : python -m tools.get_refmar <socoa|boucau> [AAAA-MM-JJ de fin]")
    main(sys.argv[1], date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else None)
