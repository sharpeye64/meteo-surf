# Archive des modèles aux points des bouées (issue #1)

_27/11/2026, Claude Code, branche `archive-modeles` (repère `avant-archive-modeles`). Non publié._

## Ce qui change

| | Avant | Après |
|---|---|---|
| Prévision archivée aux 21 bouées | le « best match » d'Open-Meteo seulement (`coast_runs/`) | **les 4 modèles un par un**, **MARC** là où il existe, le best match, le **mélange brut** et le **mélange corrigé** (`buoy_runs/`) |
| Gascogne | 4 modèles (`runs/`) | idem, plus MARC, les mélanges et la provenance |
| Mélange réellement calculé | archivé nulle part | archivé à chaque passage, brut et corrigé |
| Provenance | aucune | heure de collecte, cache ou non, **cycle (run) de chaque modèle** quand il est connu, version du moteur |
| Heures | heure de Paris sans décalage | **ISO 8601 avec décalage** (contrat horaire v2, [heures.md](heures.md)) |
| Doublons | **≈ 40 % des passages archivés deux fois** (deux passages du robot dans l'heure d'archive) | un seul enregistrement par heure ; les anciens doublons sont ignorés à la lecture |
| Requêtes Open-Meteo | 25 par passage d'archive, ≈ 475 par jour | **5 requêtes groupées** (22 bouées chacune), via le cache : ≈ 25 par jour |

## Les archives existantes sont préservées

- **Aucun fichier existant n'est réécrit ni supprimé.** `runs/`, `coast_runs/`, `obs/` et `coast_obs/` gardent leur format et continuent d'être alimentés, avec le même contenu qu'avant : mêmes points, mêmes variables, même découpage sur 97 h.
- **Les mesures** (`obs/`, `coast_obs/`) sont fusionnées heure par heure, comme avant.
- **Les doublons déjà présents restent dans les fichiers.** Les lecteurs les ignorent : `history.reliability`, `history.read_coast_runs`, `tools/coast_report.py`. Pour une heure en double, on garde le premier passage.
- **Conséquence visible** : la « fiabilité mesurée » (`reliability`) ne compte plus deux fois les heures doublées. Les chiffres peuvent bouger légèrement ; ils sont plus justes.
- **Une seule différence pour les anciens formats** : la prévision peut venir du cache (#7). Le cache est redemandé dès qu'un modèle publie un nouveau run, donc la prévision archivée est toujours celle du **dernier run disponible**, comme avant.

## Le nouveau fichier : `history/buoy_runs/AAAA-MM.jsonl`

Une ligne par passage d'archive (heures UTC multiples de 3, `main` seulement). Ajout seul : rien n'est jamais réécrit. Un échantillon réel (3 bouées) est dans [archive-modeles-exemple.json](archive-modeles-exemple.json).

```
{"v": 2, "scope": "points des bouées (pas la prévision publiée aux spots)",
 "issued": "2026-11-27T17:00+01:00",       heure du passage (instant exact)
 "generated": "2026-11-27T17:13+01:00",    instant de la génération
 "t0": "2026-11-27T17:00+01:00", "step_h": 1, "n": 97,   l'heure k vaut t0 + k heures exactes
 "engine": {"melange": "melange-1", "code": "<commit>", "correction_hours": 24, ...},
 "weights": {"marc": 0.3, "mfwam": 0.25, "ewam": 0.25, "ecmwf": 0.15, "gfs": 0.05},
 "correction": {"ratio": 1.2, "ratio_measured": 1.2, "t_obs": "…+01:00", "hours": 24, "status": "appliquée"},
 "sources": {"mfwam": {"api": "meteofrance_wave", "fetched": "…", "from": "api|cache|cache-dégradé",
                       "run": "2026-11-27T01:00+01:00", "run_available": "…", "native_step_h": 3.0}, ...},
 "missing": {"ewam": "raison"},             modèle absent de ce passage, avec la raison
 "b": {"03302": {"lat", "lon", "tz": "Europe/Paris",
                 "models": {"mfwam": [Hs × 97], "ewam": [...], "ecmwf": [...], "gfs": null},
                 "marc": {"hs": [...], "cell": [lat, lon], "km": 1.8} | null,
                 "base": [Hs best match],   série de repli du mélange
                 "mix_raw": [Hs],            mélange brut (avant correction)
                 "mix": [Hs]}, ...}}         mélange corrigé (après correction par la bouée Gascogne)
```

### Règles

- **Instants** : ISO 8601 avec décalage. Les réponses Open-Meteo sont replacées sur l'axe **par instant**, y compris une réponse en cache écrite avec un autre décalage (avant un changement d'heure).
- **Valeur absente** = `null`. **Modèle absent** = `null` partout, avec sa raison dans `missing`. GFS sur une maille « terre » (0,00 m partout) = `null`, comme dans la prévision.
- **Cycle d'un modèle (`run`)** : il est lu dans les métadonnées publiques d'Open-Meteo (`last_run_initialisation_time`), qui ne sont pas comptées dans les quotas. On ne l'écrit que s'il était disponible **avant** la collecte, depuis au moins 10 minutes, délai conseillé par Open-Meteo. Sinon `null`, avec la raison dans `run_note`. On ne l'invente jamais :
  - **best match** : toujours `null`, car il n'est lié à aucun run unique ;
  - **MARC** : toujours `null`, car la série OPeNDAP agrégée ne donne pas d'heure de run.
