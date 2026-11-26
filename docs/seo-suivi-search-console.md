# Suivi du lot SEO dans Search Console

À utiliser après la publication de la branche `seo-corrections`. Notez la **date de mise en ligne**, qui sert de point de comparaison.

## 1. Le jour de la publication

1. **Demander une indexation prioritaire** : dans « Inspection de l'URL », coller l'adresse puis cliquer sur « Demander l'indexation », pour :
   - `https://houlalah.fr/`
   - `https://houlalah.fr/bouees/anglet/`, `/bouees/cap-ferret/`, `/bouees/les-pierres-noires/`, `/bouees/plateau-du-four/`
   - `https://houlalah.fr/spots/la-graviere/`, `/spots/lacanau/`, `/spots/la-nord/`
2. **Vérifier la canonique** : sur `https://houlalah.fr/?spot=lacanau`, regarder « Inspection de l'URL » → « Indexation de la page » → « URL canonique déclarée par l'utilisateur ». Elle doit indiquer `https://houlalah.fr/spots/lacanau/` après le nouveau passage de Google.
3. **Sitemap** : rien à changer, les adresses sont les mêmes. Le sitemap peut être renvoyé dans « Sitemaps » pour accélérer la nouvelle exploration.

## 2. Ce qu'on attend, et comment le mesurer

| Changement | Effet attendu | Où le voir | Délai |
|---|---|---|---|
| « Bouée houlographe » + numéro CANDHIS (7 pages) | apparition sur « houlographe [lieu] », « candhis [lieu] » ; meilleure position sur « bouée [lieu] » | **Performances** → filtre Requête *contient* « houlographe », puis « bouée » ; comparer 28 jours avant / après | 2 à 6 semaines |
| Titre honnête des bouées muettes (« dernières mesures ») | moins de déception, CTR plus juste ; la page reste indexée | Performances → Pages : `/bouees/anglet/` | 2 à 4 semaines |
| Accueil sans contenu de Lacanau, un seul H1 | l'accueil se positionne sur « météo surf atlantique », « prévisions surf » plutôt que sur Lacanau ; `/spots/lacanau/` ne lui fait plus concurrence | Performances → Pages : `/` et `/spots/lacanau/`, requêtes de chacune | 2 à 6 semaines |
| Canonique de `/?spot=x` vers `/spots/x/` | les 15 « pages alternatives » restent exclues, mais leurs signaux vont à la page du spot | **Pages** → « Page alternative avec balise canonique correcte » (le nombre peut rester stable, c'est normal) ; Inspection de l'URL | 2 à 4 semaines |
| Heure par heure et marées sur les 214 pages de spots | plus d'impressions sur « houle [spot] aujourd'hui », « marée [spot] », « prévisions surf [spot] » ; moins de pages « explorées, non indexées » | Performances → filtre Requête *contient* « marée », « houle » ; **Pages** → onglet « Non indexées » | 3 à 8 semaines |
| Liens bouée → pages de spots | meilleure exploration des spots proches des bouées | **Pages** → « Détectée, actuellement non indexée » (le nombre devrait baisser) | 3 à 8 semaines |
| `Dataset` sur les pages de bouées | éligibilité à Google Dataset Search ; aucun effet direct sur le classement | **Améliorations** (si Google affiche un rapport Dataset) ; test des résultats enrichis sur une page de bouée | 2 à 6 semaines |

## 3. Tableau de bord simple (toutes les deux semaines)

| Date | Impressions 7 j | Clics 7 j | Position moyenne | Pages indexées | Non indexées | « houlographe » (impressions) | « bouée » (impressions) |
|---|---|---|---|---|---|---|---|
| 26/11/2026 (avant) | 831 | 0 | 31,4 | 204 | 66 | — | — |
| | | | | | | | |

**Comment remplir**
- **Impressions, clics et position** : Performances → 7 derniers jours.
- **Pages indexées et non indexées** : onglet Pages.
- **Mots-clés** : Performances → filtre de requête.

## 4. À exporter pour la suite

- Onglet **Pages** → « Explorée, actuellement non indexée » et « Détectée, actuellement non indexée » → Exporter. Cette liste permettra de traiter les 21 groupes de spots à prévision identique (`docs/seo-corrections-2026-11-26.md`, section 5).
- **Performances** → Requêtes → Exporter (28 jours), pour voir quels termes de bouées et de spots progressent.

## 5. Ce qui serait un signal d'alerte

- **Chute des pages indexées** de plus de 10 % : vérifier les canoniques (Inspection de l'URL) et le sitemap.
- **Pages de bouées qui disparaissent** des résultats sur « bouée [lieu] » : vérifier les titres réécrits par Google dans Performances (colonne Pages).
- **Accueil remplacé** par une page de spot sur « météo surf » : vérifier le rendu de l'accueil (Inspection de l'URL → « Tester l'URL en direct » → capture d'écran et HTML rendu).
