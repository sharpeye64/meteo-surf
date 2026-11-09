# Contexte pour Claude Code — le site s’appelle Houlalah (nom de domaine disponible avec le h final) (wordmark minuscule « houlalah » + trait de vague)

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

- Bandeau « L'équipement idéal » : on annonce seulement un TYPE de planche (Mid-length, Groveler, Shortboard, Step-up, Gun),
  avec une fourchette de longueur et de volume (table `GEAR` dans `web/index.html`), choisi d'après la puissance de la houle
  (taille × période × exposition) puis ajusté au poids (liste déroulante, mémorisée). Pas de marque ni de modèle : l'utilisateur
  ne veut pas de précision excessive. Les coefficients litres/kg sont des repères, pas une norme.
- Le trait doré « créneau favorable » de la frise horaire est désactivé (`winA=99,winB=-1`) : on y réfléchira plus tard.
  Le score interne (`h.score`) existe encore mais ne s'affiche plus.
- Bas de page : « Marées de la semaine » (horaires, coefficient, lever/coucher du soleil sur 7 jours) a remplacé « Le spot »,
  qui répétait le haut de page. « Fiabilité des données » est le dernier bandeau (2 cartes courtes, pas de « sources »).
- Bandeaux Vagues / Vent / Marée du haut de page : icône fine + valeur + pastilles ; la marée a sa courbe du jour en fond de
  carte avec un point à l'heure choisie (hauteur interpolée). Pas de ligne « jour · heure · soleil » ni de bouton webcam texte :
  la webcam est une icône à côté de l'étoile.

## Logo
- Le logo est celui FOURNI par l'utilisateur (`brand/logo-source.webp` : un « h » dont l'arche devient une houle, avec le mot
  « houlalah » en dessous). Il ne faut PAS le redessiner : `tools/trace_logo.py` le vectorise fidèlement (calque de contour,
  sans retouche) vers `web/brand/` (`symbol.svg`, `wordmark.svg`, `lockup.svg`, `lockup.png`), puis `tools/brand_assets.py`
  produit `favicon.svg`, `apple-touch-icon.png` et `icon-512.png`. `tools/make_og.py` colle `lockup.png` dans `web/og.png`.
  En-tête et pages de spots utilisent `brand/symbol.svg` + `brand/wordmark.svg`. Couleur d'origine : sable #E9C694.
  Pour changer de logo : remplacer `brand/logo-source.webp`, relancer `python -m tools.trace_logo`, `tools.brand_assets`, `tools.make_og`.
- Anciennes pistes (redessinées par Claude : rond et houles, boussole, aileron, h en trait) abandonnées.
- À faire côté juridique : recherche d'antériorité « Houlalah » sur la base de marques de l'INPI avant de s'y installer ; un
  logo généré par IA est difficile à protéger.
- Direction artistique : pistes présentées (Profondeur sombre, Papier de mer clair, Signal technique, thème à deux faces) ; à
  confirmer avec l'utilisateur. Il a demandé d'abandonner les maquettes : ne rien appliquer sans demande.

## SEO
- `pipeline/seo.py` (appelé par `build.py`, jamais bloquant) écrit `web/spots/<slug>/index.html` (une page par spot avec vrai
  texte, tableau des 7 jours, JSON-LD, balises canonical/Open Graph, spots voisins), `web/spots/index.html` (index par région),
  `web/sitemap.xml`, `web/robots.txt`. Ces fichiers sont générés (ignorés par git) et publiés avec le site.
- L'adresse publique est https://houlalah.fr (`config.SITE_URL`, variable `METEO_SITE_URL` dans `.github/workflows/update.yml`, fichier
  `web/CNAME`). Le DNS et le domaine personnalisé dans Settings > Pages sont réglés à la main par l'utilisateur. Les pages de spots mènent à `./?spot=<slug>` (le site lit ce
  paramètre, met à jour le titre de l'onglet et l'adresse selon le spot).
- `pipeline/pages.py` génère 3 pages de contenu (`/comment-ca-marche/`, `/mentions-legales/`, `/confidentialite/`), listées dans le
  sitemap et liées dans le pied de page avec les 58 pages de spots (liens classiques, que Google peut suivre). Les mentions légales
  gardent l'éditeur anonyme (LCEN art. 6 III 2) et citent l'hébergeur GitHub ; le contact est contact@houlalah.fr, ADRESSE À CRÉER
  (redirection e-mail chez le registrar). À relire si on ajoute un outil de mesure d'audience, une pub ou un compte utilisateur.
