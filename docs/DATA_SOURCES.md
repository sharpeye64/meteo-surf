# Sources de données et méthodes de calcul

Règle absolue : **aucune donnée inventée**. Une donnée absente n'est pas affichée, ou est signalée comme absente.

## 1. Prévisions de vagues

| Modèle | Fournisseur | Accès | Poids dans le mélange |
|---|---|---|---|
| MARC (WAVEWATCH III Golfe de Gascogne, environ 3,7 km) | Ifremer | OPeNDAP direct, Licence Ouverte | 0,30 (quand disponible) |
| MFWAM | Météo-France | via Open-Meteo | 0,25 |
| EWAM (5 km) | DWD | via Open-Meteo | 0,25 |
| ECMWF WAM | ECMWF | via Open-Meteo | 0,15 |
| GFS-Wave | NOAA | via Open-Meteo | 0,05 |

- **Mélange** : moyenne pondérée heure par heure (`pipeline/build.py`).
- **Modèles écartés** : un modèle qui annonce 0,00 m sur toute la série (maille « terre », fréquent avec GFS-Wave près des côtes) est retiré du mélange.
- **Accord des modèles** : fort si l'écart est inférieur à 0,15 m ou 15 % ; moyen jusqu'au double ; faible au-delà. Affiché en trois points, sans jugement de qualité.
- **Correction par la bouée Gascogne** : le rapport mesure / prévision au point de la bouée corrige les modèles. L'effet décroît jusqu'à 0 sur `BUOY_CORRECTION_HOURS`, à partir de l'**heure de la dernière mesure**. Pas de correction si la mesure est trop ancienne (`BUOY_MAX_AGE_HOURS`).
- **Heure d'arrivée** de la houle vue à Gascogne : `eta_hours` par spot (calcul de propagation). Elle n'est pas affichée en premier plan ; l'idée d'une « heure d'arrivée de la houle » a été écartée de l'interface.
- **Houle principale, secondaire et mer du vent** : trains de houle d'un modèle de vagues, montrés dans le « Détail de la houle » à la demande.
- **Hauteur au large ≠ taille au bord** : `h.Heff` (hauteur × exposition × période) ne sert qu'au calcul interne. Aucune « taille au bord » n'est affichée tant qu'elle n'a pas été apprise et validée sur l'archive.

## 2. Prévisions de vent

| Modèle | Fournisseur | Accès |
|---|---|---|
| AROME (modèle principal) | Météo-France | via Open-Meteo |
| ICON | DWD | via Open-Meteo |
| GFS | NOAA | via Open-Meteo |
| IFS | ECMWF | via Open-Meteo |

**Orientation du vent pour un spot** : même règle sur le site (`windInfo`) et dans les pages (`seo.wind_for_spot`). On mesure l'angle entre le vent et la direction offshore du spot (orientation + 180°) :

| Condition | Mot affiché |
|---|---|
| Vent sous 8 km/h | « Lisse » |
| Angle ≤ 45° | « Offshore » |
| Angle ≤ 80° | « Side-offshore » |
| Angle ≤ 120° | « Side-shore » |
| Au-delà | « Onshore » |

## 3. Mesures réelles : 22 bouées

| Réseau | Stations | Accès | Cadence | Licence |
|---|---|---|---|---|
| **CANDHIS (Cerema) — houlographes** | Cap Ferret 03302, Anglet 06402, Saint-Jean-de-Luz 06403, Plateau du Four 04403, Les Pierres Noires 02911, Île de Batz 02922, Belle-Île 05602 | pages publiques (1 requête par bouée et par passage) | 1 mesure toutes les 30 min | Licence Ouverte Etalab 2.0 ; temps réel non validé |
| **Météo-France** | Gascogne (WMO 62001), au large | API publique « Données d'observation » (clé en secret GitHub), Copernicus en secours, NOAA en dernier recours | horaire, environ 1 h de retard (API) ; une fois par jour via Copernicus | Licence Ouverte. Seule la période **moyenne** est fournie (`per_moy_vag`), jamais présentée comme une période pic |
| **Copernicus Marine In Situ (IBI)** | Bilbao-Vizcaya (Puertos del Estado), Donostia (Euskalmet), Bilbao côte, Pasaia, Gijón, Cabo Peñas, Estaca de Bares, A Coruña, Cabo Vilano-Sisargas, Cabo Silleiro, Leixões, Nazaré, Sines, Faro | fichiers NetCDF publics | horaire, 30 à 60 min de retard (irrégulier pour Leixões, Sines, Faro) | données Copernicus Marine, libres ; citer « Copernicus Marine Service » et l'exploitant quand il est connu |

