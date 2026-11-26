# Sécurisation de la publication (issue #3)

_26/11/2026, Claude Code, branche `securiser-publication` (repère `avant-securiser-publication`). Non publié._

## Le risque corrigé

Avant ce lot, le test hors ligne écrivait des données **simulées** dans `web/`, juste avant la vraie génération. Si la génération des données de l'application ou des pages SEO échouait, l'erreur était avalée et les fausses fiches ou pages restaient dans `web/`, qui était envoyé tel quel sur houlalah.fr.

## Ce qui change

| Où | Changement |
|---|---|
| `pipeline/config.py` | `METEO_OUT_DIR` : le robot peut écrire ailleurs que dans `web/` (`config.OUT_DIR`). `METEO_TEST=1` : exécution de test (`config.TEST_RUN`) |
| `tests/test_offline.py` | Écrit dans un **dossier temporaire**, jamais dans `web/`. Il vérifie lui-même qu'il n'a rien modifié dans `web/` et que le contrôle refuse son propre site de test |
| `pipeline/seo.py`, `appdata.py`, `build.py` | En test, tout ce qui est produit porte une **marque de test** : `meta._test`, `_test` dans l'index de l'appli et `health.json`, balises `noindex` + `houlalah-test` dans les pages |
| `pipeline/seo.py`, `build.py` | Les échecs des pages bouées et zones (`seo_bouees`, `seo_zones`) et l'échec SEO sont maintenant **écrits** dans `forecast.json` (avant, l'erreur SEO n'y figurait jamais) |
| `pipeline/safe.py` | Messages publics et journaux sans secret (voir « Secrets ») |
| `pipeline/build.py` | Nouveau `health.json` : heure de génération, nombre de spots, erreurs (adresses et clés masquées), âge de chaque bouée. **Aucun secret** |
| `tools/check_site.py` | **Contrôle avant publication** (voir ci-dessous). Code de sortie 1 = publication refusée |
| `.github/workflows/update.yml` | Le robot génère dans `_site/` (copie de `web/`), le contrôle passe, puis seul `_site/` est envoyé. Job `surete` sans réseau (aussi sur les pull requests), dont dépend la vraie génération. Déploiement et archive **uniquement depuis `main`**. Échec d'archive signalé (annotation + résumé). File d'attente par branche : un essai sur une branche n'annule jamais un passage de production |

Rien d'autre ne change : même rythme d'appels aux API, mêmes heures, même archive, même application.

## Le contrôle avant publication (`tools/check_site.py`)

Les quantités attendues viennent du **catalogue et de la configuration**, jamais d'un nombre figé :