- À faire quand le domaine est branché : déclarer le sitemap dans Google Search Console / Bing Webmaster, image de partage
  (og:image), vérifier les Core Web Vitals (l'océan WebGL est lourd sur mobile).

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

- Encadré « La bouée » (ex-radar) : bascule entre la bouée Gascogne (62001, au large, Copernicus, retard de plusieurs heures) et la
  bouée CANDHIS la plus proche du spot (Cap Ferret 03302, Anglet 06402, Saint-Jean-de-Luz 06403 ; mesures toutes les 30 min),
  nommées par leur NOM (pas « large / côte »). Carte de gauche : hauteur en grand, période, direction (flèche), eau, fraîcheur,
  barres « mesuré / prévu ». Carte de droite : courbe des 48 h, mesure contre prévision. `pipeline/candhis.py` lit les pages
  publiques (1 requête par bouée, relancée une fois, heures TU converties en heure de Paris). Licence Ouverte Etalab 2.0, mesures
  temps réel non validées (dit dans l'info-bulle et le pied de page). Allosurf et sites similaires : ne pas utiliser.
- Fraîcheur de la bouée Gascogne (CORRIGÉ le 09/11/2026 après lecture de `index_latest.txt` de Copernicus) : Météo-France ne livre qu'UNE
  fois par jour, vers 21 h 50 UTC (≈ 23 h en France), avec des données jusqu'à ~20 h UTC du jour même. La dernière mesure a donc entre 2 et
  26 h (14 h en moyenne). Pas de fichier intra-journalier, pas d'API ouverte Météo-France pour la 62001 ; sites tiers (Allosurf,
  surf-report, Meteociel, Surf-Forecast) non utilisables. Variables : VGHS (Hs), VEMH, VGTA, VTPK et VDIR (douteux) : période du modèle.
- BOUÉES FRAÎCHES DANS LE MÊME PRODUIT COPERNICUS (vérifié le 09/11/2026, retard ≈ 30 à 45 min, fichiers horaires `IR_TS_MO_<nom>_AAAAMMJJ.nc`
  dans le même dossier `latest/AAAAMMJJ/`) : Puertos del Estado « 6200024 » = bouée du large Bilbao-Vizcaya (43,65 N, 3,04 O ; VHM0, VTPK, VMDR,
  VPED), Euskalmet « Donostia-buoy » (43,57 N, 2,01 O), Puertos del Estado « Bilbao-coast-buoy » et « PasaiaII-coast-buoy ». Mesures
  cohérentes avec nos bouées côtières (≈ 0,8 m, 4 s, secteur S-SE le 09/11). Licence : données Copernicus Marine, mention « Puertos del Estado,
  Euskalmet, via Copernicus Marine ». FAIT le 09/11/2026 : `pipeline/ibi_buoys.py` les récupère (+ prévision des modèles au point, archive côtière) ; « La bouée » propose Gascogne, Bilbao-Vizcaya, Donostia (si < 80 km du spot) et la bouée CANDHIS la plus proche ; par défaut, la plus proche dont la mesure a moins de 6 h, sinon la plus fraîche (`pickBuoy`). Les bouées CANDHIS sont
  aussi dans ce produit (6200064 Cap Ferret, 6200066 Anglet, 6200079 Saint-Jean-de-Luz) avec le même retard court.
- Mesure réelle affichée à côté de la prévision (demande de l'utilisateur, 09/11/2026) : une pastille `meterHtml()` juste sous le grand chiffre du
  haut de page (« MESURE RÉELLE AU BORD · 0,6 m · 4 s · SSE · Bouée Cap Ferret · à l'instant », lien vers « La bouée »), sur ordinateur et
  mobile, avec la bouée choisie par `pickBuoy` (la plus proche dont la mesure a moins de 6 h). L'utilisateur NE veut PAS la mesure sur la frise
  horaire (essayé puis retiré). Priorité géographique : côte atlantique française (là où sont la majorité des surfeurs et des spots) ; pas
  d'heure d'arrivée de la houle ; le but est que la donnée mesurée soit claire et fiable, à côté des prévisions.
- ATTENTION (retour de l'utilisateur) : la hauteur affichée (modèles près du spot ou bouée au large) n'est PAS la taille des vagues
  au bord. À hauteur égale, une houle longue (14 s) arrive bien plus grosse et plus puissante sur la côte qu'une houle courte (7 s).
  Toujours montrer la période avec la hauteur, dire « au large » / « à la bouée », et ne jamais présenter la hauteur de la bouée comme
  la taille au spot. Les info-bulles « taille » et « période » et la phrase sous la bouée (`whyText`) le disent. `h.Heff` (hauteur ×
  exposition × facteur de période) ne sert qu'au choix de la planche et n'est pas affiché. Piste : apprendre, avec l'archive des
  bouées côtières CANDHIS, une vraie relation hauteur/période → taille au bord par spot, avant d'afficher une « taille au bord ».
- Archive côtière (démarrée le 09/11/2026) : à chaque passage, `history.record_coast` garde les mesures horaires des 3 bouées CANDHIS
  (hauteur, Hmax, période, direction, eau : `history/coast_obs/`) et la prévision au même point (hauteur, période, direction sur 96 h :
  `history/coast_runs/`). Bilan : `python -m tools.coast_report history/`. Objectif : après ≥ 30 jours, apprendre par bouée la relation
  prévu (hauteur, période) → mesuré près du bord, puis seulement afficher une « taille au bord ». Ne rien afficher avant validation.
- Haut de page : une seule pastille de fiabilité en mots simples (« Prévision fiable / assez fiable / incertaine », info-bulle), plus
  de « Accord des modèles », de « 4 modèles de houle… », de « Fiabilité mesurée… » ni de bouton « Lancer la journée ».

- Mobile : pas d'accord des modèles, pas de pastille bouée dans le haut, pas de boutons « Comparer / Lancer la journée » ;
  la légende sous la frise horaire est supprimée partout (seul l'avertissement sur le vent AROME/ICON reste). Le choix du poids est
  supprimé : la planche n'affiche plus de volume (il dépend du poids). Idée à reprendre : version « Light » et version « Pro »
  (comparaison des modèles, volume selon le poids, lecture de la journée) pour ceux qui veulent aller plus loin.

- 09/11/2026 : bandeau « L'équipement idéal » (planche et combinaison) RETIRÉ à la demande de l'utilisateur (inutile) ; pastille « Prévision
  fiable / assez fiable / incertaine » du haut de page RETIRÉE ; le nom du spot est grand (Unbounded, clamp 24-40 px), la taille des vagues plus
  petite (clamp 30-50 px). Code de la planche (`GEAR`, `gearBoardHtml`) et `trustHtml` encore présent mais plus affiché.

- 09/11/2026 : API Météo-France « Données d'observation » v2 VÉRIFIÉE avec la clé de l'utilisateur (en-tête `apikey`, base
  `https://public-api.meteofrance.fr/public/DPObs/v2`, paramètre `format=json` obligatoire). `/liste-bouees` = 24 h d'historique horaire de TOUTES
  les bouées ; `/bouees` = dernière mesure de toutes (les filtres `id_bouee` et `date` sont ignorés). Gascogne : `geo_id_wmo` « 6200001 » ; champs
  `haut_vag` (m), `per_moy_vag` (s, période MOYENNE, pas la période pic), `dir_vag` (°), `tmer` (K), `validity_time` (UTC), mesure ≈ 1 h de retard.
  `pipeline/meteofrance.py` + `buoy.load()` : Météo-France prioritaire, complété par Copernicus pour l'historique ; sans clé, retour à Copernicus.
  La clé = secret GitHub `METEOFRANCE_APIKEY` (jamais dans le dépôt). La période affichée reste celle du modèle (`period_used`).

## Pistes suivantes
- (FAIT, voir plus haut) Gascogne plus fraîche : l'app La Bouée affiche une mesure vieille de 1 h 10 « via Météo-France ». Piste : API officielle Météo-France « Données
  d'observation », endpoints `/liste-bouees` et `/bouees` (mesures horaires à H + 10 min, id à 7 chiffres, compte gratuit sur
  portail-api.meteofrance.fr, jeton OAuth2). Non testable sans clé : `tools/meteofrance_probe.py` (à lancer par l'utilisateur) imprime la structure
  des réponses ; ensuite écrire `pipeline/meteofrance.py`, avec la clé dans un secret GitHub (`METEOFRANCE_TOKEN`), jamais dans le dépôt.
- API CANDHIS officielle : jeton sur demande à candhis@cerema.fr (base https://candhis.cerema.fr/API/v1/, guide PDF `04_Candhis_API_v1_Utilisateur`).
- Archive côtière en cours (voir plus haut) : à exploiter avec `tools/coast_report.py` après ≥ 30 jours, pour une vraie « taille au bord ».
- Clé d'API CANDHIS officielle (demande par mail à l'équipe Candhis) pour remplacer la lecture des pages publiques.
- Coefficient de marée, calibration `tide_offset_min` par spot, réglages de spots validés sur le terrain.
- Statistiques publiques de fiabilité (écart prévision / bouée).

- 09/11/2026 : HAUT DE PAGE « STYLE LISTE » publié (tag `avant-design-c` = ancienne version, pour revenir en arrière : `git checkout avant-design-c -- web/index.html`). Structure : nom du spot, grand chiffre + mini-boussole en anneau
  (`compassMini`, houle = point blanc, vent = point creux turquoise, période au centre), carte de la bouée en sable plein (`meterHtml`, « EN DIRECT » si mesure < 2 h),
  liste Vent / Marée (courbe intégrée, le point passe au centre de la courbe : la marge de `.tideline` est remise à 0), semaine en barres horizontales (`weekRow`). Plus de cartes
  Vagues, plus de ligne « Journée », « Mer du vent », « Houle secondaire ». IMPORTANT : la hauteur du haut de page doit rester CONSTANTE (lignes à hauteur fixe, textes sur une
  ligne) : l'océan WebGL est redimensionné à chaque changement de hauteur, ce qui fait saccader l'animation. Pied de page : liste des 58 spots dans un `<details>` (liens toujours dans le HTML).
