# Contexte pour Claude Code

Prototype de site de prévisions surf (côte Lacanau → Hendaye) pour concurrencer Yadusurf. L'utilisateur
n'est pas développeur : expliquer en français, simplement, une étape à la fois.

## Architecture
- `pipeline/` (Python) : `build.py` orchestre ; `openmeteo.py`, `marc.py`, `buoy.py`, `tides.py` sont les sources.
  Toute source sauf Open-Meteo peut échouer sans bloquer la génération (erreurs listées dans `meta.errors`).
- `web/index.html` : site statique autonome (WebGL, Leaflet via jsDelivr, trait de côte embarqué). Il lit
  `web/data/forecast.json` et, à défaut, appelle Open-Meteo en direct (`loadLive`).
- `.github/workflows/update.yml` : génération toutes les 3 h et publication sur GitHub Pages.
- `tests/test_offline.py` : tout le pipeline avec des sources simulées. À garder vert.

## Points à vérifier au premier vrai lancement (non testés en conditions réelles)
1. Noms des modèles de vagues Open-Meteo (`config.WAVE_MODELS`) : le code essaie plusieurs noms et ignore ceux refusés.
2. MARC : URL OPeNDAP (`config.MARC_OPENDAP_URLS`) et noms de variables (`marc.py` : HS/TP/FP/DIR). En cas d'échec,
   ouvrir le dataset et afficher `list(ds.variables)`, puis ajuster. Catalogue : marc.ifremer.fr / sextant.ifremer.fr.
3. Bouée 62001 : source Copernicus Marine In Situ (fichier NetCDF journalier, code 6200001, `config.GASCOGNE`), NDBC en secours
   (NDBC ne publiait plus cette bouée en novembre 2026). Période pic absente → on prend celle du modèle.
4. Format des fichiers REFMAR téléchargés (`tools/fit_tides.py:read_refmar`) : séparateur et colonnes peuvent varier.
5. Volume d'appels Open-Meteo : environ 30 points × (1 + 4 modèles) + vent toutes les 3 h. Rester sous les limites gratuites.

## Pistes suivantes
- Bouée CANDHIS d'Anglet (Licence Ouverte) en « vérité terrain » près de la côte, avec comparaison H1/3 et TH1/3.
- Coefficient de marée, calibration `tide_offset_min` par spot, réglages de spots validés sur le terrain.
- Statistiques publiques de fiabilité (écart prévision / bouée).
