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
4. Marées : constantes Socoa (station REFMAR 95) et Boucau (94) ajustées sur 1 an de mesures validées 10 min
   (`tools/get_refmar.py` puis `tools/fit_tides.py`, API publique services.data.shom.fr, sans compte). Validées contre
   des mesures hors échantillon : écart d'heure moyen 5 min. `tide_offset_min` par spot reste à calibrer sur le terrain.
5. Volume d'appels Open-Meteo : environ 30 points × (1 + 4 modèles) + vent toutes les 3 h. Rester sous les limites gratuites.

## Choix de produit (décidés avec l'utilisateur)
- Public visé : surfeur confirmé du Sud-Ouest. Il se fait sa propre idée : ne pas mettre en avant d'avis sur les conditions
  (pas de « Petit/Bon » dans le haut de page ni dans la frise horaire). Insister sur la fiabilité des données :
  accord des modèles, écart mesuré avec la bouée (`pipeline/history.py`, branche git `history`), âge des mesures.
- Le « créneau favorable » (réglages des spots, jamais validés sur le terrain) reste discret : trait doré dans la frise.
- Plus aucun mot de qualité ni couleur de qualité nulle part (liste des spots, carte, spots proches : taille et accord des
  modèles seulement). La section « La semaine » du bas a été retirée (doublon du bandeau du haut). Le tri du sélecteur de
  spot se fait par taille. Le score interne (`h.score`, `day.sc`) existe encore pour le trait doré, mais ne s'affiche plus.

- Bandeau « L'équipement idéal » : exemple de planche réelle (table `GEAR` dans `web/index.html`) choisi d'après la puissance
  de la houle (taille × période × exposition), puis ajusté au poids (liste déroulante, mémorisée). Dimensions et volumes
  relevés en novembre 2026 sur les fiches Pyzel et sur des revendeurs concordants ; les revendeurs divergent selon l'année
  et la construction, donc toujours indiquer « à vérifier chez le shaper ». Ajouter une famille ou un modèle = ajouter une
  entrée à `GEAR` avec uniquement des dimensions vérifiées. Les coefficients litres/kg sont des repères, pas une norme.

## Pistes suivantes
- Bouée CANDHIS d'Anglet (Licence Ouverte) en « vérité terrain » près de la côte, avec comparaison H1/3 et TH1/3.
- Coefficient de marée, calibration `tide_offset_min` par spot, réglages de spots validés sur le terrain.
- Statistiques publiques de fiabilité (écart prévision / bouée).
