# Corrections SEO — premier lot (branche `seo-corrections`, environnement de test)

Rien n'est publié. Repère pour revenir en arrière : tag `avant-seo-corrections`.
Audit de départ : `docs/audit-seo-2026-11-26.md`.

## 1. Ce qui a changé

### 1.1 Accueil : Lacanau n'est plus le contenu de la page `/` — `web/index.html`

- **Avant** : au démarrage, le site construisait la page du premier spot (Lacanau) derrière la carte. Après exécution du JavaScript, Google voyait sur l'accueil le H1 « Météo surf Lacanau » et toute la prévision de ce spot.
- **Après** : quand l'accueil s'affiche, la page d'un spot n'est construite qu'au moment où on la quitte (bouton d'un spot, retour à la prévision). Rien ne change pour le visiteur.
- **Vérifié après rendu** (téléphone simulé) :
  - un seul H1 : « La houle prévue, vérifiée par les bouées. » ;
  - plus aucune mention de Lacanau ;
  - même title, même canonique (`/`) ;
  - le parcours accueil → spot → retour fonctionne, et les 214 spots s'ouvrent.
- **HTML initial** (sans JavaScript) : inchangé. On y trouve le title, la description, le bloc `<noscript>` avec son H1 et les liens vers les 12 régions.
- **Liens explorables** : le panneau de l'accueil a maintenant une rubrique repliable « Spots, bouées et régions », avec de vrais liens `<a href>` vers `/spots/`, `/bouees/`, les 12 régions, « Comment ça marche » et « À propos ». Sur téléphone, le menu ☰ contient les mêmes liens. Aucun texte caché : c'est une vraie navigation, utile aux visiteurs.

### 1.2 Fraîcheur des bouées selon la cadence de chaque station — `web/index.html`, `pipeline/bouees.py`

La règle est la même partout : carte de l'accueil, liste du panneau, page de prévisions, pages de bouées et titres Google.

| Station | Cadence | « En direct » | « Récente » | « Ancienne » | « Muette » |
|---|---|---|---|---|---|
| Houlographes CANDHIS (7) | 30 min | < 1 h | < 3 h | < 48 h | au-delà |
| Météo-France 62001 et bouées Copernicus (15) | horaire, publiée avec 30 à 60 min de retard | < 2 h | < 6 h | < 48 h | au-delà |

- **Pastille verte animée** : seulement pour « en direct ».
- **Titre Google** :
  - « houle (mesurée) en direct » tant que la station publie normalement (mesure de moins de 6 h, ou statut « en direct » ou « récente ») ;
  - « dernières mesures » au-delà.
- **Station qui ne publie plus** : un encadré indique la date de la dernière mesure, par exemple « Pas de mesure transmise depuis le 18/11 à 0 h 30 ». Il propose les 3 bouées à jour les plus proches. La page reste indexée : la requête existe, et l'historique et les records restent utiles.
- **État au moment du test** (données de 19 h 32) :
  - « dernières mesures » : Anglet (9 jours), Cabo Silleiro (5 jours), Île de Batz (10 h), Belle-Île (23 h), Leixões (11 h) ;
  - les 17 autres stations restent « en direct ».

### 1.3 Pages de bouées : le vocabulaire réellement recherché, exact — `pipeline/bouees.py`

- **Houlographes CANDHIS** : les 7 stations (Cap Ferret 03302, Anglet 06402, Saint-Jean-de-Luz 06403, Plateau du Four 04403, Les Pierres Noires 02911, Île de Batz 02922, Belle-Île 05602) sont nommées par leur vrai nom.
  - title : « Bouée houlographe Cap Ferret : houle en direct | Houlalah »
  - H1 : « Bouée houlographe du Cap Ferret »
  - sous-titre : « Houlographe du réseau CANDHIS (Cerema) · station 03302 · une mesure toutes les 30 minutes »
- **Identifiant officiel affiché sur les 22 pages** :
  - CANDHIS avec son numéro ;
  - « Météo-France 62001 » ;
  - « plateforme Copernicus 6200024 », etc.
