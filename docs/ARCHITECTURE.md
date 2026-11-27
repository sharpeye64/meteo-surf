# Architecture

## Vue d'ensemble

```
          sources publiques (Open-Meteo, Ifremer MARC, Copernicus Marine, CANDHIS, Météo-France, Shom REFMAR)
                                   │
                    ┌──────────────▼───────────────┐
                    │  ROBOT Python (pipeline/)    │  GitHub Actions, ≈ toutes les heures (+ cron-job.org)
                    │  build.py orchestre          │
                    └──┬────────────┬──────────┬───┘
                       │            │          │
        web/data/forecast.json   pages SEO     branche git « history »
        web/data/app/*.json      statiques     (archive prévision / mesure)
                       │            │
                    ┌──▼────────────▼──┐
                    │   GitHub Pages    │  → https://houlalah.fr
                    └──┬────────────┬───┘
                       │            │
         site (web/index.html)    application mobile Expo (app/)
         lit forecast.json        lit web/data/app/
```

Il n'y a **aucun serveur** à maintenir : tout est généré par le robot puis servi en fichiers statiques.

## Dépôt

| Dossier | Rôle |
|---|---|
| `pipeline/` | Robot Python : récupération des sources, calculs, génération des données et des pages |
| `web/` | Site publié tel quel par GitHub Pages. `index.html` = toute l'application web (HTML, CSS et JavaScript dans un seul fichier) |
| `web/data/` | `forecast.json` (site), `app/` (application mobile). Générés |
| `web/spots/`, `web/bouees/`, `web/meteo-surf-*/`, `sitemap.xml`, `robots.txt`, `og/` | Pages SEO **générées** (ignorées par git, recréées à chaque passage) |
| `app/` | Application mobile Expo (React Native, TypeScript) |
| `tests/test_offline.py` | Tout le robot avec des sources simulées, sans internet. **Doit rester vert** |
| `tools/` | Utilitaires : marées (`get_refmar`, `fit_tides`), logo (`trace_logo`, `brand_assets`, `make_og`, `app_icons`), serveur local, rapports |
| `tides/constants/` | Constantes harmoniques des ports (Socoa, Boucau, Brest…) |
| `brand/` | Logo source fourni par le porteur (ne pas redessiner) |
| `docs/` | Cette documentation |
| `.github/workflows/update.yml` | Le robot (planification, tests, construction, archive, déploiement) |

## Le robot (`pipeline/`)

