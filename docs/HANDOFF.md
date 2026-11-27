# HANDOFF — état du projet (à garder court)

_Dernière mise à jour : 27/11/2026 pour l'issue #1 (archive des modèles), par Claude Code._

## Point SEO/GEO

- **Issue #13, PR #16** — trois guides en ligne depuis le 27/11. Les quatre URL, leurs canoniques et leur présence dans le sitemap ont été vérifiées.
- **Lot suivant** — liens contextuels en revue sur la branche `codex/seo-liens-guides`. Voir [GEO.md](GEO.md).

## En production (houlalah.fr)

- **Accueil cartographique Premium Ocean v2** : panneau compact, choix houle / période / vent, sélecteur de jour et d'heure, bouées dorées, approche « la carte d'abord » sur téléphone.
- **Pages de prévisions Premium Ocean** (`/?spot=…`), avec une frise horaire pleine largeur sur téléphone.
- **Premier lot SEO** (commit `afb3185`, publié le 26/11 au soir) :
  - « Bouée houlographe » et numéros CANDHIS ;
  - fraîcheur des bouées selon la cadence de chaque station ;
  - pages de spots avec l'heure par heure et les marées ;
  - canonique de `/?spot=x` vers `/spots/x/` ;
  - génération en heure de Paris.
- **Vérifié en ligne** : le titre « Bouée houlographe Anglet : dernières mesures » et les marées sur `/spots/lacanau/`.

## En cours

- **Issue #1, branche `archive-modeles`** (PR en revue, **non publiée**, repère `avant-archive-modeles`) : archive v2 aux points des 22 bouées (`history/buoy_runs/`) avec les modèles un par un, MARC, mélanges brut et corrigé, provenance et cycle des modèles, heures avec décalage. 5 requêtes groupées au lieu de 25, fin des doublons (≈ 40 % des passages archivés deux fois avant). Anciennes archives intactes, prévision publiée identique. [archive-modeles.md](archive-modeles.md).
- **Issue #2 publiée** (PR #17, fusion `68cac65`) ; production vérifiée : contrat v2, Portugal à l'heure de Lisbonne, aucune heure sans décalage. Reste : l'appli sur un vrai téléphone (Expo Go). [heures.md](heures.md).
- **Issue #7 publiée** (PR #12, fusion `d0cd73d`) ; premier passage de production vérifié : cache, compteurs, cohérence des séries.
- **Issue #13, PR #15** — trois guides et cinq schémas relus, comparateur corrigé sur `codex/geo-guides-audit`. Aperçu HTML autonome vérifié dans Chromium. Voir [l’audit des guides](audit-geo-guides-2026-11-27.md). Validation éditoriale avant toute mise en ligne.

- **Déjà publiés** : #3 sécurisation de la publication (PR #11, avec la documentation commune de `docs-onboarding`), #7 quotas et cache (PR #12, [quotas-licences.md](quotas-licences.md) : **4 refus 429** vus sur un passage à cache vide), #2 heures (PR #17).
- **Ordre retenu ensuite (non commencé)** : #4, #6, #8 → #5, #9 après 30 jours de collecte de l'archive v2 (fin décembre 2026 au plus tôt) → #10 après les licences.
- **Amélioration mineure à traiter à part** : le marqueur « maint. » de la frise du site arrondit encore à l'heure la plus proche (« maint. » sur 16 h à 15 h 45). Détail dans [heures.md](heures.md), section « Après la publication ».

## Problèmes ouverts

1. **Pages non indexées** : 66 dans Search Console. Il faut l'**export** des URL concernées pour traiter les 21 groupes de spots à prévision identique (`docs/seo-corrections-2026-11-26.md`, section 5).
2. **Application mobile** : ses seuils de fraîcheur des bouées ne suivent pas encore la règle « selon la cadence » du site.
3. **Poids** : `forecast.json` (6,5 Mo) est trop lourd pour l'accueil.
4. **Code mort dans `web/index.html`** : fonctions `*_v1`, directions artistiques B et C, ancien océan WebGL.
5. **Bouées muettes** : Anglet depuis le 18/11, Cabo Silleiro depuis le 21/11. C'est côté source, pas un bug du robot.
6. **Marées absentes** pour les 75 spots d'Espagne et du Portugal.
7. **Open-Meteo** : usage non commercial uniquement. C'est un frein à toute monétisation.

## Prochaines étapes proposées (à valider par le porteur)

- **Documentation** : la pousser sur GitHub pour que ChatGPT y accède, avec l'accord du porteur.
- **Search Console** : suivre l'effet du lot SEO (`docs/seo-suivi-search-console.md`) et récupérer l'export des pages non indexées.
- **Archive** : fiabilité par bouée à partir de l'archive (`docs/archives-bouees-potentiel.md`).
- **Application** : compte Apple développeur, puis une vraie version sur iPhone, puis les stores.

## Remettre les vraies données

Depuis ce lot, les tests n'écrivent plus dans `web/`. Pour avoir les vraies données en local (aperçu) :

```
curl -s -o web/data/forecast.json https://houlalah.fr/data/forecast.json
python -c "import json; from pipeline import appdata, seo; p=json.load(open('web/data/forecast.json',encoding='utf-8')); appdata.generate(json.load(open('pipeline/spots.json',encoding='utf-8')),p); seo.generate(p)"
```