- **Source citée en bas de page** : exploitant quand il est documenté dans le code (Puertos del Estado pour Bilbao-Vizcaya, Euskalmet pour Donostia), licence, cadence, et la mention « mesures en temps réel, non validées ». Les houlographes renvoient à leur page officielle CANDHIS. Aucun exploitant n'est cité s'il n'est pas documenté.
- **Intertitres** : « Dernière mesure de houle », « Historique de la hauteur de houle (48 h) », « Historique des mesures ».
- **Description Google** : « Hauteur de houle mesurée en direct par la bouée houlographe Cap Ferret (CANDHIS 03302) : … Historique 48 h, records et spots voisins. »
- **Données structurées `Dataset`** sur les 22 pages : créateur, licence, coordonnées, période couverte et variables mesurées. Aucune note ni avis.
- **Maillage** : les liens « Spots autour de la bouée » mènent maintenant aux **pages de spots** (`/spots/x/`, indexables), et non plus à l'application (`/?spot=x`, dont la canonique est l'accueil).
- **Liste des bouées** : « Houlographe » devant les stations CANDHIS.

### 1.4 Pages de spots : la journée et les marées, en clair — `pipeline/seo.py`

- **« Heure par heure aujourd'hui »** (le lendemain après 19 h) : toutes les 3 h, de 6 h à 21 h, avec la houle, la période et la direction, le vent et les rafales. S'y ajoute une colonne **« Pour ce spot »** : le vent rapporté à l'orientation propre du spot (offshore, side-offshore, side-shore, onshore), calculé avec exactement la règle du site.
- **« Marées à … »** : pleines et basses mers de la semaine (heure, hauteur, coefficient), calculées pour le port de référence du spot, décalage du spot compris. Ce port est indiqué sous le tableau.
- **Tableaux visibles par tous** : même style que le tableau de la semaine existant, et un lien vers la prévision complète.
- **Aucune valeur modifiée ni inventée** : tout vient des prévisions et des marées déjà calculées par le robot.

### 1.5 Tests du robot — `tests/test_offline.py`

Le test des pages de bouées vérifie maintenant :
- le H1 houlographe, le numéro CANDHIS, la source et le `Dataset` ;
- que les liens vers les spots ne passent plus par `?spot=` ;
- la présence de « Heure par heure » et des marées sur les pages de spots.

Tout est vert, avec titres ≤ 60 caractères et descriptions ≤ 160 caractères sur les 255 pages.

## 2. Audit comparatif avant / après

Même exploration (255 URL du sitemap, HTML brut) sur la production et sur la version de test locale.

| Indicateur | Avant (production) | Après (test) |
|---|---|---|
| Accueil après rendu : H1 | « Météo surf Lacanau » (+ H1 de l'accueil masqué) | « La houle prévue, vérifiée par les bouées. » seul |
| Accueil après rendu : contenu Lacanau | toute la prévision | aucun |
| Pages de spots : mots (médiane) | 338 | 646 (données réelles seulement) |
| Pages de spots avec heure par heure | 0 | 214 |
| Pages de spots avec marées | 0 | 139 (les spots d'Espagne et du Portugal n'ont pas encore de port de marée) |
| Liens entrants vers une page de spot (médiane) | 8 | 9 |
| Liens bouée → page de spot indexable | 0 (tout passait par `?spot=`) | 8 par bouée |
| Titres de bouées avec « houlographe » | 0 | 7 (les 7 CANDHIS) |
| Pages de bouées avec identifiant officiel et source | 1 | 22 |
| Pages de bouées avec `Dataset` | 0 | 22 |
| Titres « en direct » sur une station muette ou en retard | Anglet (9 jours), Cabo Silleiro, Île de Batz, Belle-Île, Leixões | aucun |
| Titres uniques / descriptions uniques / canoniques auto-référentes | oui / oui / 255 | oui / oui / 255 |
| Titre max / description max | 60 / 155 | 60 / 155 |
| Pages de spots : poids | 4 Ko compressés | ≈ 6 Ko compressés (LCP local 0,7 s) |

## 3. Maillage interne : état des lieux

| Lien | État | Remarque |
|---|---|---|
| Bouée → spots associés | **corrigé** : 8 liens vers `/spots/x/` | avant : vers l'application |
| Spot → bouée de référence | en place | même règle que le site (`config.ref_buoy`) ; dans les Landes, la bouée de référence est parfois Gascogne, à plus de 300 km |
| Spot → spots voisins | en place : 6 voisins | |
| Région → spots et bouées | en place | tableau des spots et bouées de la zone |
| Accueil → contenus | **corrigé** : liens HTML vers spots, bouées, régions et pages | avant : seulement les régions dans `<noscript>` et l'application |
| Carte de l'accueil → spot | événement JavaScript (normal pour une carte) | les vraies pages sont atteignables par les liens ci-dessus et le sitemap |

**Piste suivante** : « Bouées de la zone » sur les pages de spots. Aujourd'hui, une page de spot ne cite qu'une bouée. Lister les 2 ou 3 bouées à jour les plus proches renforcerait le lien spot ↔ bouée, qui fait notre différence. Rien n'est encore fait.

## 4. URL `/?spot=` : analyse (rien n'a été changé)

- **Ce qu'elles sont** : la même page `index.html` pour tous les spots, l'état « application ouverte sur tel spot ». L'adresse est écrite par le site (`history.replaceState`). Les pages de spots y renvoient par « Voir les prévisions heure par heure ».
- **Canonique actuelle** : `https://houlalah.fr/` en dur dans `index.html`. Google les classe donc en « page alternative avec balise canonique correcte » (vos 15 pages).
- **Ce qui change avec ce lot** : l'accueil ne contient plus de prévision de spot. Une page `/?spot=x` (prévision d'un spot) qui désigne l'accueil (carte) comme page de référence devient donc un signal **incohérent** : le contenu n'est pas le même. Google pourrait ignorer cette canonique et choisir la sienne.
- **URL de référence proposée**, par type de contenu :