**Variables** : hauteur significative, hauteur maximale, période pic (sauf Gascogne), direction, température de l'eau.

### Fraîcheur : une seule règle partout

Elle s'applique sur le site (`pvFresh(ageH, t, key)`, `pvLim`), dans les pages de bouées (`bouees.station()`, `fresh_state()`) et dans les titres Google.

| Station | « En direct » | « Récente » | « Ancienne » | « Muette » |
|---|---|---|---|---|
| Houlographe CANDHIS | < 1 h | < 3 h | < 48 h | au-delà |
| Bouée horaire (Météo-France, Copernicus) | < 2 h | < 6 h | < 48 h | au-delà |

- **Pastille verte animée** : seulement pour « en direct ».
- **Titre Google** : « houle en direct » tant que la station publie normalement, « dernières mesures » sinon.
- **Station qui ne publie plus** : un encadré « Pas de mesure transmise depuis… » propose les 3 bouées à jour les plus proches.
- **Robot arrêté** : la page de bouée se corrige seule dans le navigateur.
- **À aligner** : l'application mobile a encore ses propres seuils (voir [HANDOFF.md](HANDOFF.md)).

### Bouée de référence d'un spot

La règle est la même sur le site, dans l'application et dans le robot : la plus proche dont la mesure a moins de 2 h (et à moins de 60 km), sinon la plus proche de moins de 6 h, sinon la plus fraîche. S'y ajoutent des cas particuliers :
- **Landes** : Cap Ferret pour le nord, jusqu'à 70 km ; Gascogne pour Saint-Girons à Tarnos.
- **Bouée abritée de Sainte-Barbe** : réservée à son spot (`BUOY_ONLY`).
- **Choix fait à la main** : retenu par spot (`localStorage.radarViews`).

## 4. Marées

- **Calcul harmonique indépendant** (`pipeline/tides.py`) à partir d'un an de mesures REFMAR validées (Shom, Licence Ouverte), par port : Socoa, Boucau-Bayonne, Brest et les autres ports français. Écart avec des mesures jamais utilisées pour le calcul : **5 min en moyenne**, 15 min au pire.
- **Coefficient** : calculé pour Brest (marnage ÷ 6,10 m × 100), avec un écart moyen de 2 points avec les valeurs publiées.
- **Rattachement des spots** : chaque spot a un port de marée (`tide_port`) et un décalage en minutes (`tide_offset_min`, à calibrer sur le terrain).
- **Statut** : ces prédictions **ne sont pas officielles**. Afficher les prédictions officielles demanderait une licence Shom.
- **Espagne et Portugal** : pas encore de port de marée, donc pas de marées affichées (75 spots).

## 5. Fiabilité mesurée et archive

- **Où** : branche git `history`, écrite par le robot un passage sur trois (heures UTC multiples de 3).
- **Contenu** :
  - mesures horaires des 21 bouées et de Gascogne ;
  - prévisions sur 96 h au point des bouées, archivées à chaque passage ;
  - depuis l'issue #1 (`buoy_runs/`) : les modèles un par un, MARC, les mélanges brut et corrigé et leur provenance ([archive-modeles.md](archive-modeles.md)).
- **Calcul** (`history.reliability`) : écart prévision − mesure par échéance (24, 48, 72, 96 h) et par modèle, sur 30 jours. Le site affiche l'écart moyen de la prévision à 1 jour avec la bouée Gascogne.
- **Inventaire, volumes, statistiques possibles et droits** : voir [archives-bouees-potentiel.md](archives-bouees-potentiel.md).

## 6. Licences et usage commercial

| Source | Licence | Usage commercial |
|---|---|---|
| Open-Meteo (toutes les prévisions sauf MARC) | API gratuite **non commerciale** ; données CC BY 4.0 | **non** sans abonnement |
| Ifremer MARC | Licence Ouverte | oui |
| CANDHIS, Météo-France, Shom REFMAR | Licence Ouverte Etalab 2.0 | oui, avec attribution |
| Copernicus Marine | licence Copernicus (libre) | oui, avec attribution |
| OpenFreeMap / OpenStreetMap | ODbL / attribution | oui, avec attribution (crédits de carte toujours visibles) |

**Conséquence** : toute monétisation de Houlalah suppose un abonnement Open-Meteo, ou un accès direct aux modèles ouverts. À faire valider par un juriste.

## 7. Sources écartées

| Source | Raison |
|---|---|
| Allosurf, surf-report, Meteociel, Surf-Forecast (pour les mesures) | pas de réutilisation autorisée ; ne pas les exploiter |
| Tourisme Landes (webcams) | bloque les vérifications automatiques |
| Intégration de webcams | on fait seulement des **liens sortants** (conditions d'utilisation des tiers) |
