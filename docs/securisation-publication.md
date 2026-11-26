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
| `pipeline/build.py` | Nouveau `health.json` : heure de génération, nombre de spots, erreurs (adresses et clés masquées), âge de chaque bouée. **Aucun secret** |
| `tools/check_site.py` | **Contrôle avant publication** (voir ci-dessous). Code de sortie 1 = publication refusée |
| `.github/workflows/update.yml` | Le robot génère dans `_site/` (copie de `web/`), le contrôle passe, puis seul `_site/` est envoyé. Déploiement et archive **uniquement depuis `main`**. Échec d'archive signalé (annotation + résumé). File d'attente par branche : un essai sur une branche n'annule jamais un passage de production |

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

## Preuves

1. `python -m tests.test_offline` : vert. Il affirme lui-même : `isolation OK : rien écrit dans web/, site de test refusé par le contrôle (5 motifs)`. Les dates de modification de `web/data/forecast.json`, `web/data/app/index.json` et `web/sitemap.xml` sont inchangées.
2. Sur le site produit par le test, le contrôle compte : 214 spots catalogue = 214 forecast = 214 appli, 22 pages bouées, 254 pages attendues, 255 adresses dans le sitemap (les 254 et l'accueil). Il refuse pour les marques de test.
3. **Simulations de pannes** (`tests/simulate_pannes.py`) : à partir de ce site, marques de test retirées, chaque scénario est rejoué sur une copie. Les résultats sont au tableau ci-dessous.

| Scénario | Résultat | Motif |
|---|---|---|
| site de référence (marques de test retirées) | ✅ publié |  |
| panne d'une source (CANDHIS) : tolérée | ✅ publié |  |
| données de test dans forecast.json | ⛔ refusé | forecast.json : données de test (meta._test) |
| une page de test oubliée | ⛔ refusé | pages de test (marque houlalah-test) : 1 (ex. ['spots/lacanau']) |
| échec des données de l'appli (exception) | ⛔ refusé | robot : appdata — KeyError: 'marine' |
| échec des pages bouées (exception) | ⛔ refusé | robot : seo_bouees — ValueError |
| échec SEO complet (exception) | ⛔ refusé | robot : seo — OSError |
| pages bouées absentes | ⛔ refusé | pages absentes : 23 (ex. ['bouees', 'bouees/a-coruna', 'bouees/anglet', 'bouees/belle-ile']) |
| une page de spot absente | ⛔ refusé | pages absentes : 1 (ex. ['spots/lacanau']) |
| une fiche spot de l'appli absente | ⛔ refusé | appli fiche spot lacanau absent (lacanau.json) |
| une fiche bouée de l'appli absente | ⛔ refusé | appli fiche bouée a-coruna absent (a-coruna.json) |
| index de l'appli : JSON tronqué | ⛔ refusé | appli index.json : JSON invalide (Unterminated string starting at: line 1 column 8 (char 7)) |
| forecast.json absent | ⛔ refusé | forecast.json absent (forecast.json) |
| un spot manquant dans forecast.json | ⛔ refusé | forecast.json : spots différents du catalogue (manquants ['martinhal'], en trop []) |
| appli d'une autre génération | ⛔ refusé | appli : génération différente de forecast.json |
| sitemap avec adresse locale | ⛔ refusé | sitemap : 1 adresse(s) en trop, 0 manquante(s) |
| sitemap absent | ⛔ refusé | sitemap.xml absent |
| canonique fausse | ⛔ refusé | canoniques incorrectes : 1 (ex. ['spots/lacanau']) |
| page en trop (reste d'un ancien spot) | ⛔ refusé | pages inattendues : 1 (ex. ['spots/ancien']) |
| secret dans health.json | ⛔ refusé | health.json : ressemble à un secret (refusé) |
| index.html du site absent | ⛔ refusé | index.html absent |
| génération trop ancienne | ⛔ refusé | forecast.json : généré il y a 7919.4 h (maximum 3 h) |

**22/22 scénarios conformes.** Panne réelle de bout en bout (`tests/panne_bout_en_bout.py`) : le test rejoué avec `appdata.generate` et `bouees.generate` qui lèvent une exception → `forecast.json` et `health.json` contiennent `appdata` et `seo_bouees`, le contrôle refuse (index de l'appli absent, 23 pages bouées absentes, sitemap incomplet). Scripts : `python tests/simulate_pannes.py <sortie du test> .` et `python tests/panne_bout_en_bout.py .`

## Limites et suite

- **Un fichier figé ne peut pas signaler sa propre panne.** Si le robot ne tourne plus du tout, `health.json` reste ancien sans rien dire. Une **surveillance externe** de l'âge de `https://houlalah.fr/health.json` (champ `generated`) est recommandée. **Non configurée** : c'est un service tiers, la décision revient au porteur (par exemple la tâche cron-job.org existante ou un service de disponibilité gratuit).
- **Alerte en cas d'échec** : GitHub envoie un e-mail quand un passage échoue, **si** les notifications « Actions » sont activées pour le compte (Settings > Notifications > Actions). Le porteur doit vérifier qu'il reçoit bien ce message : ce n'est pas testable d'ici.
- **Premier vrai passage** : le contrôle n'a pas encore tourné sur une vraie génération GitHub. Si un motif inattendu le fait échouer, la production reste simplement sur la version précédente : on corrige alors le contrôle.
- **Archive** : seul le signalement de l'échec est ajouté. Le stockage n'est pas modifié (issue #1).
- `health.json` est publié : il ne contient ni clé ni adresse d'API (masquées), seulement l'état de la génération.