| Contenu | URL de référence |
|---|---|
| Accueil (carte) | `/` |
| Prévision d'un spot (texte, 7 jours, heure par heure, marées) | `/spots/x/` |
| Application ouverte sur un spot | `/?spot=x` → canonique vers `/spots/x/` |
| Région | `/meteo-surf-x/` |
| Bouée | `/bouees/x/` |

- **Mise en œuvre proposée, à valider** :
  1. retirer la canonique en dur de `index.html` ;
  2. la poser en JavaScript selon l'état : `/` sur l'accueil, `/spots/x/` pour `?spot=x`.

  Alternative plus prudente : garder `/` et ajouter `noindex` sur les états `?spot=` (ils ne seraient alors jamais indexés).
- **Incertitude** : Google lit la canonique du rendu JavaScript, mais recommande qu'elle ne contredise pas le HTML initial, d'où l'étape 1. À vérifier dans Search Console (« Inspection de l'URL » → « URL canonique sélectionnée par Google ») sur 2 ou 3 de ces URL **avant** de choisir.

## 5. Les 53 spots à prévision partagée : stratégie (en attente de votre export)

21 groupes de spots (53 pages) utilisent le même point des modèles : houle et vent identiques. Les valeurs n'ont **pas** été modifiées et ne le seront pas.

**Ce qui est réellement propre à chaque spot** (données existantes, `pipeline/spots.json` et robot) :

| Donnée propre | Groupes où elle diffère |
|---|---|
| Orientation (donc lecture du vent : offshore ou onshore) | 15 groupes sur 21 |
| Type de vague, fond, niveau, marée conseillée, tailles de fonctionnement | 6 groupes |
| Port de marée | 1 groupe |
| Commune, coordonnées, voisins, distance aux bouées | tous |
| Aucune différence dans la fiche (Messanges / Vieux Boucau, Les Casernes / Le Penon, L'Océan / La Madrague, Ribeira d'Ilhas / Coxos / São Lourenço) | 4 groupes |

