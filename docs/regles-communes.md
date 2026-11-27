# Règles métier communes : site, application, robot (issue #4)

_27/11/2026, Claude Code, branche `regles-communes` (repère `avant-regles-communes`). Non publié._

Une même situation doit être interprétée de la même façon sur houlalah.fr, dans l'application et dans les pages générées par le robot. Ce document décrit les règles communes, les écarts trouvés, les corrections et les tests qui empêchent une nouvelle divergence.

## Les règles

### 1. Fraîcheur d'une mesure de bouée, selon la cadence de la station

| Station | « En direct » (pastille verte) | « Récente » | « Ancienne » | « Muette » |
|---|---|---|---|---|
| Houlographe CANDHIS (une mesure toutes les 30 min) | < 1 h | < 3 h | < 48 h | au-delà, ou bouée signalée muette |
| Bouée horaire (Météo-France 62001, Copernicus) | < 2 h | < 6 h | < 48 h | idem |

- **Cadence** : le robot l'écrit pour chaque bouée dans les données de l'appli (`lim`, d'après `bouees.station`). Le site et l'appli ont la même règle de repli, utilisée si `lim` est absent, par exemple dans un ancien fichier en cache : identifiant CANDHIS à 5 chiffres commençant par 0 → 1 h, sinon 2 h.
- **Horloge** : une mesure datée jusqu'à 15 min dans le futur (téléphone en retard) vaut « à l'instant ». Au-delà, l'heure est incohérente et la mesure est classée « ancienne », **jamais « en direct »**.
- **Âge** : il est recalculé à chaque affichage, y compris sur des données en cache hors connexion. L'âge de la mesure (heure de la bouée) n'est pas l'âge des prévisions (heure de génération).

### 2. Vent rapporté à l'orientation du spot

`ori` est la direction vers le large ; le vent offshore vient donc de `ori + 180°`. Soit `d` l'écart entre la direction du vent et cette direction offshore.

| Condition | Catégorie | Mot affiché |
|---|---|---|
| vitesse < 8 km/h | `lisse` | Lisse (appli : « Plan d’eau lisse ») |
| d ≤ 45° | `offshore` | Offshore |
| d ≤ 80° | `side-off` | Side-offshore |
| d ≤ 120° | `de côté` | Side-shore |
| au-delà | `onshore` | Onshore |
| vitesse, direction ou orientation absente | aucune | rien (jamais « lisse ») |

### 3. Direction en 16 secteurs

N, NNE, NE… NNO : `round(degrés / 22,5) mod 16`. C'est la direction **d'où** viennent la houle ou le vent.

### 4. Bouée de référence d'un spot

**Bouées proposées** (site : `buoyChoices` ; appli : `candidates`) :
- Gascogne, à moins de 450 km ;
- les bouées Copernicus à 300 km au plus. Celles « de côte » ne sont proposées qu'à 130 km au plus, et Donostia qu'à 80 km au plus ;
- la bouée CANDHIS la plus proche, à 130 km au plus. Une bouée abritée n'est proposée qu'à son spot : celle de Saint-Jean-de-Luz pour Sainte Barbe ;
- dans les Landes, Cap Ferret toujours, si elle est à 70 km au plus ;
- au plus 5 bouées, les plus proches, en gardant toujours la bouée de référence des Landes.
- Les distances se mesurent depuis le point de prévision du spot, pas depuis le point recalé sur la côte de la carte.

**Choix par défaut**, dans cet ordre (site : `pickBuoy` ; appli : `pickRef`) :
1. **Sur le site**, le choix fait à la main, retenu par spot.
2. **Dans les Landes** (D9) : Cap Ferret au nord, Gascogne au sud, si sa mesure a moins de 6 h. Sinon Gascogne pour le nord.
3. La plus proche **en direct selon sa cadence**, à 60 km au plus.
4. La plus proche dont la mesure a moins de 6 h.
5. Sinon la plus fraîche. Une bouée muette n'est choisie que s'il n'y a rien d'autre.

## Écarts trouvés et corrections

| # | Écart constaté | Où | Correction |
|---|---|---|---|
| 1 | « En direct » jusqu'à **2 h pour toutes les bouées**, « récente » jusqu'à 6 h : un houlographe CANDHIS de 1 h 30 clignotait en vert sur l'appli, en sable sur le site | appli : listes de bouées, carte, accueil, fiche bouée, fiche spot | règle de cadence commune (`rules.freshState`), avec la cadence `lim` écrite par le robot dans les données de l'appli |
| 2 | Mesure datée dans le futur : « en direct » sur le site (âge négatif), pas dans le robot | site, robot | tolérance d'horloge de 15 min ; au-delà, jamais « en direct » |
| 3 | Vent : **3 catégories** dans l'appli (de mer, de travers, de terre ; coupures à 60° et 120° de l'axe), **5** sur le site (45°, 80°, 120°), et pas de « plan d'eau lisse » sous 8 km/h | appli : fiche spot | même fonction et mêmes mots que le site. Exemple : un vent de 20 km/h à 60° de l'offshore donnait « de terre » dans l'appli, « side-off » sur le site |
| 4 | Vitesse du vent absente → **« Lisse »** (en JavaScript, `null < 8` est vrai) ; direction absente → une catégorie au hasard | site (`windInfo`) | donnée absente = aucune qualification |
| 5 | Bouée par défaut : le site n'appliquait pas l'étape « la plus proche en direct à 60 km » de la règle documentée (DATA_SOURCES.md) | site (`pickBuoy`) | étape ajoutée, avec « en direct » selon la cadence. Seul effet : une bouée en direct à 60 km au plus est préférée à une bouée plus proche mais seulement « récente ». Exemple : Grande Plage, Anglet à 1 h 30 et Pasaia en direct → Pasaia. Avec Anglet en direct, rien ne change. |
| 6 | Bouée par défaut dans l'appli : pas les mêmes bouées proposées (toutes à moins de 130 km, Gascogne seulement dans les Landes), la plus proche au lieu de la plus fraîche en dernier recours, distances mesurées depuis le point affiché et avec une formule approchée | appli : fiche spot, « Autour de mon spot » | mêmes bouées proposées et même choix que le site (`rules.candidates` + `rules.pickRef`) ; point de prévision exporté par le robot (`pt`), même formule de distance |
| 7 | « Autour de mon spot » ne choisissait que parmi les bouées côtières à moins de 120 km | appli : onglet Bouées | bouée de référence commune |
| 8 | « à l'instant » jusqu'à 59 min | appli | comme le site : « à l'instant » sous 12 min, puis les minutes |
| 9 | Âges et pastilles figés tant que l'écran ne bouge pas ; données pas redemandées au retour au premier plan | appli | âges et états recalculés chaque minute et au retour au premier plan ; données redemandées à ce moment-là (reprise réseau) |
| 10 | Fiche bouée de l'appli : la prévision était filtrée en comparant des **heures écrites** (contrat horaire #2) : erreur d'une heure pour une bouée portugaise | robot (`appdata`) | comparaison en instants |

