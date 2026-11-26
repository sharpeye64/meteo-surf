# Changelog

Évolutions significatives, de la plus récente à la plus ancienne. Le détail technique fin est dans `CLAUDE.md` et l'historique git. Tags `avant-…` = point de retour avant un chantier.

## 26/11/2026

- **Sécurisation de la publication, issue #3** (branche `securiser-publication`, PR en revue, non publié) : tests isolés hors de `web/`, marques de test, contrôle avant publication (`tools/check_site.py`), génération dans `_site/`, déploiement depuis `main` seulement, `health.json`. Voir [securisation-publication.md](securisation-publication.md).
- **SEO, premier lot** (publié, commit `afb3185` ; tag `avant-seo-corrections`) :
  - accueil sans la page d'un spot derrière la carte ;
  - fraîcheur des bouées selon la cadence de chaque station ;
  - pages de bouées : « houlographe », numéros CANDHIS, sources, Dataset, encadré « pas de mesure depuis », liens vers les pages de spots ;
  - pages de spots : heure par heure avec « Pour ce spot », marées de la semaine ;
  - canonique de `/?spot=x` vers `/spots/x/` ;
  - génération en heure de Paris (le robot tourne en UTC) ;
  - page de bouée qui se corrige seule si le robot s'arrête.
- **Accueil Premium Ocean** (publié ; tags `avant-accueil-ocean`, `accueil-ocean-v1` à `v4`) :
  - carte sable et mer, panneau compact, Houle / Période / Vent, sélecteur jour et heure ;
  - bouées vivantes, regroupement des spots, en-tête qui change avec la sélection, caméra avec contexte ;
  - téléphone : la carte d'abord, socle en bas, fiches à la demande ;
  - ancien style de l'accueil supprimé.
- **Pages de prévisions Premium Ocean** (publié ; tags `avant-v2-previsions` à `avant-finition-mobile`) :
  - le chemin : V2, V3, trois directions artistiques, choix de Premium Ocean ;
  - les finitions : résumé en colonnes, calendrier vertical, frise horaire pleine largeur sur téléphone, courbe de marée, sélection qui glisse, info-bulles, pages générées alignées.
- **Présentation mobile de l'accueil** publiée (commit `5944446`).

## 18–25/11/2026

- **214 spots et 22 bouées** (Espagne, Portugal, Bretagne) ; bouées muettes reprises depuis l'archive (`keep_silent`) ; bouée de référence par défaut dans les Landes ; Sainte-Barbe.
- **Application mobile Expo** publiée sur `main` (onglets, carte, bouées, favoris, mode sombre, icône « A · Nuit »).
- **Points des spots ramenés sur le trait de côte** (`mlat`, `mlon`) ; pages de bouées ; accueil « carte de la côte ».

## 9–17/11/2026

- **Bouées** : API Météo-France (Gascogne, environ 1 h de retard), bouées CANDHIS, bouées Copernicus (Bilbao-Vizcaya, Donostia…), archive côtière.
- **Mesure réelle** affichée à côté de la prévision ; haut de page « style liste » ; retrait de l'équipement conseillé et de la pastille de fiabilité.
- **Pages SEO** (spots, régions, pages de texte), sitemap, domaine houlalah.fr.

## 6–8/11/2026

- **Prototype** : robot Python (Open-Meteo, MARC, bouée Gascogne), page statique avec océan animé en WebGL, marées harmoniques REFMAR, archive prévision / mesure, nom et logo Houlalah.
