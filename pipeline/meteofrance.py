"""Bouée Gascogne (62001) : mesures horaires officielles de Météo-France (API « Données d'observation » v2).

Une mesure par heure pleine, publiée environ 10 minutes plus tard, sur les 24 dernières heures.
Il faut une clé API gratuite (portail-api.meteofrance.fr) dans la variable d'environnement METEOFRANCE_APIKEY :
en local dans PowerShell, sur GitHub dans le secret du même nom. Sans clé, ce module ne fait rien (erreur claire).

Champs utilisés : haut_vag (hauteur des vagues, m), per_moy_vag (période MOYENNE, s : pas la période pic),
dir_vag (direction d'où vient la houle, °), tmer (température de l'eau, kelvin).
"""
import os

import numpy as np
import pandas as pd
import requests

BASE = "https://public-api.meteofrance.fr/public/DPObs/v2"
WMO_ID = "6200001"


def parse_rows(rows, wmo_id=WMO_ID):
    """Liste de dictionnaires JSON -> tableau au format de pipeline.buoy (colonnes time, WVHT, APD, MWD, WTMP)."""
    keep = [r for r in rows if str(r.get("geo_id_wmo", "")).strip() == wmo_id]
    if not keep:
        raise RuntimeError("Météo-France : la bouée Gascogne n'est pas dans la réponse")
    df = pd.DataFrame(keep)
    num = lambda c: pd.to_numeric(df[c], errors="coerce") if c in df else np.nan
    out = pd.DataFrame({
        "time": pd.to_datetime(df["validity_time"], utc=True),
        "WVHT": num("haut_vag"), "APD": num("per_moy_vag"), "MWD": num("dir_vag"),
        "WTMP": num("tmer") - 273.15, "DPD": np.nan})
    out = out.drop_duplicates("time", keep="last").sort_values("time").reset_index(drop=True)
    if out["WVHT"].notna().sum() == 0:
        raise RuntimeError("Météo-France : pas de hauteur de vagues valide")
    return out


def load():
    key = os.environ.get("METEOFRANCE_APIKEY", "").strip()
    if not key:
        raise RuntimeError("Météo-France : clé API absente (METEOFRANCE_APIKEY)")
    headers = {"apikey": key, "accept": "application/json"}
    rows = []
    for path in ("liste-bouees", "bouees"):  # historique 24 h, puis dernière mesure
        try:
            r = requests.get(f"{BASE}/{path}", headers=headers, params={"format": "json"}, timeout=60)
            r.raise_for_status()
            rows += r.json()
        except Exception:
            if path == "liste-bouees":
                raise
    return parse_rows(rows)
