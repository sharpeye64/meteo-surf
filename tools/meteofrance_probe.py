"""Sonde de l'API Météo-France « Données d'observation » pour les bouées ancrées (dont la Gascogne, 62001).

À lancer PAR TOI, sur ton ordinateur, avec ta clé : elle reste dans ta session et n'est jamais affichée ni enregistrée.
  1. Crée un compte gratuit sur https://portail-api.meteofrance.fr, abonne-toi à l'API « Données d'observation »
     (DonneesPubliquesObservation) et génère une clé / un jeton.
  2. PowerShell :   $env:METEOFRANCE_TOKEN = "ta_clé_ici"      puis      python -m tools.meteofrance_probe
     (si le portail t'a donné une « API key » plutôt qu'un jeton OAuth2 :  $env:METEOFRANCE_APIKEY = "..." )
  3. Copie-colle la sortie dans la conversation : elle ne contient que la structure des réponses, pas ta clé.
"""
import json
import os
import sys

import requests

BASES = ["https://public-api.meteofrance.fr/public/DPObs/v2", "https://public-api.meteofrance.fr/public/DPObs/v1"]


def headers():
    if os.environ.get("METEOFRANCE_TOKEN"):
        return {"Authorization": "Bearer " + os.environ["METEOFRANCE_TOKEN"], "accept": "application/json"}
    if os.environ.get("METEOFRANCE_APIKEY"):
        return {"apikey": os.environ["METEOFRANCE_APIKEY"], "accept": "application/json"}
    sys.exit("Aucune clé : définis METEOFRANCE_TOKEN ou METEOFRANCE_APIKEY (voir l'en-tête de ce fichier).")


def show(title, r):
    print(f"\n=== {title} -> HTTP {r.status_code} ({r.headers.get('content-type', '')[:40]})")
    body = r.text
    try:
        body = json.dumps(r.json(), ensure_ascii=False, indent=1)
    except ValueError:
        pass
    print(body[:2500] + ("\n[...tronqué]" if len(body) > 2500 else ""))


def main():
    h = headers()
    for base in BASES:
        r = requests.get(f"{base}/liste-bouees", headers=h, timeout=40)
        show(f"{base}/liste-bouees", r)
        if r.status_code == 200:
            for path in ("/bouees?id=6200001", "/bouees?id=6200001&date=latest"):
                show(base + path, requests.get(base + path, headers=h, timeout=40))
            break


if __name__ == "__main__":
    main()
