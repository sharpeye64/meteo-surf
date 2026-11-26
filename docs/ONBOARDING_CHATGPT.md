# Onboarding ChatGPT — Houlalah en 5 minutes

Tu interviens comme **Product Manager, designer UX/UI, conseiller stratégique, analyste SEO et relecteur technique**. Claude Code implémente. Le porteur décide. Lis ensuite [AGENTS.md](../AGENTS.md), [HANDOFF.md](HANDOFF.md) et [DECISIONS.md](DECISIONS.md).

## 1. Ce qu'est Houlalah

- **Le produit** : prévisions surf pour **214 spots, de la Bretagne au Portugal**, sur houlalah.fr, vérifiées par **22 bouées de mesure** (houlographes CANDHIS, Météo-France, Copernicus Marine).
- **Pour qui** : le **surfeur confirmé**, qui veut des données justes pour se faire son idée.
- **Promesse** : « La houle prévue, vérifiée par les bouées ».
- **Différences** : plusieurs modèles comparés, mesure réelle au premier plan, honnêteté sur la fraîcheur, design soigné.
- **Statut** : prototype non commercial, porté par une personne non développeuse.

## 2. Où nous en sommes (fin novembre 2026)

- **En ligne** :
  - accueil cartographique Premium Ocean ;
  - pages de prévisions Premium Ocean ;
  - pages SEO de spots, de bouées et de régions ;
  - premier lot de corrections SEO.
- **Application mobile Expo** : fonctionne en développement, pas encore sur les stores.
- **Search Console** : 204 pages indexées, 66 non indexées, 831 impressions sur 7 jours, **0 clic**, position 31,4. La demande porte surtout sur les **bouées et houlographes**.

## 3. Comment ça marche

- **Un robot Python** (GitHub Actions, environ une fois par heure) récupère les sources et les traite :
  - vagues : MARC, MFWAM, EWAM, ECMWF, GFS, mélangés et corrigés par la bouée Gascogne ;
  - vent : AROME, ICON, GFS, IFS ;
  - les bouées et les marées (calcul harmonique REFMAR).
- **Ce qu'il produit** :
  - `forecast.json` (site) et `data/app/` (application) ;
  - des pages SEO statiques ;
  - une archive prévision / mesure (branche `history`).
- **Le site** : un seul fichier `web/index.html` (MapLibre, Unbounded et Manrope), servi par GitHub Pages. Aucun serveur.
- **L'application** : Expo SDK 58, qui lit les mêmes données allégées.
- **Le détail** : [ARCHITECTURE.md](ARCHITECTURE.md) et [DATA_SOURCES.md](DATA_SOURCES.md).

## 4. Choix tranchés (ne pas reproposer sans élément nouveau)

1. **Pas de note de surf**, pas d'étoiles, pas de « créneau favorable », pas de « va surfer » (D2, D3).
2. **La mesure des bouées est centrale**, en **or**. Elle n'est jamais présentée comme la taille au spot ; sa fraîcheur est honnête (D4, D15).
3. **Période et direction toujours ensemble**, et la période toujours avec la hauteur (D5).
4. **Direction artistique Premium Ocean** retenue. V2, V3 et les directions « Editorial » et « Modern Weather » ont été écartées (D11).
5. **Accueil « la carte d'abord »** :
   - écartés : page marketing, panneau pleine hauteur, grande frise avec lecture automatique (D12) ;
   - sur téléphone : pas de panneau inférieur permanent (D13).
6. **Aucune donnée inventée**, aucune différenciation artificielle des spots qui partagent un même point de prévision (D10).
7. **Webcams** : liens sortants seulement (D8). Le logo fourni par le porteur n'est jamais redessiné (D16).

## 5. Principaux problèmes

- **SEO** : 66 pages non indexées. On attend l'export Search Console. Il y a aussi 21 groupes de spots à prévision identique.
- **Licence Open-Meteo** : usage non commercial uniquement, ce qui bloque toute monétisation en l'état.
- **Poids** : `forecast.json` fait 6,5 Mo.
- **Code** : `index.html` est monolithique, avec du code mort.
- **Application** : règle de fraîcheur pas encore alignée sur le site, pas de design Premium Ocean, pas d'alertes ni de widgets, pas de compte Apple.
- **Sources** : certaines bouées sont muettes (Anglet, Cabo Silleiro). Il n'y a pas de marées pour l'Espagne et le Portugal.

## 6. Prochaines opportunités

- **Fiabilité chiffrée par bouée** (écart prévu / mesuré par échéance et par modèle), à partir de l'archive. C'est la promesse rendue visible.
- **Historique et records** des bouées (en réponse aux requêtes « bouée / houlographe [lieu] »).
- **Application** : vraie version installée, **alertes de houle** et **widgets**, puis les stores.
- **SEO international** : espagnol, portugais, anglais (sous-dossiers, `hreflang`, traductions faites par une personne).
- **« Taille au bord »**, apprise sur l'archive côtière après validation.
- **Offre Pro** : seulement après avoir réglé la licence des prévisions.

## 7. Comment proposer

Ouvre une **issue GitHub** avec le modèle de [COLLABORATION.md](COLLABORATION.md) : constat, proposition, pourquoi, vérification dans DECISIONS.md, hors périmètre et mesure de succès. Le porteur valide, puis Claude Code implémente sur une branche de test. Écris au porteur **en français, simplement**.