Il n'y a **aucun changement visuel**. Seuls quelques mots changent dans l'appli : la catégorie du vent, et « il y a 25 min » au lieu de « à l'instant ».

## Écarts connus, non corrigés dans ce lot

| Écart | Pourquoi il reste | Proposition |
|---|---|---|
| **Pages de spots générées** : leur ligne « Bouée de référence / la plus proche » suit une règle simplifiée. Elle prend la référence des Landes, sinon la bouée côtière la plus proche à 80 km au plus, sans tenir compte de l'âge, car la page est statique | ces pages font partie du lot SEO, sur lequel ChatGPT travaille en parallèle | ticket séparé : appliquer `candidates` et `pickRef` dans le robot, à l'heure de génération |
| **Valeurs « maintenant » de l'index de l'appli** : elles sont calculées à l'heure de la génération. Hors connexion, avec un index de plusieurs heures, l'accueil et la carte montrent la prévision de cette heure-là. L'appli affiche « hors connexion » et « Mis à jour il y a X h » | exporter une courte série par spot alourdirait l'index ; à coordonner avec #6 et #8 | quelques heures par spot dans l'index, ou recalcul depuis la fiche du spot |
| **Période à la bouée Gascogne** : l'appli montre la période moyenne mesurée (« 8 s moy. »), le site la période estimée du modèle (« ≈ X s période estimée ») | choix d'affichage antérieur, documenté dans CLAUDE.md | à trancher par le porteur, si l'on veut un seul affichage |
| **Fiche d'un spot en cache depuis plus de 7 jours** : « maintenant » se cale sur la dernière heure disponible | cas extrême hors connexion | message « prévision trop ancienne » |
| **Choix de bouée fait à la main** : retenu par spot sur le site ; l'appli n'a pas ce choix | différence de fonctionnalité, pas de règle | — |

## Tests communs : mêmes cas, trois implémentations

`tests/regles_communes.json` contient les cas, avec des attendus écrits à la main d'après les règles ci-dessus :
- **fraîcheur** : 17 cas, dont chaque seuil 1 h, 3 h, 2 h, 6 h et 48 h, la cadence du robot, l'horloge en retard et l'horloge en avance ;
- **vent** : 16 cas, dont chaque seuil, le passage par le nord et les données absentes ;
- **secteurs** : 9 cas ;
- **choix de bouée** : 16 scénarios avec les vraies positions des spots et des stations, dont :
  - Landes nord et sud, Sainte-Barbe et Hendaye ;
  - Portugal ;
  - bouée muette, bouée sans hauteur, tout ancien, aucune bouée.

| Implémentation | Test | Lancé par |
|---|---|---|
| Site : fonctions **extraites telles quelles** de `web/index.html` | `node tests/regles_site.test.js` | CI, job `surete` |
| Appli : `app/src/rules.ts`, sans dépendance, utilisé par `data.ts` et les écrans | `node tests/regles_app.test.mjs` | CI |
| Robot : `bouees.fresh_state`, `seo.wind_for_spot`, `seo.sector`, cadence `station`, référence des Landes, données écrites pour l'appli | `python -m tests.test_regles` | CI |
| Données réelles de l'appli (`lim`, `kind`, `pt`) | `python -m tests.test_offline` | CI |

**Preuve que le test détecte les écarts** : joué sur la version du site d'avant ce lot (`REGLES_HTML=… node tests/regles_site.test.js`), il échoue sur 5 cas :
- l'horloge en avance ;
- les trois données de vent absentes ;
- Anglet récente face à Pasaia en direct.

**Vérifié dans le navigateur** avec les données réelles de houlalah.fr :
- **Site** : aucune erreur. Les bouées par défaut sont celles attendues : Cap Ferret pour Lacanau et Biscarrosse, Anglet pour la Grande Plage et Hendaye, Saint-Jean-de-Luz pour Sainte Barbe, Gascogne pour La Gravière, Nazaré pour Supertubos.
- **Appli** (aperçu web) : « Bouées en direct » selon la cadence de chaque station. Sur la fiche de la Grande Plage, « Plan d’eau lisse » à 5 km/h, comme le site (« Lisse »), et la bouée Anglet à 7 km, la même que sur le site.

## Pour changer une règle

1. Modifier `app/src/rules.ts`, la fonction correspondante de `web/index.html` et, s'il y a lieu, le robot.
2. Mettre à jour les attendus de `tests/regles_communes.json`.
3. Les trois tests doivent passer. Un seul qui diverge fait échouer la CI.
