# Quotas, cache et licences (issue #7)

_27/11/2026, Claude Code, branche `quotas-cache` (repère `avant-quotas-cache`). Non publié._

> Ce document est une **analyse technique**, pas un avis juridique. Les conditions des fournisseurs peuvent changer : les liens et la date de lecture sont donnés pour chaque point. Toute monétisation demande une validation des conditions par le porteur, idéalement avec un professionnel.

## 1. Consommation mesurée avant ce lot

### Rythme du robot (API GitHub Actions, 20 au 26/11/2026)

| Jour | Passages | Réussis | Annulés | Échecs | Origine |
|---|---|---|---|---|---|
| 20/11 | 57 | 51 | 6 | 0 | 48 cron-job.org, 9 programmés |
| 21/11 | 58 | 45 | 11 | 2 | 48 cron-job.org, 10 programmés |
| 22/11 | 56 | 49 | 7 | 0 | 48 cron-job.org, 8 programmés |
| 23/11 | 58 | 52 | 6 | 0 | 48 cron-job.org, 8 programmés, 2 push |
| 24/11 | 55 | 50 | 5 | 0 | 48 cron-job.org, 7 programmés |
| 25/11 | 61 | 54 | 6 | 1 | 47 cron-job.org, 6 programmés, 8 push |
| 26/11 | 63 | 55 | 8 | 0 | 49 cron-job.org, 8 programmés, 4 push, 2 PR |

En moyenne, **56 passages par jour**, de 7,4 min en médiane. Un passage annulé (`concurrency`) a pu envoyer une partie de ses requêtes.

### Requêtes Open-Meteo d'un passage (lues dans le code de `main`)

| Requête | Nombre | Points | Variables | Fréquence |
|---|---|---|---|---|
| Mer « best match » (vagues, houles, niveau, eau) | 1 | 176 | 14 | chaque passage |
| Vagues par modèle (MFWAM, EWAM, ECMWF WAM, GFS-Wave) | 4 | 176 | 3 | chaque passage |
| Vent 4 modèles + lever et coucher du soleil | 1 | 177 | 20 (5 × 4 modèles) | chaque passage |
| Prévision au point des bouées (14 du large + Gascogne) | 15 | 1 | 4 | chaque passage |
| Archive (4 modèles au point Gascogne + 21 bouées) | 25 | 1 | 1 à 3 | un passage sur trois (8 par jour) |

**Refus 429** : on ne peut pas les compter dans le passé. Le robot ne journalisait pas ses reprises, et les journaux GitHub de plus de quelques jours ne sont plus disponibles. Douze échecs depuis le 01/11 : les deux derniers lisibles sont une panne de déploiement GitHub (HTTP 500, 25/11) et un passage du 21/11 dont le journal est tronqué. **L'absence de refus visibles ne prouve pas que les quotas sont respectés** : c'est pourquoi ce lot ajoute la mesure.

### Règle de comptage d'Open-Meteo (https://open-meteo.com/en/pricing, lu le 27/11/2026)

- Une requête HTTP correspond « en général » à un appel. Plus de 10 variables ou plus de 2 semaines de données comptent en fractions d'appel supplémentaires (15 variables sur 2 semaines = 1,5 appel).
- **La règle pour plusieurs lieux dans une même requête n'est pas publiée.** Nous calculons donc toujours deux hypothèses :
  - **H1 « par requête »** : chaque requête compte une fois ;
  - **H2 « par point »** : chaque lieu de la requête compte.
- **Limites gratuites** : 600 appels par minute, 5 000 par heure, 10 000 par jour, 300 000 par mois.
- Le **calculateur** de la page tarifs comporte un champ **« Locations »** (vérifié le 27/11/2026 dans le code de la page) : le nombre de lieux entre bien dans le calcul. C'est un argument de plus pour H2, sans la règle exacte.
- La lecture des métadonnées des modèles n'est pas comptée dans les limites journalières et mensuelles (https://open-meteo.com/en/docs/model-updates). La page ne parle pas des limites par minute ou par heure.

## 2. Ce que fait ce lot

### Mesure à chaque passage
- **Requêtes logiques et tentatives HTTP** sont comptées séparément (`requests`, `attempts`, `attempts_ok`, `attempts_429`, `attempts_5xx`, `attempts_network`).
- Les poids H1 et H2 ne portent que sur les tentatives **acceptées**. Le poids des tentatives refusées est donné à part (`calls_if_per_point_refused`) : on ne suppose pas qu'un refus soit facturé.
- **Compteurs du jour** (`meta.api.today`, `.cache/usage/AAAA-MM-JJ.json`) : cumulés d'un passage à l'autre et conservés par `actions/cache`. C'est un dispositif **au mieux** : un cache peut être évincé. Ces compteurs ne prouvent pas le respect des quotas ; seul Open-Meteo connaît son propre décompte.

