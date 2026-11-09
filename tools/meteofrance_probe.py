"""Sonde de l'API Météo-France « Données d'observation » (v2) pour les bouées ancrées (dont la Gascogne, 62001).

À lancer PAR TOI, sur ton ordinateur, avec ta clé : elle reste dans ta session et n'est jamais affichée ni enregistrée.
  1. Sur https://portail-api.meteofrance.fr : page « API Données d'observation » > « Souscrire à l'API gratuitement »,
     puis génère une clé API (ou un jeton) dans ton compte.
  2. PowerShell, dans le dossier du projet :
        cd C:\\Users\\andre\\Downloads\\meteo-surf\\meteo-surf
        $env:METEOFRANCE_APIKEY = "ta_clé_ici"          (ou  $env:METEOFRANCE_TOKEN = "..."  si c'est un jeton OAuth2)
        .venv\\Scripts\\python -m tools.meteofrance_probe
  3. Copie-colle la sortie dans la conversation : elle ne contient que la structure des réponses, pas ta clé.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import requests

BASES = ["https://public-api.meteofrance.fr/public/DPObs/v2", "https://public-api.meteofrance.fr/public/DPObs/v1"]


def headers():
    if os.environ.get("METEOFRANCE_TOKEN"):
        return {"Authorization": "Bearer " + os.environ["METEOFRANCE_TOKEN"], "accept": "application/json"}
    if os.environ.get("METEOFRANCE_APIKEY"):
        return {"apikey": os.environ["METEOFRANCE_APIKEY"], "accept": "application/json"}
    sys.exit("Aucune clé : définis METEOFRANCE_APIKEY ou METEOFRANCE_TOKEN (voir l'en-tête de ce fichier).")


def show(title, r, limit=1800):
    print(f"\n=== {title} -> HTTP {r.status_code} ({r.headers.get('content-type', '')[:40]})")
    body = r.text
    try:
        body = json.dumps(r.json(), ensure_ascii=False, indent=1)
    except ValueError:
        pass
    print(body[:limit] + ("\n[...tronqué]" if len(body) > limit else ""))


def find_gascogne(node):
    """Premier élément de la liste dont une valeur texte contient « gascogne » ou le numéro 62001."""
    if isinstance(node, dict):
        if any(isinstance(v, str) and ("gascogne" in v.lower() or v.strip() in ("62001", "6200001")) for v in node.values()):
            return node
        for v in node.values():
            f = find_gascogne(v)
            if f:
                return f
    elif isinstance(node, list):
        for v in node:
            f = find_gascogne(v)
            if f:
                return f
    return None


def main():
    h = headers()
    for base in BASES:
        r = requests.get(f"{base}/liste-bouees", headers=h, timeout=40)
        show(f"{base}/liste-bouees", r, 1200)
        if r.status_code != 200:
            continue
        try:
            data = r.json()
        except ValueError:
            return
        g = find_gascogne(data)
        print("\n>>> Entrée trouvée pour la Gascogne :", json.dumps(g, ensure_ascii=False) if g else "AUCUNE (voir la liste ci-dessus)")
        if not g:
            return
        ident = next((str(v) for k, v in g.items() if ("id" in k.lower() or "numer" in k.lower()) and v), None) or "6200001"
        when = (datetime.now(timezone.utc) - timedelta(hours=3)).replace(minute=0, second=0, microsecond=0)
        for idk in ("id", "id_station", "id_bouee", "station"):
            for dk, fmt in (("date", "%Y-%m-%dT%H:%M:%SZ"), ("date_heure", "%Y-%m-%dT%H:%M:%SZ"), ("date", "%Y%m%d%H")):
                r2 = requests.get(f"{base}/bouees", headers=h, params={idk: ident, dk: when.strftime(fmt)}, timeout=40)
                if r2.status_code == 200:
                    show(f"{base}/bouees?{idk}=<id>&{dk}=<date> (fonctionne)", r2, 3500)
                    return
                if (idk, dk, fmt) == ("id", "date", "%Y-%m-%dT%H:%M:%SZ"):
                    show(f"{base}/bouees?{idk}=<id>&{dk}=<date> (premier essai)", r2, 800)
        print("\nAucune combinaison de paramètres n'a fonctionné : colle la sortie ci-dessus, je regarderai la documentation.")
        return


if __name__ == "__main__":
    main()