- **Échéance** (horizon de prévision) d'une valeur = son heure de validité − `run`. Quand `run` est `null`, on calcule par rapport à `fetched`, l'heure de collecte.
- **MARC** n'est retenu que si sa maille est à 6 km au plus de la bouée (grille d'environ 3,7 km). Le test réel du 27/11 l'a trouvé pour 5 bouées : Cap Ferret (1,8 km), Anglet (0,5), Saint-Jean-de-Luz (0,9), Donostia (0,9), Pasaia (0,5). Il vaut `null` ailleurs : Bretagne, Galice, Portugal, Gascogne au large, Bilbao.
- **Mélanges** : ils viennent du **même code** que la prévision publiée (`pipeline/melange.py`, extrait de `build.py` sans changement de méthode). On peut les recalculer à l'identique depuis l'archive, mais ils sont conservés tels quels, comme demandé : une évolution future de l'algorithme ne les rendra pas faux.
- **Périmètre** : ce sont les calculs **aux points des bouées**, pour comparer prévision et mesure. Ce n'est **pas** la prévision publiée aux spots, qui est calculée sur 176 points en mer distincts des bouées. Le champ `scope` le rappelle.
- **Version du moteur** : `engine.melange` (`melange-1`). Elle doit changer si les poids, le repli ou la correction changent. `engine.code` donne le commit.

## Volumes et coûts (mesurés)

### Requêtes Open-Meteo

Mesuré par `python -m tools.api_budget`, sur les métadonnées réelles des modèles.

| | Avant | Après |
|---|---|---|
| Passages d'archive par jour | 19 (dont 11 doublons) | 8 (le premier de chaque heure d'archive) |
| Requêtes par jour (H1 : une requête = un appel) | 475 | **≈ 25** (best match 8, MF-WAM 4, EWAM 4, ECMWF 5, GFS 4) |
| Points par jour (H2 : un point = un appel) | 475 | **≈ 550** (+75 par jour) |

- **H1** : −450 appels par jour.
- **H2** : +75 appels par jour, contre une limite gratuite de 10 000. L'archive pèse donc moins de 1 % de la limite.
- **Rappel #7** : avec l'hypothèse H2, la consommation totale du robot dépasse déjà la limite gratuite ([quotas-licences.md](quotas-licences.md)). Ce lot ne change presque rien à ce constat.
- **Essai réel** du 27/11, un seul passage : 5 requêtes, toutes acceptées (HTTP 200), 22 points chacune.

