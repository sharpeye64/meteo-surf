# Contrat horaire des données (issue #2)

_27/11/2026, Claude Code, branche `heures-locales` (repère `avant-heures-locales`). Non publié._

## Le contrat

Chaque **instant** publié par le robot s'écrit en **ISO 8601 avec décalage**, à l'**heure locale du lieu** :

| Lieu | Fuseau (IANA) | Exemple pour le même instant |
|---|---|---|
| France, bouée Gascogne | `Europe/Paris` | `2026-11-27T10:00+01:00` |
| Espagne (Pays basque, Cantabrie, Asturies, Galice) | `Europe/Madrid` | `2026-11-27T10:00+01:00` |
| Portugal continental | `Europe/Lisbon` | `2026-11-27T09:00+00:00` |

- Les 16 premiers caractères donnent l'**heure locale affichable**. Le code qui découpe `t.slice(11,16)` continue donc de fonctionner.
- Le décalage rend l'instant **exact** partout, quel que soit le fuseau du navigateur ou du téléphone.
- Les **dates seules** (`2026-11-27` : soleil, coefficients) sont des dates locales du lieu.
- **Concerné** : `forecast.json` (`meta.time.version = 2`), `data/app/` (index et fiches), `health.json`, ainsi que les pages générées (affichage à l'heure du lieu).
- **Champ `tz`** : il donne le fuseau de chaque spot, de chaque bouée et de chaque fiche de l'appli.
- **Non concerné** : l'**archive** (branche `history`). Elle n'est pas réécrite et reste en heure de Paris sans décalage. Les nouvelles archives (#1) devront adopter ce contrat.

## Lecture : une seule règle, partout

Le robot (`pipeline/timefmt.py`), le site (`web/index.html`, bloc « CONTRAT HORAIRE ») et l'application (`app/src/time.ts`) appliquent la même règle :
- **Chaîne avec décalage** : c'est l'instant exact.
- **Chaîne sans décalage** (ancien format, archive, ancienne donnée en cache) : c'est l'heure de **Paris**, explicitement. Ce n'est **jamais** le fuseau de l'appareil.
- **Heure ancienne ambiguë** (la nuit du passage à l'heure d'hiver, 2 h à 3 h, qui existe deux fois) : c'est la **première** occurrence. Ce choix est documenté, pas déduit. Dans une série ordonnée, en revanche, le robot sait quelle heure est la seconde.
- **Heure inexistante** (la nuit du passage à l'heure d'été) : on prend le décalage d'avant le changement, et le cas est compté (`meta.time.nonexistent`).
- **Comparaisons, âges, rapprochements** (prévision contre mesure, carte de l'accueil) : ils se font sur des **instants**, jamais sur des chaînes. Une bouée portugaise et un spot espagnol se comparent heure pour heure.

## Ce qui s'affiche

| Endroit | Heure affichée |
|---|---|
| Page d'un spot, fiche de l'appli | **heure du spot** : Lisbonne au Portugal. Frise, « maintenant », lever et coucher, marées, mise à jour |
| Mesure d'une bouée (« aujourd'hui 22 h », âge) | heure du **lieu de la bouée**, avec un âge exact |
| Carte de l'accueil (site) et onglets Carte et Spots (appli), qui couvrent plusieurs fuseaux | une seule horloge, **heure de Paris**, et le **même instant** pour tous les spots |
| Pages générées (Google) | heure locale du spot ou de la bouée |

## Découverte : Open-Meteo ne suit pas le changement d'heure dans ses séries

Vérifié le 27/11/2026 (une requête) : avec `timezone=Europe/Paris`, Open-Meteo écrit **toute** la série avec **un seul décalage**, celui du moment de la requête (`utc_offset_seconds`). Le 25/10/2026 y compte 24 heures, sans heure répétée.
- **Avant ce lot** : les prévisions situées après un changement d'heure, dans la fenêtre de 7 jours, étaient décalées d'une heure.
- **Maintenant** : l'instant est l'heure écrite moins `utc_offset_seconds`, exactement, puis il est réécrit à l'heure du lieu avec le bon décalage.
- **Cache (#7)** : une réponse obtenue avant un changement d'heure est ramenée au décalage de la réponse « mer » avant l'alignement.

## Transition

1. **Le robot** publie le nouveau format dès la mise en ligne.
2. **Le site et l'application** lisent les deux formats. Le site et ses données partent ensemble ; le service hors ligne (`sw.js`) prend le réseau d'abord.
3. **L'archive** n'est pas réécrite (voir plus haut).
4. **Application** : il n'y a pas de version sur les stores, seulement Expo Go chez le porteur. Pas d'ancienne version à ménager.
5. **Retour en arrière** : tag `avant-heures-locales`. L'ancien site lirait mal le nouveau format (`t + ':00'`) : il faut revenir sur le robot **et** sur le site ensemble, ce qui est automatique puisqu'ils partent du même commit.

## Tests (job `surete` de GitHub Actions, sans réseau)

- `python -m tests.test_heures` : écriture et lecture, France, Espagne et Portugal, série Open-Meteo traversant le 25/10, heure répétée déduite de l'ordre, heure du 29/03 absente, fuseaux des 214 spots et des 22 bouées, axe portugais commençant à minuit de Lisbonne, mêmes valeurs aux mêmes instants, aucune heure sans décalage restante.
- `node tests/heures_site.test.js` et `node tests/heures_app.test.mjs`, lancés sous **4 fuseaux de téléphone** (Paris, Lisbonne, New York, Tokyo) : mêmes instants et mêmes libellés partout ; heure ancienne ambiguë et heure absente ; journée de 25 h et de 23 h ; « aujourd'hui » jugé à l'heure du lieu.
- `tools/check_site.py` refuse un `forecast.json` sans contrat horaire ou avec des heures sans décalage.
- Vérifié dans le navigateur, avec des données au nouveau format :
  - Supertubos affiche « Maintenant · 10h15 », lever à 7h05, mise à jour à 10h05 (heure de Lisbonne) ;
  - Lacanau affiche 11h15 (heure de Paris) ;
  - la carte de l'accueil montre le même instant (11 h à Paris, 10 h à Lisbonne) ;
  - l'ancien format s'affiche toujours correctement ;
  - aucune erreur dans la console.

## Limites

- **Heure répétée d'octobre** : une valeur isolée ambiguë, par exemple la dernière mesure d'une bouée absente de sa série, prend la première occurrence ; elle est comptée dans `meta.time.ambiguous`.
- **Calculs internes du robot** (mélange, correction par la bouée, marées, archive) : ils restent faits sur ses heures internes. Seule la publication change. Autour d'un changement d'heure, l'alignement interne des marées et de MARC sur l'axe Open-Meteo n'est pas repris dans ce lot.
- **Écran de l'application** : non vérifié sur un téléphone, seulement par TypeScript et les tests. À voir dans Expo Go avec les vraies données après publication.