| Module | Rôle |
|---|---|
| `build.py` | Orchestration : récupère tout, mélange les modèles, corrige avec la bouée, écrit `forecast.json`, appelle la génération des pages et l'archive |
| `openmeteo.py` | Vagues (4 modèles) et vent (4 modèles) par spot via Open-Meteo |
| `marc.py` | Modèle côtier Ifremer MARC (OPeNDAP) |
| `buoy.py`, `meteofrance.py` | Bouée Gascogne : API Météo-France (prioritaire, clé en secret GitHub), Copernicus, NOAA en secours |
| `candhis.py` | 7 houlographes CANDHIS (pages publiques Cerema) |
| `ibi_buoys.py` | 14 bouées Copernicus Marine In Situ (Espagne, Portugal) |
| `tides.py` | Marées harmoniques, coefficient (Brest) |
| `history.py` | Archive « prévision contre réalité » (branche `history`) et calcul de fiabilité |
| `archive.py` | Archive v2 aux points des bouées : modèles, MARC, mélanges brut et corrigé, provenance (issue #1, `docs/archive-modeles.md`) |
| `melange.py` | Mélange des modèles et correction par la bouée : le calcul de la prévision publiée, partagé avec l'archive |
| `appdata.py` | Fichiers allégés pour l'application (`web/data/app/`) |
| `seo.py`, `bouees.py`, `zones.py`, `pages.py`, `seotext.py`, `share.py` | Pages statiques (spots, bouées, régions, pages de texte), sitemap, images de partage |
| `config.py` | Réglages : modèles et poids, bouées, fuseau (`Europe/Paris`), adresse du site |
| `spots.json` | Les 214 spots et leurs caractéristiques (orientation, type, fond, marée, port de marée…) |

**Règles du robot**
- **Publication contrôlée** (issue #3, [securisation-publication.md](securisation-publication.md)) : sur GitHub, le robot génère dans `_site/` (`METEO_OUT_DIR`), puis `python -m tools.check_site _site` vérifie spots, bouées, fiches de l'appli, sitemap, canoniques, JSON et absence de données de test. Refus = pas d'envoi, la version en ligne reste. Seule `main` déploie.
- **Résilience** : toute source sauf Open-Meteo peut échouer sans bloquer la génération. Les erreurs sont listées dans `meta.errors`. Une bouée absente est reprise depuis l'archive (`build.keep_silent`), puis marquée muette au-delà de 48 h.
- **Heures** : en interne, le robot calcule en heure de Paris (`config.TIMEZONE`, `seo.paris_now()`, car il tourne en UTC). À la publication, `timefmt.localize` écrit chaque instant en ISO 8601 **avec décalage**, à l'heure locale du lieu (Portugal : Lisbonne). Voir [heures.md](heures.md).
- **Pas de données inventées** : une donnée absente n'est pas affichée, ou est signalée comme absente.

## Le site (`web/index.html`)

- **Un seul fichier** d'environ 600 Ko (CSS dans `<style>`, JavaScript dans `<script>`). Il lit `web/data/forecast.json` (6,5 Mo bruts, 727 Ko compressés). Si ce fichier manque, il interroge Open-Meteo directement (mode secours, `loadLive`).
- **Bibliothèques** chargées à la demande depuis jsDelivr : MapLibre GL 4.7.1, fond de carte OpenFreeMap (style positron recoloré). Polices Google : Unbounded et Manrope.
- **Blocs de code** :
  - accueil cartographique : bloc « ACCUEIL PREMIUM OCEAN v2 », fonctions `home*`, classes `ho-` ;
  - page de prévisions : bloc « PAGE DE PRÉVISIONS V3 », fonctions `pv*`, classes `pv-` ;
  - couches de style Premium Ocean en fin de `<style>`.
- **Adresses** :

| Adresse | Contenu | Canonique |
|---|---|---|
| `/` | Accueil (carte) | `/` |
| `/?spot=<slug>` | Application ouverte sur un spot | `/spots/<slug>/` (posée par un script d'en-tête, tenue à jour par `setCanon`) |
| `/spots/<slug>/` | Page SEO du spot | elle-même |
| `/bouees/<slug>/` | Page SEO d'une bouée | elle-même |
| `/meteo-surf-<zone>/` | Page régionale | elle-même |

- **Code mort** : il reste à supprimer un jour. Fonctions `*_v1` de l'ancienne page, directions artistiques de test B et C (`?da=b|c|v3`), ancien océan WebGL (`ocean*`) encore initialisé.
- **Hors ligne** : `sw.js` (service worker, PWA) garde les dernières prévisions.

## L'application mobile (`app/`)

Voir [MOBILE_APP.md](MOBILE_APP.md). Elle lit `https://houlalah.fr/data/app/` (`index.json`, `spots/<slug>.json`, `bouees/<slug>.json`).

## Environnements

| Environnement | Où | Comment |
|---|---|---|
| **Production** | branche `main` → GitHub Pages → houlalah.fr | tout push sur `main` déclenche le robot et le déploiement. **Jamais sans le « Oui, publie » du porteur** |
| **Test** | une branche locale par chantier (ex. `seo-corrections`), aperçu local `http://localhost:8000` | serveur « site » de `.claude/launch.json`, ou `cd web && python -m http.server 8000` |
| **Données de test** | `python -m tests.test_offline` | écrit dans un **dossier temporaire** (jamais dans `web/`) ; tout porte une marque de test refusée par `tools/check_site.py` |
| **Application** | Expo Go sur iPhone : `& .\app\tester-sur-telephone.ps1` ; aperçu web : configuration `appli-web` (port 8081) | |

**Repères git** : avant chaque gros chantier, une branche et un tag `avant-…` (par exemple `avant-accueil-ocean`, `avant-seo-corrections`). La branche `history` est réservée à l'archive du robot.

## Planification et secrets

- **Planification** : trois séries de crons GitHub décalées (environ un passage par heure), plus cron-job.org (environ toutes les 30 min), plus un passage à chaque push sur `main`. GitHub saute parfois des passages programmés : 9 h de trou constatées le 11/11.
- **Secrets** : uniquement dans GitHub → Settings → Secrets. Aujourd'hui, `METEOFRANCE_APIKEY` (API Météo-France). **Jamais dans le dépôt, la documentation ou un message.**

## Coûts d'exploitation (estimation)

| Poste | Coût actuel | Remarque |
|---|---|---|
| Hébergement (GitHub Pages, Actions) | 0 € | dépôt public, minutes Actions gratuites |
| Domaine houlalah.fr | ≈ 10–15 €/an | chez le registrar |
| Open-Meteo | 0 € | **usage non commercial uniquement** ; un usage commercial demande un abonnement |
| API Météo-France, Copernicus, CANDHIS, Shom | 0 € | comptes gratuits ou accès public |
| Fond de carte OpenFreeMap, jsDelivr | 0 € | |
| Mesure d'audience GoatCounter | 0 € | gratuit en usage non commercial |
| cron-job.org | 0 € | |
| Apple Developer (application iPhone) | 99 $/an | **prévu, pas encore pris** |
| Google Play (application Android) | 25 $ une fois | prévu |
| EAS (compilation et mises à jour de l'application) | 0 € (offre gratuite) | à surveiller selon l'usage |

## Limitations techniques connues

- **Poids** : `forecast.json` pèse 6,5 Mo, chargés par l'accueil et l'application web. À alléger (résumé compact, puis détail à la demande).
- **Un seul fichier** : `web/index.html` est très gros et contient du code mort, ce qui rend les modifications délicates. Les classes CSS génériques de l'ancien code entrent en collision avec le nouveau, d'où les préfixes `pv-` et `ho-`.
- **Fraîcheur des bouées** : elle dépend des sources. Les données Copernicus et Météo-France ont parfois plusieurs heures de retard, et certaines stations coupent (Anglet depuis le 18/11).
- **Marées** : seulement pour les spots rattachés à un port français. Les 75 spots d'Espagne et du Portugal n'en ont pas.
- **Lecture de CANDHIS** : passe par les pages publiques. L'API officielle demande un jeton du Cerema.
- **Planification** : dépendante de GitHub, qui peut sauter des passages.
