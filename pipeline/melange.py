"""Mélange des modèles de vagues et correction par la bouée Gascogne : LE calcul de la prévision publiée.

Extrait de build.py (issue #1) pour que l'archive aux points des bouées utilise exactement le même calcul que les spots,
sans copie qui pourrait diverger. Aucun changement de méthode : mêmes poids, même ordre des opérations.
"""
import pandas as pd

from . import config

VERSION = "melange-1"   # à changer si la méthode change (poids, repli, correction) : l'archive le note à chaque passage


def correction(times, ratio, start):
    """Facteur de correction de chaque heure : ratio mesuré à `start` (heure de la mesure), ramené linéairement à 1 sur
    BUOY_CORRECTION_HOURS. `times` : heures écrites comme l'axe Open-Meteo ; `start` : pd.Timestamp sans fuseau."""
    corr = [1.0] * len(times)
    if ratio:
        for j, t in enumerate(times):
            dt = (pd.Timestamp(t) - start) / pd.Timedelta("1h")
            if 0 <= dt <= config.BUOY_CORRECTION_HOURS:
                corr[j] = 1 + (ratio - 1) * (1 - dt / config.BUOY_CORRECTION_HOURS)
    return corr


def blend(models, weights, base, n):
    """Mélange BRUT, heure par heure : moyenne pondérée des modèles disponibles ; à défaut, la série de repli `base`."""
    raw = []
    for j in range(n):
        num = den = 0.0
        for k, arr in models.items():
            v = arr[j] if j < len(arr) else None
            if v is not None:
                num += v * weights.get(k, 0.1)
                den += weights.get(k, 0.1)
        b = base[j] if base is not None and j < len(base) else None
        raw.append(num / den if den else b)
    return raw


def corrected(raw, corr):
    """Mélange CORRIGÉ (celui qui est publié) : mélange brut × facteur de correction."""
    return [None if v is None else v * c for v, c in zip(raw, corr)]
