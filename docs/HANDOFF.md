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

- **Branche `docs-onboarding`** (non publiée, non poussée) : documentation commune complète. Elle comprend :
  - `AGENTS.md` ;
  - dans `docs/` : PROJECT_CONTEXT, ARCHITECTURE, DATA_SOURCES, PRODUCT, DESIGN_SYSTEM, MOBILE_APP, SEO, DECISIONS, ROADMAP, CHANGELOG, COLLABORATION, ONBOARDING_CHATGPT et ce HANDOFF.
- **Pour que ChatGPT y accède** : pousser cette branche sur GitHub (sans toucher `main`), puis la fusionner dans `main` quand le porteur valide. La documentation ne change pas le site, mais un push sur `main` relance le robot et le déploiement.

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

## Remettre les vraies données après les tests

```
curl -s -o web/data/forecast.json https://houlalah.fr/data/forecast.json
python -c "import json; from pipeline import appdata, seo; p=json.load(open('web/data/forecast.json',encoding='utf-8')); appdata.generate(json.load(open('pipeline/spots.json',encoding='utf-8')),p); seo.generate(p)"
```