- **spots** : les slugs de `pipeline/spots.json` doivent être exactement ceux de `forecast.json`, de l'index de l'appli et des pages `spots/<slug>/` ;
- **bouées** : les pages `bouees/<slug>/` attendues sont calculées par `bouees.collect()` sur les données du passage ; chaque bouée de l'index de l'appli doit avoir sa fiche ;
- **zones et pages de texte** : d'après `zones.ZONES` (régions présentes dans le catalogue) et `pages.ALL` ;
- **sitemap** : exactement ces adresses, sans doublon, toutes sur `https://houlalah.fr/` ;
- **canoniques** : chaque page pointe vers sa propre adresse publique ;
- **JSON** valides (forecast, index et fiches de l'appli, health) ;
- **génération** : l'appli et `forecast.json` viennent du même passage, et le passage a moins de 3 h ;
- **aucune trace de test** (`_test`, `houlalah-test`), aucune adresse `localhost`, aucun secret dans `health.json`, aucune page en trop.

**Panne de source ou artefact incomplet ?** Une erreur de source (une bouée, MARC, Météo-France…) est **tolérée** : elle apparaît en avertissement, le site part quand même, comme aujourd'hui. Une erreur de **génération** (`appdata`, `seo`, `seo_bouees`, `seo_zones`) ou un fichier manquant **bloque** la publication.

**En cas de refus** : le workflow s'arrête avant l'envoi. GitHub Pages garde la **dernière version valide**. Le passage apparaît en échec (croix rouge) avec le motif dans le résumé.

## Preuves (après la revue de ChatGPT)

### 1. Vraie exécution GitHub, sans déploiement
Un seul passage lancé à la main (`workflow_dispatch`) sur `securiser-publication`, avec les vraies sources : [run 45906766602](https://github.com/sharpeye64/meteo-surf/actions/runs/45906766602), commit `e013810`.

| Job / étape | Résultat |
|---|---|
| `surete` (tests sans réseau) | ✅ réussi |
| `build` : construction réelle dans `_site/` | ✅ réussi |
| `build` : **contrôle avant publication** | ✅ OK : 214 spots catalogue = 214 forecast = 214 appli ; 22 bouées appli = 22 pages bouées ; 254 pages attendues ; 255 adresses au sitemap ; 498 fichiers texte inspectés ; génération âgée de 0,08 h |
| avertissement toléré | ⚠️ `ibi_6200084` : aucun fichier récent (panne de source, pas d'artefact incomplet) |
| `build` : enregistrer l'archive | ⏭️ **ignorée** (pas `main`) |
| `deploy` | ⏭️ **ignoré** (pas `main`) |

Après ce passage, `https://houlalah.fr/health.json` répond toujours 404 : la production n'a pas été touchée.

La pull request elle-même déclenche maintenant le job `surete` seul ([run 45906749827](https://github.com/sharpeye64/meteo-surf/actions/runs/45906749827)) : ✅ réussi, `build` et `deploy` ignorés, aucun appel réseau.

### 2. Tests de sûreté, exécutés dans GitHub Actions (job `surete`)
- `python -m tests.test_offline` : vert. Isolation vérifiée sur **tout** `web/` (instantané chemin, taille, date avant et après, ajouts compris) : « 20 fichiers de web/ inchangés, aucun ajouté » sur le robot GitHub, où `web/` ne contient que les sources du site.
- `python -m tests.simulate_pannes` : **32/32 scénarios conformes** (tableau ci-dessous).
- `python -m tests.panne_bout_en_bout` : exceptions réelles dans `appdata.generate` et `bouees.generate`, plus une exception de source contenant une **fausse** clé, une adresse avec identifiants et paramètres et un en-tête `Authorization`. Résultat : erreurs enregistrées, **aucune fausse valeur dans aucun fichier produit** (message public : `GET https://***@api.exemple.test/v2/bouees?… Authorization: *** key=***`), publication refusée. La valeur exacte d'un secret glissée dans une page est détectée.
- Les trois scripts renvoient un code de sortie non nul en cas d'échec ; la vraie génération (`build`) dépend du job `surete`.

| Scénario | Résultat | Motif |
|---|---|---|
| site de référence (marques de test retirées) | ✅ publié |  |
| panne d'une source (CANDHIS) : tolérée | ✅ publié |  |
| données de test dans forecast.json | ⛔ refusé | données de test : 1 fichier(s) marqué(s) (ex. ['data/forecast.json']) |
| une page de test oubliée | ⛔ refusé | données de test : 1 fichier(s) marqué(s) (ex. ['spots/lacanau/index.html']) |
| échec des données de l'appli (exception) | ⛔ refusé | robot : appdata — KeyError: 'marine' |
| échec des pages bouées (exception) | ⛔ refusé | robot : seo_bouees — ValueError |
| échec SEO complet (exception) | ⛔ refusé | robot : seo — OSError |
| pages bouées absentes | ⛔ refusé | pages absentes : 23 (ex. ['bouees', 'bouees/a-coruna', 'bouees/anglet', 'bouees/belle-ile']) |
| une page de spot absente | ⛔ refusé | pages absentes : 1 (ex. ['spots/lacanau']) |
| une fiche spot de l'appli absente | ⛔ refusé | appli fiche spot lacanau absent (lacanau.json) |
| une fiche bouée de l'appli absente | ⛔ refusé | appli fiche bouée sines absent (sines.json) |
| index de l'appli : JSON tronqué | ⛔ refusé | appli index.json : JSON invalide (Unterminated string starting at: line 1 column 8 (char 7)) |
| forecast.json absent | ⛔ refusé | forecast.json absent (forecast.json) |
| un spot manquant dans forecast.json | ⛔ refusé | forecast.json : spots différents du catalogue (manquants ['martinhal'], en trop []) |
| appli d'une autre génération | ⛔ refusé | appli : génération différente de forecast.json |
| sitemap avec adresse locale | ⛔ refusé | sitemap : 1 adresse(s) en trop, 0 manquante(s) |
| sitemap absent | ⛔ refusé | sitemap.xml absent |
| canonique fausse | ⛔ refusé | canoniques incorrectes : 1 (ex. ['spots/lacanau']) |
| page en trop (reste d'un ancien spot) | ⛔ refusé | pages inattendues : 1 (ex. ['spots/ancien']) |
| secret dans health.json | ⛔ refusé | secret possible dans 1 fichier(s) (ex. ['health.json']) : refusé |
| index.html du site absent | ⛔ refusé | index.html absent |
| fiche JSON valide d'un autre spot | ⛔ refusé | appli : fiches de spots incorrectes : 1 (ex. ["lacanau (fiche d'un autre spot)"]) |
| fiche de spot aux séries vides | ⛔ refusé | appli : fiches de spots incorrectes : 1 (ex. ['lacanau (séries vides, trop courtes ou de longueurs différentes |
| fiche de spot aux séries de longueurs différentes | ⛔ refusé | appli : fiches de spots incorrectes : 1 (ex. ['lacanau (séries vides, trop courtes ou de longueurs différentes |
| spot en double dans l'index de l'appli | ⛔ refusé | appli : spots en double dans l'index |
| bouée de l'appli absente de forecast.json | ⛔ refusé | appli : bouées de l'index différentes de forecast.json (manquantes ['faro'], en trop []) |
| fiche bouée d'une autre bouée | ⛔ refusé | appli : fiches de bouées d'une autre bouée : 1 (ex. ['a-coruna']) |
| health.json d'un autre passage | ⛔ refusé | health.json : génération différente de forecast.json |
| marque de test dans une fiche de l'appli | ⛔ refusé | données de test : 1 fichier(s) marqué(s) (ex. ['data/app/spots/lacanau.json']) |
| adresse avec identifiants dans forecast.json | ⛔ refusé | secret possible dans 1 fichier(s) (ex. ['data/forecast.json']) : refusé |
| valeur exacte d'un secret dans une page | ⛔ refusé | secret possible dans 1 fichier(s) (ex. ['spots/lacanau/index.html']) : refusé |
| génération trop ancienne | ⛔ refusé | forecast.json : généré il y a 7919.8 h (maximum 3 h) |

## Ce que le contrôle garantit, et ce qu'il ne garantit pas
- **Garanti** : site complet (pages, fiches, sitemap attendus d'après le catalogue et la configuration), cohérent (mêmes slugs et identifiants internes partout, même passage pour forecast, appli et health, séries de même longueur et d'au moins 24 h), sans marque de test ni secret connu ou typique dans aucun fichier texte.
- **Non garanti** : la justesse physique des valeurs. Une prévision fausse mais bien formée passe ; c'est le rôle des sources et de l'archive de fiabilité.

## Secrets
- `pipeline/safe.py` : `public_error()` pour tout ce qui va dans `forecast.json` et `health.json` (valeur exacte des secrets connus, `clé=valeur`, en-têtes `Authorization`, identifiants dans les adresses masqués ; paramètres d'adresse retirés ; longueur bornée). `redact()` pour les journaux : `build.py` enveloppe la sortie standard et la sortie d'erreur.
- Le contrôle reçoit la clé Météo-France (secret GitHub, masqué dans les journaux) **uniquement** pour vérifier que sa valeur n'apparaît dans aucun fichier publié.
- Tests faits avec de fausses valeurs uniquement, jamais la vraie clé.

## Limites et suite

- **Un fichier figé ne peut pas signaler sa propre panne.** Si le robot ne tourne plus du tout, `health.json` reste ancien sans rien dire. Une **surveillance externe** de l'âge de `https://houlalah.fr/health.json` (champ `generated`) est recommandée. **Non configurée** : c'est un service tiers, la décision revient au porteur (par exemple la tâche cron-job.org existante ou un service de disponibilité gratuit).
- **Alerte en cas d'échec** : GitHub envoie un e-mail quand un passage échoue, **si** les notifications « Actions » sont activées pour le compte (Settings > Notifications > Actions). Le porteur doit vérifier qu'il reçoit bien ce message : ce n'est pas testable d'ici.
- **Passage réel sur `main`** : validé sur la branche (ci-dessus) ; le premier passage de production reste à observer après la fusion. En cas de refus inattendu, la production garde la version précédente.
- **Pull request** : le job `surete` tourne aussi sur les pull requests (environ 3 min de calcul GitHub, sans appel aux API météo).
- **Archive** : seul le signalement de l'échec est ajouté. Le stockage n'est pas modifié (issue #1).
- `health.json` est publié : il ne contient ni clé ni adresse d'API (masquées), seulement l'état de la génération.