**Déjà fait dans ce lot, pour tous les spots** : la colonne « Pour ce spot » (vent rapporté à l'orientation) et les marées. Les pages d'un même groupe diffèrent donc maintenant dès que leur orientation donne une lecture du vent différente.

**Proposé, après votre export** :
1. **Croiser** la liste des URL non indexées (« explorées » et « détectées ») avec ces 21 groupes, et regarder dans « Inspection de l'URL » la canonique choisie par Google pour 2 ou 3 d'entre elles.
2. **Si ce sont bien ces pages** : ajouter une ligne factuelle « Même prévision au large que La Centrale et La Sud : ce qui change ici, c'est l'orientation (face au NO), le fond (sable) et la marée conseillée », avec des liens entre les pages du groupe (maillage et honnêteté).
3. **Pour les 4 groupes sans aucune différence dans nos fiches** : enrichir les fiches sur le terrain ou à partir de sources vérifiables (niveau, dangers, accès). Sinon, accepter que Google n'en indexe qu'une partie. Pas de fusion d'URL, pas de texte de remplissage.

## 6. Opportunités

### Bouées (votre porte d'entrée naturelle)

- **Archive des mesures** (branche `history`, depuis le 09/11) : avec plusieurs mois d'historique, des pages de bouées avec « houle moyenne de novembre », « plus grosse houle mesurée » et « jours au-dessus de 2 m ». C'est de la vraie donnée, rare, et cela répond à « historique bouée Anglet ».
- **Écart prévision / mesure par bouée** (`pipeline/history.py`) : afficher sur chaque page de bouée l'écart moyen entre notre prévision et la mesure. C'est la promesse « vérifiée par les bouées », chiffrée.
- **API CANDHIS officielle** (jeton sur demande au Cerema) : plus fiable que la lecture des pages publiques, avec possiblement la profondeur et le type exact de houlographe, à afficher seulement si c'est fourni.

### Maillage géographique

- Bouées de la zone sur les pages de spots (section 3).
- Sur les pages régionales, une ligne « Bouées en direct de la zone » avec leur état de fraîcheur (déjà en partie présente).

### Internationalisation (moyen terme)

- **Pourquoi** : la moitié des spots sont en Espagne et au Portugal, et les bouées espagnoles et portugaises sont recherchées dans leur langue (« boya Bilbao », « boia Leixões », « previsão surf Peniche »). Les surfeurs étrangers en France cherchent en anglais (« Hossegor surf forecast »).
- **Comment, sans multiplier des pages vides** :
  - des sous-dossiers `/es/`, `/pt/`, `/en/` générés par le même robot, avec les mêmes données ;
  - des gabarits traduits par une personne (pas de traduction automatique en masse) ;
  - des balises `hreflang` réciproques et `x-default` vers le français.
- **Ordre conseillé** :
  1. **espagnol** : spots du Pays basque espagnol, de Cantabrie, des Asturies et de Galice, plus leurs bouées ;
  2. **portugais** : spots et bouées du Portugal ;
  3. **anglais** : spots les plus connus et toutes les bouées.
- **Vocabulaire à respecter** : « boya », « oleaje », « previsión de surf » ; « boia », « ondulação », « previsão de surf » ; « buoy », « swell », « surf forecast ».
- **Préalable** : regarder dans Search Console la répartition des impressions par pays. Commencer par la langue qui en a déjà.

## 7. Incertitudes restantes

- **Cause des 66 pages non indexées** : hypothèse forte (spots à prévision partagée, site jeune), non prouvée sans l'export de Search Console.
- **Effet des nouveaux titres de bouées** : Google réécrit parfois les titres. Il faut suivre les impressions et le taux de clic par requête (« houlographe … », « bouée … ») 2 à 4 semaines après publication.
- **Marées** : absentes pour 75 spots d'Espagne et du Portugal (pas de port de marée calculé). Rien n'est affiché plutôt qu'une valeur approximative.
- **Seuils de fraîcheur** : ils reposent sur la cadence connue des sources (CANDHIS 30 min, horaire pour Météo-France et Copernicus). Une station qui change de rythme (Leixões, Sines et Faro publient de façon irrégulière) peut passer de « en direct » à « récente » plus souvent.
- **Accueil sur téléphone** : le H1 y est en texte réservé aux lecteurs d'écran (le titre visible est le logo). C'est accepté par Google, mais un H1 visible serait plus fort ; à arbitrer avec le design.
- **Canonique `/?spot=`** : décision à prendre (section 4).

## 8. Pour publier ce lot (après votre accord)

1. **Relire** : l'aperçu (accueil, une page de bouée muette comme `/bouees/anglet/`, une page de spot comme `/spots/la-graviere/`).
2. **Publier** : avancer `main` sur la branche `seo-corrections` (avance simple, sans conflit), après un « Oui, publie ».
3. **Dans Search Console** :
   - « Inspection de l'URL » puis « Demander l'indexation » pour `/`, 3 pages de bouées et 3 pages de spots ;
   - suivre l'onglet « Pages » 2 à 4 semaines après.
