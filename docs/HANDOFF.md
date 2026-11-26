# HANDOFF — état du projet (à garder court)

_Dernière mise à jour : 26/11/2026, par Claude Code._

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

- **Issue #3, branche `securiser-publication`** (poussée, pull request ouverte pour revue, **non fusionnée**, repère `avant-securiser-publication`) : tests isolés dans un dossier temporaire, marques de test, contrôle avant publication `tools/check_site.py`, génération dans `_site/`, déploiement et archive depuis `main` seulement, `health.json`. Rapport et preuves : [securisation-publication.md](securisation-publication.md). Attend la revue de ChatGPT puis le « Oui, publie ».
- **Branche `docs-onboarding`** (poussée, non fusionnée) : documentation commune. `securiser-publication` part de cette branche : la fusionner inclut aussi la documentation.
- **Ordre retenu ensuite (non commencé)** : #7 quotas et cache → #2 heures et Portugal → #1 archives → #4, #6, #8 → #5, #9 après la collecte → #10 après les licences.

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
