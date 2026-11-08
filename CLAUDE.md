# Contexte pour Claude Code — le site s’appelle Houlala (wordmark minuscule + trait de vague)

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

- Haut de page = OCÉAN ANIMÉ (WebGL, shader dans `oceanBuild()`), voulu par l'utilisateur : ciel et mer qui bougent, soleil sur un
  arc symbolique de gauche à droite (`sunVec`, jamais hors cadre) qui glisse du lever vers l'heure actuelle au chargement,
  rayons, reflet, lune et étoiles la nuit, arc pointillé (`drawArc`). Sans arbres ni montagnes : l'utilisateur a trouvé les
  décors dessinés « cheap » (ils ont été retirés).
- Bouée de mesure de la houle posée sur l'eau, dessinée DANS le shader (`buoy()` : coque jaune en dôme, bande noire, panneau
  solaire, mât, lanterne qui éclate toutes les 5 s, reflet dans l'eau déformée, écume autour de la coque). Elle monte, descend
  et s'incline avec la houle : `swellAt()` (JavaScript) recalcule les 3 trains de houle de `waves()` (GLSL) pour donner sa
  hauteur et sa pente. Si on change les constantes des vagues dans le shader, les changer AUSSI dans `swellAt()`, sinon la
  bouée flotte à côté de l'eau. Position : 46 m devant, à 72 % de la largeur (entre le texte et la boussole).
  Une étiquette (`buoyLabelHtml`) affiche sa VRAIE dernière mesure (bouée Gascogne via Copernicus : hauteur, direction, âge) ;
  la taille de la bouée et son mouvement, eux, ne dépendent pas de la mesure. Les données Copernicus ont souvent 12 à 30 h
  de retard : l'étiquette passe en gris au-delà de 6 h. Flottante à côté de la bouée sur ordinateur, dans le flux sur mobile.
- RÈGLES ANTI-BLOCAGE (l'ancienne version bloquait la page après quelques clics ; ne jamais les enfreindre) :
  1. UN SEUL canvas, `#ocean`, hors de `#app`, créé une fois par `oceanInit()` ; `render()` ne le recrée jamais.
  2. Une seule boucle `oceanLoop` : 30 images/s max, en pause si la page est cachée ou hors écran.
  3. Qualité adaptative : si la moyenne dépasse 52 ms par image, la résolution baisse par paliers, puis l'eau se fige.
  4. Pas de `backdrop-filter` sur les éléments du haut de page (reflouter chaque image coûte très cher).
  5. Le fond de page (`html`) doit porter le dégradé et `body` rester transparent : sinon le fond du `body` se peint
     par-dessus le canvas (z-index négatif) et l'océan disparaît.
  Test à refaire après toute modif du fond : 60 `render()` d'affilée => toujours 1 canvas, même contexte WebGL.
- Webcams : liens externes seulement (`CAMS` dans index.html), jamais d'intégration ni de rediffusion (conditions d'utilisation
  des tiers). Sources : pages Surf-Forecast par spot, Quiksilver pour Saint-Jean-de-Luz et Hendaye ; pour les autres spots,
  « webcam la plus proche » à moins de 15 km. Tourisme Landes (officiel) bloque les vérifications automatiques : non utilisé.
  Les caméras sont gérées par des tiers et peuvent être hors ligne : le dire.

- Radar : bascule « Large » (bouée Gascogne 62001, Copernicus, retard 12-30 h, calcul d'arrivée de la houle) / « Côte »
  (bouée CANDHIS la plus proche du spot : Cap Ferret 03302, Anglet 06402, Saint-Jean-de-Luz 06403 ; mesures toutes les 30 min,
  fraîches ; comparée à notre prévision du spot). `pipeline/candhis.py` lit les pages publiques (1 requête par bouée et par passage,
  heures TU converties en heure de Paris ; positions des bouées approximatives, servent seulement à choisir la plus proche).
  Licence Ouverte Etalab 2.0, mesures temps réel non validées : le dire. Allosurf et sites similaires : pas d'API ni de conditions
  de réutilisation, ne pas les utiliser.

## Pistes suivantes
- Archiver aussi les mesures CANDHIS (fiabilité près de la côte) : aujourd'hui seule la bouée Gascogne alimente `history/`.
- Clé d'API CANDHIS officielle (demande par mail à l'équipe Candhis) pour remplacer la lecture des pages publiques.
- Coefficient de marée, calibration `tide_offset_min` par spot, réglages de spots validés sur le terrain.
- Statistiques publiques de fiabilité (écart prévision / bouée).
