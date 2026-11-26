"""Réglages centraux du pipeline de prévision."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPOTS_FILE = ROOT / "pipeline" / "spots.json"
TIDE_CONSTANTS_DIR = ROOT / "tides" / "constants"
# Sources du site (web/) et dossier où le robot ÉCRIT ce qu'il génère. Par défaut le même ; METEO_OUT_DIR permet de générer
# ailleurs : les tests écrivent dans un dossier temporaire (jamais dans web/), le robot GitHub dans _site/ contrôlé avant publication.
WEB_DIR = ROOT / "web"
OUT_DIR = Path(os.environ.get("METEO_OUT_DIR") or WEB_DIR)
OUTPUT_FILE = OUT_DIR / "data" / "forecast.json"
# Exécution de test (sources simulées) : tout ce qui est généré porte une marque refusée par le contrôle de publication.
TEST_RUN = os.environ.get("METEO_TEST") == "1"
HISTORY_DIR = ROOT / "history"  # archive prévision/réalité (branche git « history » dans GitHub Actions)

# Adresse publique du site (pages de référencement, sitemap). À remplacer par le nom de domaine une fois branché :
# variable METEO_SITE_URL dans .github/workflows/update.yml.
SITE_URL = os.environ.get("METEO_SITE_URL", "https://houlalah.fr").rstrip("/")

# Bouées abritées : elles ne représentent que les spots listés (la bouée de Saint-Jean-de-Luz est dans la baie,
# protégée par les digues : sa mesure ne vaut que pour Sainte-Barbe, pas pour les spots ouverts autour).
# Même règle dans l'appli (app/src/data.ts : BUOY_ONLY) et sur le site (web/index.html : BUOY_ONLY).
BUOY_ONLY = {"Saint-Jean-de-Luz": ["Sainte Barbe"]}

# Bouée de référence PAR DÉFAUT des Landes (demande de l'utilisateur) : Cap Ferret pour le nord, jusqu'à 70 km
# (Biscarrosse à Cap de l'Homy), la Gascogne pour les autres. Calculée ici une seule fois (champ « ref » des données de
# l'appli, pages de spots) ; le site (web/index.html : prefRank, LANDES_CF_KM) applique la même règle.
LANDES_CF_KM = 70
CAP_FERRET = (44.6525, -1.4467)   # bouée CANDHIS 03302


def ref_buoy(spot):
    """Identifiant de la bouée de référence par défaut d'un spot (« 03302 » ou « gascogne »), ou None hors des Landes."""
    if spot.get("region") != "Landes":
        return None
    import math
    r = math.pi / 180
    x = (spot["lon"] - CAP_FERRET[1]) * r * math.cos((spot["lat"] + CAP_FERRET[0]) / 2 * r)
    y = (spot["lat"] - CAP_FERRET[0]) * r
    return "03302" if math.hypot(x, y) * 6371 <= LANDES_CF_KM else "gascogne"

TIMEZONE = "Europe/Paris"
FORECAST_DAYS = 7

# Modèles de vagues Open-Meteo : clé interne, libellé, poids dans le mix, noms d'API possibles.
# Le poids de MARC (Ifremer) est ajouté par build.py quand ses données sont disponibles.
WAVE_MODELS = [
    ("mfwam", "Météo-France MFWAM", 0.25, ["meteofrance_wave"]),
    ("ewam", "DWD EWAM 5 km", 0.25, ["ewam", "dwd_ewam"]),
    ("ecmwf", "ECMWF WAM", 0.15, ["ecmwf_wam", "ecmwf_wam025"]),
    ("gfs", "NOAA GFS-Wave", 0.05, ["ncep_gfswave025", "gfs_wave"]),
]
MARC_WEIGHT = 0.30
MARC_LABEL = "Ifremer MARC (côtier)"

WIND_MODELS = [
    ("arome", "Météo-France AROME", "meteofrance_seamless"),
    ("icon", "DWD ICON", "icon_seamless"),
    ("gfs", "NOAA GFS", "gfs_seamless"),
    ("ecmwf", "ECMWF IFS", "ecmwf_ifs025"),
]

# Modèle côtier Ifremer MARC, WAVEWATCH III Golfe de Gascogne, grille 2 minutes (~3,7 km), Licence Ouverte.
# Si l'URL change, la retrouver sur https://marc.ifremer.fr ou le catalogue Sextant.
MARC_OPENDAP_URLS = [
    "https://tds1.ifremer.fr/thredds/dodsC/MARC-WW3_NORGAS_2MIN-FOR_FULL_TIME_SERIE",
    "http://tds1.ifremer.fr/thredds/dodsC/MARC-WW3_NORGAS_2MIN-FOR_FULL_TIME_SERIE",
]

# Bouée Gascogne (Météo-France, WMO 62001), au large à 45,2° N / 5° O.
# Source principale : Copernicus Marine In Situ (IBI, temps réel), accès public sans compte.
# Un fichier NetCDF par jour : {base}/{AAAAMMJJ}/GL_TS_MO_6200001_{AAAAMMJJ}.nc (code Copernicus 6200001).
# Si l'adresse change, parcourir {base} (liste S3) ou le catalogue https://data.marine.copernicus.eu.
# Secours : NOAA NDBC (aucune donnée pour cette bouée en novembre 2026, gardé au cas où le relais reprend).
GASCOGNE = {"id": "62001", "lat": 45.2, "lon": -5.0,
            "copernicus_base": "https://s3.waw3-1.cloudferro.com/mdl-native-03/native/"
                               "INSITU_IBI_PHYBGCWAV_DISCRETE_MYNRT_013_033/"
                               "cmems_obs-ins_ibi_phybgcwav_mynrt_na_irr_202311/latest",
            "copernicus_code": "6200001",
            "url": "https://www.ndbc.noaa.gov/data/realtime2/62001.txt"}
# Correction des modèles à partir de la bouée : fenêtre de comparaison et bornes de sécurité.
BUOY_COMPARE_HOURS = 12
BUOY_RATIO_BOUNDS = (0.75, 1.35)
BUOY_CORRECTION_HOURS = 24  # la correction décroît linéairement jusqu'à 0 sur cette durée, à partir de la mesure
BUOY_MAX_AGE_HOURS = 36     # au-delà, la mesure est trop ancienne : on ne corrige pas les modèles

# Ports de marée : les constantes harmoniques sont calculées par tools/fit_tides.py
# à partir des mesures REFMAR (Shom, Licence Ouverte) déposées dans tides/raw/.
TIDE_PORTS = {
    "socoa": "Socoa (Saint-Jean-de-Luz)",
    "boucau": "Boucau-Bayonne",
    "larochelle": "La Rochelle-Pallice",
    "sables": "Les Sables-d'Olonne",
    "brest": "Brest",
    "roscoff": "Roscoff",
    "porttudy": "Port-Tudy (Groix)",
    "saintnazaire": "Saint-Nazaire",
}

# Limites de l'API gratuite Open-Meteo : on espace les appels.
REQUEST_PAUSE_S = 1.0
