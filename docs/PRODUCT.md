# Produit : fonctionnalités, règles métier, expérience

Les raisons des choix sont dans [DECISIONS.md](DECISIONS.md), et le style visuel dans [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).

## Principes

1. **Données d'abord, sans avis.** On montre la houle (hauteur **et** période **et** direction), le vent, son orientation par rapport au spot, la marée, l'accord des modèles et la mesure des bouées. Le surfeur conclut lui-même.
2. **L'essentiel en trois secondes, le reste à la demande.** Le haut de page donne houle, vent et bouée ; le tableau horaire suit ; le détail de la houle, les modèles, les 7 jours et la comparaison s'ouvrent à la demande.
3. **Honnêteté sur la donnée** :
   - la hauteur au large n'est pas la taille au bord ;
   - une mesure ancienne est dite ancienne ;
   - une source en panne est signalée ;
   - les marées sont indicatives.
4. **La carte d'abord** sur l'accueil : explorer la côte, pas lire une page commerciale.

## Accueil (`/`)

- **Carte plein écran** de toute la côte, de la Bretagne au Portugal (MapLibre, fond sable et mer). À l'arrivée, on voit tous les spots.
- **Marqueurs de spots** : valeur de la donnée choisie, avec son unité et l'échelle de couleurs du tableau des prévisions. Les spots proches se regroupent selon le zoom ; le groupe garde la valeur la plus haute.
- **Bouées** : toujours visibles, en bleu nuit et or. Halo doré et pastille verte animée seulement si la mesure est « en direct ». Une bouée qui tombe sur un spot passe en petite pastille dessous.
- **Grand écran** :
  - **panneau flottant compact** : titre, recherche, zones (Tous, France, Espagne, Portugal), « Mes spots » replié, 3 bouées puis la liste complète à la demande, et des liens vers les spots, les bouées et les régions ;
  - **en haut à droite** : Houle / Période / Vent, le bouton des bouées et une légende en paliers ;
  - **en bas** : le sélecteur de jour et d'heure.
- **Téléphone** : carte plein écran, recherche flottante en haut, zones FR / ES / PT, et un socle en bas (donnée affichée, bouées, puis ‹ jour · heure ›). Les fiches (spot, bouées, favoris, donnée, menu) s'ouvrent à la demande ; il n'y a pas de panneau permanent.
- **Fiche d'un spot** : son nom remplace l'accroche dans l'en-tête. Elle montre la houle et le vent prévus à l'heure choisie, l'orientation du vent, la bouée de référence (mesure réelle, âge, distance) et « Voir la prévision ».
- **Caméra** :
  - spot : ses voisins à moins de 25 km restent visibles ;
  - bouée côtière : zoom modéré ;
  - bouée du large : un cadrage qui garde la côte ;
  - à la fermeture d'une fiche, retour au cadrage précédent.
- **Sélecteur de temps** : les vraies prévisions déjà chargées, sans appel en plus. Les bouées restent la **mesure actuelle**, signalée comme telle quand on regarde le futur. **Pas de lecture automatique.**

## Page de prévisions d'un spot (`/?spot=<slug>`)

- **En-tête bleu nuit** : nom du spot, région, type de vague, eau, lever et coucher du soleil ; calendrier de 7 jours avec la houle du jour.
- **Résumé** en trois colonnes :
  - houle : hauteur, période, direction, « moyenne de N modèles » ;
  - vent : force, direction, rafales, orientation (Offshore, Side-shore…) ;
  - bouée en doré : mesure, période, direction, eau, âge.
- **Tableau horaire** de 6 h à 21 h : vagues, période et direction (toujours ensemble), accord des modèles en trois points, vent avec sa flèche, courbe de marée avec pleines et basses mers.
  - colonne choisie avec un cadre qui glisse ;
  - info-bulle au survol ;
  - sur téléphone, frise bord à bord avec des pictogrammes à gauche, centrée sur l'heure actuelle.
- **À la demande** : « 7 jours » (graphique), « Détail de la houle » (trains de houle et rose des directions), « Modèles » (une ligne par modèle).
- **Mesure en mer** : la bouée choisie (bascule entre les bouées proches), la courbe des 48 h mesurée contre la prévision, et la page de la bouée.
- **Spots à proximité** : carte et liste, tri, comparaison.
- **Fiabilité** : écart moyen entre la prévision à 1 jour et la bouée Gascogne.
- **Le reste** : favoris (étoile, gardés sur l'appareil) et mode sombre en option (bouton lune).

## Pages SEO (statiques, générées par le robot)

| Page | Contenu |
|---|---|
| `/spots/<slug>/` | Résumé du jour ; tableau 7 jours ; « Heure par heure » toutes les 3 h (avec « Pour ce spot ») ; marées de la semaine ; fiche du spot ; bouée de référence ; 6 voisins ; région |
| `/bouees/<slug>/` | Dernière mesure, identifiant officiel et source ; encadré si la station ne publie plus ; carte ; historique 48 h ; tableau des mesures ; records et moyennes ; 8 spots autour ; bouées voisines ; données structurées Dataset |
| `/meteo-surf-<zone>/` | 12 régions : spots, bouées de la zone, autres zones |
| `/spots/`, `/bouees/` | Index |
| Pages de texte | Comment ça marche, À propos, Mentions légales, Confidentialité |

## Règles métier clés

- **Fraîcheur des bouées** : selon la cadence de chaque station (règle dans [DATA_SOURCES.md](DATA_SOURCES.md)).
- **Bouée de référence d'un spot** : règle commune au site, à l'application et au robot ([DATA_SOURCES.md](DATA_SOURCES.md)).
- **Orientation du vent** : par rapport à l'orientation propre du spot, même règle partout.
- **Couleurs** : bleu nuit = prévision, **or = mesure réelle**. Aucune couleur de qualité (bon ou mauvais) nulle part.
- **Spots partageant un même point de prévision** : 21 groupes, 53 spots. Ils ont des valeurs identiques : on ne les différencie **jamais** artificiellement.
- **Webcams** : liens sortants vers la caméra du spot ou la plus proche (à moins de 15 km), en signalant qu'elle est gérée par un tiers.

## Fonctionnalités retirées (ne pas réintroduire sans décision)

- **Équipement idéal** (type de planche, volume selon le poids).
- **Pastille « Prévision fiable / assez fiable / incertaine »** dans le haut de page.
- **Créneau favorable** (trait doré dans la frise) : désactivé (`winA=99`).
- **Mesure de la bouée sur la frise horaire** : essayée, puis retirée.
- **Lecture automatique de la frise** de l'accueil.
- **Panneau inférieur permanent** sur téléphone (en trois crans).
- **Section « La semaine »** en bas de page (doublon).
