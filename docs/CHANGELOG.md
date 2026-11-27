# Changelog

Évolutions significatives, de la plus récente à la plus ancienne. Le détail technique fin est dans `CLAUDE.md` et l'historique git. Tags `avant-…` = point de retour avant un chantier.

## 27/11/2026

- **Règles communes site / appli, issue #4** (branche `regles-communes`, PR en revue, non publiée ; repère `avant-regles-communes`) :
  - fraîcheur des bouées selon la cadence de chaque station, qualification du vent, secteurs et bouée de référence identiques sur le site, dans l'appli et dans le robot ;
  - mêmes cas de test pour les trois ;
  - âges recalculés et données redemandées au retour dans l'appli ;
  - aucun changement visuel.
  - Voir [regles-communes.md](regles-communes.md).

- **Archive des modèles aux points des bouées, issue #1** (branche `archive-modeles`, PR #20 corrigée après la revue de ChatGPT, non publiée ; repère `avant-archive-modeles`) : modèles un par un, MARC, mélanges brut et corrigé, cycle des modèles, heures avec décalage (`history/buoy_runs/`) ; 5 requêtes groupées au lieu de 25 ; fin des passages archivés deux fois ; anciennes archives intactes. Voir [archive-modeles.md](archive-modeles.md).
- **Heures explicites, issue #2** : **publiée** (PR #17, fusion `68cac65`) après deux revues de ChatGPT. ISO 8601 avec décalage à l'heure du lieu, Portugal à l'heure de Lisbonne, lecture des deux formats (site, appli), correction du décalage unique des séries Open-Meteo. Voir [heures.md](heures.md).
- **Issue #7 publiée** (PR #12).
- **Guides SEO/GEO, issue #13** (branche de test `codex/geo-guides-audit`) — revue scientifique des trois guides et de leurs cinq schémas, corrections du comparateur en eau profonde et vérification de l’aperçu sur ordinateur et mobile. Voir [l’audit](audit-geo-guides-2026-11-27.md).

- **Quotas et cache Open-Meteo, issue #7** (publiée, PR #12) : mesure de chaque requête (dont les 429), cache des prévisions renouvelé à chaque nouveau run des modèles, vent séparé par modèle, mode dégradé signalé. Environ 3,3 fois moins d'appels, bouées inchangées. Voir [quotas-licences.md](quotas-licences.md).
- **Sécurisation de la publication, issue #3** : publiée le 26/11 au soir (PR #11, fusion `56c4c91`).

- **Liens vers les guides, issue #13** (branche `codex/seo-liens-guides`, en revue) — accès au guide depuis les mesures des bouées et le tableau de prévisions des spots.

## 26/11/2026

- **Sécurisation de la publication, issue #3** (publiée le 26/11 au soir, PR #11) : tests isolés hors de `web/`, marques de test, contrôle avant publication (`tools/check_site.py`), génération dans `_site/`, déploiement depuis `main` seulement, `health.json`. Voir [securisation-publication.md](securisation-publication.md).
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
