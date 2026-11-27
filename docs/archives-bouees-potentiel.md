# Archives des bouées : ce que nous avons, ce qu'on peut en faire

Inventaire au 26/11/2026, à partir de la branche git `history` (écrite par le robot, `pipeline/history.py`). Rien n'est développé ici. Le but est de connaître notre potentiel technique et produit.

## 1. Depuis quand ?

| Archive | Début | Stations |
|---|---|---|
| Mesures de la bouée Gascogne (Météo-France 62001) | 06/11/2026 | 1 |
| Mesures des bouées côtières et du large | 07/11/2026 pour Cap Ferret, Anglet, Saint-Jean-de-Luz, Bilbao-Vizcaya et Donostia ; 13/11/2026 pour les 16 autres | 21 |
| Prévisions archivées au point de la bouée Gascogne (`runs`) | 08/11/2026 | 290 passages du robot |
| Prévisions archivées aux points des bouées côtières (`coast_runs`) | 09/11/2026 | 250 passages du robot |

Il y a donc **3 semaines d'historique** environ. L'archive n'est écrite qu'un passage du robot sur trois, aux heures UTC multiples de 3.

## 2. Quelles données ?

- **Mesures**, une valeur par heure et par station :
  - hauteur significative `hs` ;
  - hauteur maximale `hmax` ;
  - période pic `tp` ;
  - direction `dir` ;
  - température de l'eau `sst`.

  Pour Gascogne, `hs` et la période. Météo-France ne fournit que la période moyenne : elle n'est jamais présentée comme une période pic.
