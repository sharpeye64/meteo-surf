"""Test minute de la clé Météo-France : affiche seulement le code de réponse et l'âge de la dernière mesure Gascogne.
La clé reste dans ta session PowerShell (jamais affichée) :
    $env:METEOFRANCE_APIKEY = "ta_clé"
    python -m tools.mf_check
"""
import os
import sys

import requests

from pipeline import meteofrance

key = os.environ.get("METEOFRANCE_APIKEY", "").strip()
if not key:
    sys.exit("Définis d'abord $env:METEOFRANCE_APIKEY")
r = requests.get(meteofrance.BASE + "/bouees", headers={"apikey": key, "accept": "application/json"}, params={"format": "json"}, timeout=60)
print("Code HTTP :", r.status_code)
if r.status_code != 200:
    print("Message :", r.text[:300].replace(key, "***"))
else:
    try:
        df = meteofrance.parse_rows(r.json())
        print("Dernière mesure Gascogne :", df["time"].max(), "(UTC)")
    except Exception as e:
        print("Réponse reçue mais illisible :", str(e)[:200])