### Stockage

Mesuré sur une ligne réelle et sur l'historique git réel de `coast_runs`.

| | Par passage | Par jour (8 passages) | Par mois |
|---|---|---|---|
| Ligne v2 (22 bouées × 97 h) | 77 Ko bruts, 11 Ko compressés | 620 Ko bruts | **≈ 18 Mo bruts** dans le dossier |
| Croissance du dépôt git | | | **≈ 2 à 3 Mo** par mois |

- **Croissance du dépôt git** : nous avons rejoué les 128 vrais passages de `coast_runs`, un commit par passage. Git stocke 0,45 Mo pour 3,2 Mo bruts, soit environ 7 fois moins.
- **Un fichier par jour** au lieu d'un par mois ne change presque rien : 0,43 Mo au lieu de 0,45 Mo. On garde donc un fichier par mois, comme pour les archives existantes.
- **Pas de gzip mensuel réécrit** : chaque version compressée serait un nouveau fichier complet pour git. Ce serait bien pire qu'un fichier texte auquel on ajoute des lignes.
- **Option pour plus tard**, à décider : compresser une seule fois les **mois terminés**, sans perte et avec vérification. Le robot télécharge l'archive complète (`fetch --depth=1`) à chaque passage. Avec environ 18 Mo de plus par mois, cela fera environ 220 Mo de fichiers bruts au bout d'un an, environ 30 Mo une fois compressés pour le transfert.

### Coût en argent

Aucun. Open-Meteo et MARC sont gratuits pour cet usage non commercial. GitHub accepte ces volumes : un dépôt doit rester sous 5 Go, et un fichier sous 100 Mo, alors qu'un mois de `buoy_runs` fait environ 18 Mo.

## Tests (`python -m tests.test_archive`, job `surete`, sans réseau)

- **Calcul inchangé** : le mélange extrait donne exactement l'ancien calcul de `build.py` sur 200 tirages, avec des valeurs manquantes, le repli et la correction. `forecast.json` est identique avant et après sur les 214 spots (test hors ligne rejoué sur les deux versions).
- **Anciennes archives** :
  - `runs/` et `coast_runs/` sont conservés à l'octet près : on ne fait qu'ajouter des lignes ;
  - toutes les anciennes mesures sont gardées ;
  - les doublons sont ignorés à la lecture, en gardant le premier passage.
- **Pas de doublon** : deux passages dans la même heure donnent une seule ligne dans chaque fichier, et le second passage n'envoie aucune requête.
- **Contenu de la ligne v2** :
  - aucune heure sans décalage ;
  - modèle refusé = `null` avec sa raison ; maille « terre » = `null` ;
  - réponse en cache d'avant un changement d'heure alignée par instant ;
  - MARC retenu à 2 km, refusé hors de la grille ;
  - mélanges brut et corrigé recalculés à l'identique depuis les ingrédients archivés.
- **Provenance** :
  - le cycle du modèle est écrit quand il est connu ;
  - il n'est pas affirmé quand le run a été publié moins de 10 min avant la collecte ;
  - il vaut `null` quand les métadonnées sont illisibles, et toujours pour le best match et MARC.
- **Fiabilité** : un passage en double ne compte plus deux fois.

## Ce qui reste hors de ce lot

- **Pas de changement** des poids, de la prévision publiée ni de l'affichage.
- **Pas d'archive de la prévision publiée aux spots** : 214 spots × 168 h, soit environ 150 Mo par mois. Elle reste dans `forecast.json` au moment de la publication. On pourra l'ajouter plus tard pour quelques spots témoins.
- **Exploitation** : écarts par modèle, par bouée et par échéance. C'est l'objet des issues #5 et #9, après 30 jours de collecte.