- **Prévisions archivées** : à chaque passage, la prévision sur 96 h au point de la bouée. _Correction du 27/11 (issue #1) : jusqu'ici, seul le « best match » d'Open-Meteo (hauteur, période, direction) était archivé aux bouées côtières, et les 4 modèles seulement à Gascogne ; ni MARC ni notre mélange ne l'étaient. Depuis l'archive v2 (`buoy_runs/`), on garde les modèles un par un, MARC et les mélanges brut et corrigé : voir [archive-modeles.md](archive-modeles.md)._ On pourra donc comparer, après coup, **ce qui était prévu** à **ce qui a été mesuré**, selon l'échéance (à 6 h, 24 h, 48 h…).
- **Fichiers** : `obs/AAAA-MM.json` (Gascogne), `coast_obs/AAAA-MM.json` (21 stations), `runs/AAAA-MM.jsonl`, `coast_runs/AAAA-MM.jsonl`. Un fichier par mois.

## 3. Fréquence et complétude (novembre 2026)

| Station | Relevés horaires | Période | Complétude | Remarque |
|---|---|---|---|---|
| Cap Ferret (CANDHIS 03302) | 464 | 07/11 → 26/11 | 100 % | |
| Anglet (06402) | 177 | 07/11 → 18/11 | 70 % | muette depuis le 18/11 ; direction et eau souvent absentes |
| Saint-Jean-de-Luz (06403) | 463 | 07/11 → 26/11 | 100 % | |
| Plateau du Four (04403) | 177 | 13/11 → 26/11 | 56 % | direction et eau absentes plus d'une fois sur deux |
| Les Pierres Noires (02911) | 298 | 13/11 → 26/11 | 96 % | |
| Île de Batz (02922) | 286 | 13/11 → 26/11 | 95 % | |
| Belle-Île (05602) | 288 | 13/11 → 25/11 | 100 % | |
| Bilbao-Vizcaya, Donostia | 459–463 | 07/11 → 26/11 | 99–100 % | |
| 11 autres stations Copernicus | 288–311 | 13/11 → 26/11 | 93–100 % | Cabo Peñas et Cabo Silleiro sans hauteur maximale ; Cabo Silleiro muette depuis le 21/11 |

**Lecture** : la plupart des stations sont complètes. Les trous correspondent à de vraies coupures côté source (Anglet, Plateau du Four, Cabo Silleiro). Ce n'est pas une panne du robot : le relevé public de la station présente les mêmes trous.

## 4. Volumes

- **Total actuel** : 7,3 Mo pour environ 3 semaines.
  - mesures des 21 stations : 0,5 Mo ;
  - prévisions aux points côtiers : 6,2 Mo ;
  - prévisions Gascogne : 0,6 Mo ;
  - mesures Gascogne : 18 Ko.
- **Projection** : environ 10 Mo par mois, soit **120 Mo par an**. Les prévisions archivées en font 90 %. C'est gérable dans git pendant un an ou deux. Au-delà, il faudra compresser (gzip ou Parquet, environ 10 fois moins) ou réduire les prévisions archivées (une échéance sur trois, par exemple).

## 5. Statistiques possibles (sans rien inventer)

**Dès maintenant, ou en quelques semaines**
- Par station : houle moyenne et maximale du mois, plus grosse vague mesurée (`hmax`), jours au-dessus de 1 m, 2 m ou 3 m, répartition des périodes et des directions, température de l'eau (moyenne, extrêmes, tendance). Une partie est déjà affichée (« Records et moyennes »).
- **Fiabilité de nos prévisions par bouée**, l'atout le plus différenciant :
  - écart moyen prévu / mesuré, et biais (trop haut ou trop bas) ;
  - par échéance (6 h, 24 h, 48 h, 72 h) ;
  - par modèle (lequel est le plus juste ici) ;
  - par situation (petite ou grosse houle).

  C'est la promesse « la houle prévue, vérifiée par les bouées », mesurée et publiable.
- **Journal des tempêtes** : épisodes au-dessus d'un seuil, avec début, pic, durée et période au pic.

**Après 30 jours ou plus par station** (objectif déjà noté dans le projet)
- **Taille au bord** : apprendre, pour chaque bouée côtière, la relation « prévision au large (hauteur, période) → mesure près de la côte ». À n'afficher qu'après validation.

**Après une saison, ou un an**
- Normales saisonnières (« novembre est-il gros cette année ? »), percentiles, probabilité d'avoir plus de 1,5 m un jour donné du mois, comparaison d'une année à l'autre.

## 6. Droits d'exploitation (à faire confirmer par un juriste avant toute monétisation)

| Source | Licence | Usage commercial | Obligation |
|---|---|---|---|
| CANDHIS (Cerema) : 7 houlographes | Licence Ouverte Etalab 2.0 | oui | citer la source et la date de mise à jour ; les mesures temps réel ne sont pas validées |
| Météo-France (bouée 62001, API publique) | Licence Ouverte Etalab 2.0 | oui | citer la source ; respecter les conditions d'usage de l'API (quotas, compte) |
| Copernicus Marine (Puertos del Estado, Euskalmet et autres plateformes) | licence Copernicus Marine (libre et gratuite) | oui | citer « Copernicus Marine Service » et la source d'origine quand elle est connue |
| Shom REFMAR (mesures de marée servant à nos constantes) | Licence Ouverte | oui | citer le Shom ; nos prédictions de marée sont notre propre calcul |
| **Open-Meteo (prévisions des modèles)** | API gratuite **réservée à un usage non commercial** ; données sous CC BY 4.0 | **non avec l'API gratuite** | un abonnement Open-Meteo (ou un accès direct aux modèles ouverts) est nécessaire pour un usage commercial |

**Ce qui en découle**
- Les **mesures archivées**, et les statistiques qu'on en tire, peuvent être exploitées commercialement, avec attribution.
- Les **prévisions archivées** viennent d'Open-Meteo. Leur usage commercial suppose l'offre payante d'Open-Meteo, ou de passer aux modèles en direct : MFWAM via Copernicus Marine, ECMWF et DWD en données ouvertes, NOAA dans le domaine public. Ce point conditionne toute monétisation du site lui-même, pas seulement des archives.
- **Pistes compatibles** : abonnement « Pro » (historique détaillé, fiabilité par modèle et par bouée, alertes), statistiques pour les écoles de surf ou les collectivités, API de statistiques agrégées. Toujours avec les mentions de source.

## 7. Ce qu'il faudrait décider plus tard

1. **Ordre des fonctionnalités** : par exemple, la fiabilité par bouée d'abord (forte valeur, données déjà là), puis l'historique mensuel, puis la taille au bord.
2. **Stockage** : passer à un format compressé quand l'archive dépassera environ 50 Mo.
3. **Licences** : clarifier la situation Open-Meteo avant toute offre payante.
