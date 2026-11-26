# SEO

## Stratégie

- **Une page forte par entité réelle** : spot (`/spots/x/`), bouée (`/bouees/x/`), région (`/meteo-surf-x/`). **Pas de pages par variante de mot-clé**, pas de texte de remplissage, pas de contenu caché pour les robots.
- **Valeur réelle et différenciante** : les mesures des bouées (fraîcheur honnête, historique, comparaison avec la prévision) et des données utiles (heure par heure, marées, orientation du vent pour chaque spot).
- **Requêtes visées** :

| Requête | Page |
|---|---|
| « météo surf / prévisions surf / houle [spot] » | `/spots/[spot]/` |
| « bouée / houlographe / bouée en direct [lieu] » | `/bouees/[lieu]/` |
| « météo surf [région] » | `/meteo-surf-[région]/` |

- **Vocabulaire exact** : « houlographe » pour les 7 stations CANDHIS, numéros officiels de station, sources citées.

## Technique en place

- **Génération** : `pipeline/seo.py`, `bouees.py` et `zones.py` génèrent les pages à chaque passage du robot (fichiers ignorés par git). Sitemap de 255 URL, `robots.txt` ouvert (moteurs IA compris), `llms.txt`.
- **Balises** : titles ≤ 60 caractères et descriptions ≤ 160, uniques (vérifiés par `tests/test_offline.py`) ; canoniques auto-référentes ; un seul H1 par page.
- **Données structurées** : Organization, WebPage, BreadcrumbList, CollectionPage, `Place` avec coordonnées pour les spots, `Dataset` pour les bouées.
- **Canoniques des adresses `/?spot=x`** : vers `/spots/x/` (voir [DECISIONS.md](DECISIONS.md) D20).
- **Accueil** : la page d'un spot n'est plus construite derrière la carte (un seul H1). L'accueil a des liens HTML vers les spots, les bouées et les régions.
- **Adresse publique** : `config.SITE_URL` (variable `METEO_SITE_URL` du workflow). DNS et domaine sont réglés à la main par le porteur.

## Historique des audits et actions

| Date | Document | Contenu |
|---|---|---|
| 26/11/2026 | [audit-seo-2026-11-26.md](audit-seo-2026-11-26.md) | Audit technique complet : 255 pages explorées, rendu JavaScript, ressemblance entre pages, performances |
| 26/11/2026 | [seo-corrections-2026-11-26.md](seo-corrections-2026-11-26.md) | Premier lot (publié le 26/11) : changements, comparaison avant / après, maillage, canoniques, groupes de spots, internationalisation |
| 26/11/2026 | [seo-suivi-search-console.md](seo-suivi-search-console.md) | Quoi suivre dans Search Console, quand, et les signaux d'alerte |

**Point de départ** (Search Console, 26/11) : 204 pages indexées ; 66 non indexées (33 détectées, 17 explorées, 15 alternatives avec canonique, 1 redirection) ; 831 impressions sur 7 jours ; 307 requêtes ; position moyenne 31,4 ; 0 clic.

## Problèmes ouverts

1. **Pages non indexées** : 66. Hypothèse forte : les 21 groupes de spots à prévision partagée et la jeunesse du site. Il faut l'export de Search Console pour trancher.
2. **Poids** : `forecast.json` pèse 6,5 Mo (performances de l'accueil et de l'application web).
3. **Accueil sans JavaScript** : peu de texte (le rendu avec JavaScript est correct).
4. **Bing Webmaster Tools** : à déclarer (action du porteur).

## Opportunités

- **Pages de bouées** : fiabilité chiffrée (écart prévu / mesuré), historique mensuel et records, à partir de l'archive ([archives-bouees-potentiel.md](archives-bouees-potentiel.md)).
- **Maillage** : « bouées de la zone » sur les pages de spots.
- **Internationalisation** :
  - quoi : `/es/`, `/pt/`, `/en/`, générés par le même robot, gabarits traduits par une personne, `hreflang` réciproques ;
  - dans quel ordre : espagnol (Pays basque espagnol, Cantabrie, Asturies, Galice), puis portugais, puis anglais ;
  - à quelle condition : commencer par la langue qui a déjà des impressions dans Search Console.