`openmeteo.get` enregistre chaque requête : API, nombre de points, nombre de variables, jours demandés, essais, codes HTTP (dont 429 et 5xx). Le résumé est écrit dans `forecast.json` (`meta.api`), dans `health.json` (`api`), dans le journal du robot et dans le résumé du contrôle avant publication. Il contient, pour chaque groupe de requêtes, la provenance (`api`, `cache` ou `cache-dégradé`), l'âge et la raison d'un nouvel appel. Il ne contient ni adresse ni paramètre.

### Cache persistant (`pipeline/omcache.py`)
- **Principe** : une réponse Open-Meteo est réutilisée tant qu'**aucun des modèles dont elle dépend** n'a publié de nouveau run. Le robot le sait en lisant les métadonnées publiques de chaque modèle (`last_run_availability_time`).
- **Nouvel appel aussi** : changement de paramètres (spot ajouté…), changement de jour (heure de Paris), plus de 6 h écoulées (filet de sécurité), métadonnées illisibles depuis plus d'1 h.
- **Vent séparé par modèle** : AROME, ICON, GFS et ECMWF ont chacun leur requête, redemandée quand **ce** modèle publie. Avant, la publication d'un seul modèle obligeait à tout redemander. Le lever et le coucher du soleil (calcul astronomique) sont redemandés une fois par jour.
- **Conservation** : le cache vit dans `.cache/openmeteo/` (ignoré par git). Dans GitHub Actions, `actions/cache` le restaure au début de chaque passage et ne le sauvegarde que s'il a changé. Chaque branche a son propre cache.
- **Mode dégradé explicite** : si Open-Meteo ne répond pas, une réponse en cache de **moins de 12 h** est réutilisée et signalée (`openmeteo_cache` dans `meta.errors`, avertissement du contrôle, provenance « cache-dégradé »). Le site continue alors de publier des **bouées à jour**. Au-delà de 12 h, la génération échoue comme avant, et le site garde sa dernière version. Le contrôle avant publication refuse toute prévision de plus de 12 h.
- **Désactivation** : `METEO_CACHE=0` fait tout redemander à chaque passage. Le vent reste toutefois en une requête par modèle : ce n'est **pas** exactement le regroupement d'avant ce lot.
- **Validation** : une réponse n'est mise en cache, puis réutilisée, que si elle est complète (des lieux, un axe `time`, des séries de même longueur). Un cache abîmé est ignoré.
- **Service de cache GitHub en panne** : la restauration et la sauvegarde ne bloquent jamais une génération valide (`continue-on-error`). Sans cache, tout est simplement redemandé.

### Ce qui ne change pas
- **Bouées** : même cadence (chaque passage, environ toutes les 30 min). CANDHIS, Copernicus et Météo-France sont lus à chaque passage, sans cache.
- **Archive** : toujours un passage sur trois, mêmes requêtes. Son coût est mesuré mais non optimisé ici (c'est le sujet de #1).
- **Marées** : calcul harmonique local, sans appel. Il n'y a rien à mettre en cache.
- Même rythme du robot, mêmes heures (#2), même application.

### Alignement horaire (corrigé après la revue de la PR #12)
Avant ce correctif, les séries étaient combinées **par position** : la n-ième valeur du vent avec la n-ième valeur de la mer. Or, en mode dégradé juste après minuit, une réponse reprise du cache de la veille commence 24 h plus tôt que les autres. Désormais, toutes les séries sont replacées **sur leurs heures réelles** : mer, 4 modèles de vagues, 4 modèles de vent (et donc le mélange et MARC, qui suivent cet axe). L'axe commun est celui de la réponse la plus récente. Le soleil est replacé **par date**.
- Chaque groupe doit couvrir l'heure actuelle et les 48 h suivantes, sinon le passage échoue et le site garde sa version.
- Le décalage d'un groupe (par exemple 24 h) est noté dans `meta.api`.
- Test intégré `tests/test_alignement.py` : passage à 23 h 50 puis à 0 h 20 ; vent GFS et soleil en panne, repris de la veille ; réponse AROME plus courte ; modèle de vagues sur 30 h refusé ; réponse abîmée refusée.
- L'heure d'été et d'hiver n'est pas traitée ici : c'est l'issue #2.

### Âge des prévisions par groupe (corrigé après la revue)
Le contrôle avant publication applique **12 h** aux prévisions météo et **24 h** au lever et au coucher du soleil. Un soleil collecté la veille reste juste, puisqu'il est replacé par date. Testé : un passage à 15 h ou à 23 h avec le soleil du matin et une météo fraîche est publié ; un soleil de plus de 24 h ou une météo de plus de 12 h est refusé.

### Mode dégradé visible (corrigé après la revue)
- `forecast.json` et `health.json` contiennent `meta.forecast_fetched` : l'heure de **collecte** la plus ancienne des prévisions météo. Ce n'est ni l'heure de génération, ni l'heure du run du modèle.
- `data/app/index.json` contient `forecast_fetched` et `forecast_degraded`, pour un affichage futur dans l'application. L'appli elle-même n'est pas modifiée.
- Sur le site, en mode dégradé, le pied de page et l'info-bulle « mis à jour » disent : « Prévisions collectées le … (service de prévision momentanément indisponible) ; mesures des bouées à jour ».
- Toutes les raisons publiées (`meta.api`) passent par `safe.public_error` : testé avec une fausse clé, une adresse avec identifiants et un paramètre.

### Fraîcheur : aucune dégradation, par construction
Avant, chaque passage redemandait tout, mais Open-Meteo ne renvoie des valeurs différentes qu'après la publication d'un nouveau run. Avec le cache, un nouveau run d'un modèle **surveillé** est pris **au premier passage qui suit sa disponibilité**, exactement comme avant. **Réserve** : Open-Meteo précise que le « best match » n'est pas directement lié aux runs individuels (https://open-meteo.com/en/docs/model-updates). Pour la requête « marine » (best match), la surveillance de ses modèles est une approximation, bornée par le filet de 6 h. L'âge affiché est l'âge de collecte de la réponse, pas celui du run. S'il a moins de 10 min (délai conseillé par Open-Meteo pour que tous ses serveurs l'aient), il est redemandé une seconde fois au passage suivant. Les seuls cas où une prévision peut être plus ancienne que la plus récente disponible :
- un modèle intermédiaire non listé dans les métadonnées surveillées : le filet de 6 h borne l'écart, et il est rattrapé dès qu'un autre modèle du groupe publie ;
- le mode dégradé (Open-Meteo en panne) : avant, il n'y avait alors **aucune** publication.

## 3. Comparatif avant / après (journée type, `python -m tools.api_budget`)

Calcul fait sur les heures de publication réelles des modèles (métadonnées Open-Meteo du 27/11/2026) et sur le rythme mesuré du robot : 48 passages cron-job.org et 8 programmés.

Journée type : 56 passages du robot (48 cron-job.org + 8 programmés) ; 176 points mer, 177 points terre, 15 bouées au point ; archive 25 requêtes × 8 passages (inchangée)

| Groupe | Requêtes par passage | Points | AVANT (requêtes/jour) | APRÈS (requêtes/jour) | AVANT H1 | APRÈS H1 | AVANT H2 | APRÈS H2 |
|---|---|---|---|---|---|---|---|---|
| wind+sun (avant) | 1 | 177 | 56 | 0 | 112 | 0 | 19824 | 0 |
| marine | 1 | 176 | 56 | 17 | 78 | 24 | 13798 | 4189 |
| wave_mfwam | 1 | 176 | 56 | 6 | 56 | 6 | 9856 | 1056 |
| wave_ewam | 1 | 176 | 56 | 7 | 56 | 7 | 9856 | 1232 |
| wave_ecmwf | 1 | 176 | 56 | 6 | 56 | 6 | 9856 | 1056 |
| wave_gfs | 1 | 176 | 56 | 6 | 56 | 6 | 9856 | 1056 |
| wind_arome | 1 | 177 | 0 | 13 | 0 | 13 | 0 | 2301 |
| wind_icon | 1 | 177 | 0 | 36 | 0 | 36 | 0 | 6372 |
| wind_gfs | 1 | 177 | 0 | 18 | 0 | 18 | 0 | 3186 |
| wind_ecmwf | 1 | 177 | 0 | 8 | 0 | 8 | 0 | 1416 |
| sun | 1 | 177 | 0 | 2 | 0 | 2 | 0 | 354 |
| point | 15 | 1 | 840 | 255 | 840 | 255 | 840 | 255 |
| archive (inchangée) | 25 | 1 | 200 | 200 | 200 | 200 | 200 | 200 |
| **Total / jour** | | | **1376** | **574** | **1454** | **581** | **74086** | **22673** |

Limite gratuite : 10 000 appels/jour, 300 000/mois. H1 : 1454 → 581 ; H2 : 74086 → 22673 (÷ 3.3). Par mois (×30) : H2 2.22 M → 0.68 M.
Métadonnées lues : {'ok': 14, 'failed': 0}

**Lecture** :
- **H1** : nous sommes, avant comme après, très en dessous de la limite gratuite.
- **H2** : la consommation est divisée par environ 3,3, mais **reste au-dessus de la limite gratuite** de 10 000 par jour. Elle passe en revanche sous le million par mois (forfait Standard).

**Pistes pour aller plus loin, non faites ici car elles changent les données :**
- regrouper les 176 points de mer par maille des modèles grossiers (ECMWF WAM et GFS-Wave à 0,25°) ;
- regrouper les 25 requêtes de l'archive en une requête à plusieurs points (#1) ;
- espacer le vent ICON, qui publie le plus souvent (D2, EU et global).

**Mesure réelle** : voir la section 4 (deux passages GitHub, cache vide puis cache rempli).

## 4. Validation réelle sur GitHub (branche, sans déploiement)

| | Passage 1 : cache vide ([run 45968059743](https://github.com/sharpeye64/meteo-surf/actions/runs/45968059743)) | Passage 2, 9 min après ([run 45969609430](https://github.com/sharpeye64/meteo-surf/actions/runs/45969609430)) |
|---|---|---|
| Requêtes Open-Meteo | 24 | **0** (24 réponses tirées du cache) |
| Points demandés | 1 779 | 0 |
| Appels H1 / H2 | 24,4 / 1 849 | 0 / 0 |
| Reprises, refus 429 | **4 reprises, 4 refus 429** | 0 |
| Âge maximal des prévisions | 0 h | 0,18 h (aucun nouveau run publié entre les deux) |
| Bouées | à jour | à jour (lues normalement) |
| Contrôle avant publication | OK (214 spots, 22 bouées, 254 pages) | OK (mêmes compteurs) |
| Durée de la construction | 5,9 min | 3,7 min |
| Archive, déploiement | ignorés (branche) | ignorés (branche) |

**Constat important** : le passage à cache vide a reçu **4 refus 429**. Jusqu'ici, ils étaient invisibles, car le robot réessayait sans les noter. Envoyer environ 1 850 « appels par point » en 1 à 2 minutes dépasse la limite gratuite de 600 par minute **si chaque point compte**. C'est un **indice fort** en faveur de l'hypothèse H2 (comptage par point), **pas une preuve**. Avec le cache, ces rafales n'ont lieu qu'aux publications des modèles, et en plus petites requêtes, une par groupe.

## 4 bis. Archive des modèles aux points des bouées (issue #1)

- **Avant** : 25 requêtes par passage d'archive (une par bouée et une par modèle à Gascogne), soit environ 475 requêtes par jour. Ce total compte les **11 passages par jour archivés en double**.
- **Après** : 5 requêtes groupées (22 bouées chacune), passées par le cache. On compte environ 25 requêtes par jour.
  - H1 (une requête = un appel) : −450 appels par jour.
  - H2 (un point = un appel) : +75 appels par jour, moins de 1 % de la limite gratuite.
- **Détail et stockage** : voir [archive-modeles.md](archive-modeles.md).

## 5. Licences et accès : inventaire au 27/11/2026

Ici, « licence des données » veut dire le droit de réutiliser les valeurs, et « accès » les conditions pour les obtenir (API, compte, quota). Les deux peuvent différer.

| Source | Usage dans Houlalah | Licence des données | Conditions d'accès | Usage commercial | À faire valider |
|---|---|---|---|---|---|
| **Open-Meteo** (prévisions vagues, vent, eau, soleil) | toutes les prévisions | CC BY 4.0 : attribution obligatoire, redistribution permise, y compris commerciale ([terms](https://open-meteo.com/en/terms), [pricing](https://open-meteo.com/en/pricing)) | API gratuite **non commerciale** : pas d'abonnement ni de publicité ; dons et « tip jar » permis. Limites 10 000 par jour, 300 000 par mois | **forfait payant obligatoire** (Standard 1 M, Professional 5 M, Enterprise > 50 M appels par mois, licence commerciale et adresse dédiée). **Prix non affichés sur la page** | prix réels (devis), règle de comptage multi-lieux (contact Open-Meteo, **décision du porteur**) |
| **CANDHIS / Cerema** (7 houlographes) | mesures en direct | Licence Ouverte Etalab 2.0 (mention de la source) | lecture des pages publiques (1 requête par bouée et par passage) ; API officielle avec jeton sur demande | permis par la licence | vérifier que la lecture automatique des pages reste tolérée ; demande de jeton API (contact externe, **décision du porteur**) |
| **Copernicus Marine** In Situ (bouées espagnoles et portugaises, Gascogne en secours) | mesures | licence Copernicus Marine : gratuite, y compris commerciale, avec attribution | fichiers publics, sans compte pour le dossier « latest » | permis avec attribution | texte exact de l'attribution requise |
| **Météo-France** API « Données d'observation » (bouée 62001) | mesure Gascogne | données publiques Météo-France (Licence Ouverte Etalab) | compte et clé gratuits sur portail-api.meteofrance.fr ; quota du portail | à vérifier dans les CGU du portail | CGU et quotas du portail |
| **Ifremer MARC** (modèle côtier) | prévision côtière | Licence Ouverte (selon le catalogue Ifremer) | OPeNDAP public | à confirmer | licence exacte du jeu de données |
| **SHOM / REFMAR** (constantes de marée calculées à partir des mesures) | marées | à vérifier : données REFMAR diffusées par le SHOM | API publique sans compte | **à vérifier** : les prédictions de marée « officielles » du SHOM ont des conditions spécifiques | statut d'une prédiction calculée par nous à partir des mesures |
| **NOAA NDBC** (secours Gascogne) | secours | domaine public (États-Unis) | public | oui | — |
| **OpenStreetMap / OpenFreeMap** (fond de carte) | carte | ODbL, attribution « © OpenStreetMap » | OpenFreeMap gratuit, sans clé | permis avec attribution | conditions d'OpenFreeMap en cas de fort trafic |
| **MapLibre GL, polices Google** (Unbounded, Manrope) | affichage | BSD-3 ; SIL Open Font License | jsDelivr, Google Fonts | oui | — |
| **GitHub Pages** (hébergement) | site | — | 1 Go de site, 100 Go par mois de bande passante (limite souple) ([limites](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)) | **pas un hébergement gratuit pour une activité commerciale** ; dons et financement participatif permis ([conditions](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#pages)) | hébergement à prévoir avant une offre payante |
| **GitHub Actions** (robot) et **actions/cache** | génération | — | cache : 10 Go par dépôt, entrées inutilisées 7 jours supprimées ([cache](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)) | minutes gratuites des dépôts publics : non vérifiées ici | facturation si le dépôt devient privé |
| **cron-job.org** (déclenchement toutes les 30 min) | rythme du robot | — | service gratuit, jeton GitHub du porteur | à vérifier | conditions d'utilisation |

### Coûts potentiels en cas de monétisation (estimations)

| Scénario | Ce qui change | Open-Meteo | Hébergement | Autres |
|---|---|---|---|---|
| **A. Aujourd'hui** (gratuit, sans pub) | — | gratuit si H1 ; si H2, au-dessus du gratuit (≈ 2,2 M par mois avant, ≈ 0,7 M après) | GitHub Pages gratuit | — |
| **B. Dons, « tip jar »** | bouton de don | toujours non commercial (dons permis) | GitHub Pages permet les boutons de don | — |
| **C. Publicité ou abonnement** | site ou appli commerciale | **forfait Standard au minimum**. 1 M par mois suffirait après ce lot en H2 **sous conditions** : estimation de journée type, reprises en plus (les 429 observés), archive #1 en plus, et **appels directs des navigateurs** en secours (`loadLive`, si `forecast.json` manque), qui ne passent pas par le robot. Prix sur devis, non affiché | hébergement commercial à prévoir (Pages exclu pour une activité commerciale) | stores (Apple 99 $ par an, déjà prévu), CGU et RGPD à revoir |
| **D1. Widget « mesures seules » chez un professionnel (#10)** | mesures des bouées uniquement | aucune donnée Open-Meteo : seules les licences des bouées (Etalab, Copernicus) et leurs attributions s'appliquent | Pages : trafic du widget | — |
| **D2. Widget « prévisions » chez un professionnel** | prévisions affichées chez un tiers | usage commercial, donc forfait payant Open-Meteo ; le widget lit nos fichiers, pas l'API | bande passante selon le trafic (100 Go par mois sur Pages) | attribution CC BY à reprendre dans le widget |
| **E. Archives (#1)** | 21 bouées × modèles, un passage sur trois | ≈ 0 en plus si regroupées en une requête à plusieurs points (H1), environ 200 à 300 appels par jour (H2) | stockage sur la branche `history` | — |

Ces conclusions sont **conditionnelles** : elles reposent sur des estimations et sur des conditions lues le 27/11/2026, pas sur une validation des fournisseurs.

**Aucun achat, abonnement ni contact n'a été fait.** Contacter Open-Meteo (règle multi-lieux, devis) ou le Cerema (jeton API) reste une décision du porteur.
