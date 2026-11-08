# Houlalah · prévisions surf (prototype)

Site de prévisions surf de Lacanau à Hendaye (58 spots).

Toutes les 3 heures, un robot (GitHub Actions) récupère les données, les croise et publie le site.

## Ce que fait le robot

1. **Vagues** : mix pondéré de 5 modèles.
   - Ifremer MARC (modèle côtier) ;
   - Météo-France MFWAM ;
   - DWD EWAM ;
   - ECMWF WAM ;
   - NOAA GFS-Wave.
2. **Vent** : Météo-France AROME, comparé à ICON, GFS et ECMWF.
3. **Radar Gascogne** : la bouée au large (62001) donne la houle réelle et son heure d'arrivée sur chaque spot. Elle corrige aussi les modèles sur les 24 prochaines heures.
4. **Marées** : pleines et basses mers à la minute, par calcul harmonique à partir des marégraphes officiels REFMAR.
5. Il écrit tout dans `web/data/forecast.json`, que le site lit.

## Mise en ligne (une étape à la fois)

1. Crée un compte sur github.com si tu n'en as pas.
2. Crée un nouveau dépôt **public** nommé `meteo-surf`.
3. Envoie tout le contenu de ce dossier dans le dépôt. Avec Claude Code, demande : « pousse ce dossier sur mon dépôt GitHub meteo-surf ».
4. Dans le dépôt, va dans **Settings → Pages** et choisis **Source : GitHub Actions**.
5. Va dans l'onglet **Actions**, ouvre « Mise à jour des prévisions » et clique **Run workflow**.
6. Au bout de 2 à 3 minutes, le site est en ligne à l'adresse affichée dans **Settings → Pages**.

## Fiabilité mesurée (archive prévision / réalité)

À chaque passage (toutes les 3 h), le robot garde dans la branche `history` du dépôt :
- la hauteur de vagues prévue par chaque modèle au point de la bouée Gascogne, pour les 96 prochaines heures ;
- les mesures horaires de la bouée.

Il compare ensuite la prévision faite 24, 48, 72 et 96 h plus tôt à la mesure réelle, et le site affiche l'écart (section « Fiabilité des données »).
Les chiffres apparaissent après quelques jours de collecte. Limite : la bouée est au large, elle vérifie les modèles de houle, pas le détail près des spots.
Pour regarder l'archive : branche `history` sur GitHub (dossiers `runs/` et `obs/`).

## Accord des modèles

Pour chaque heure, le site compare les modèles de houle entre eux : fort (écart sous 0,15 m ou 15 %), moyen (jusqu'au double), faible (au-delà).
Un modèle qui annonce 0,00 m sur toute la série (maille « terre », fréquent avec GFS-Wave près de la côte) est écarté du mélange.

## Coefficient de marée

Calculé pour Brest (station REFMAR 3) : marnage ÷ 6,10 m × 100. Écart moyen de 2 points avec les valeurs publiées (contrôle sur novembre 2026).
Les constantes se rafraîchissent comme les autres ports : `python -m tools.get_refmar brest` puis `python -m tools.fit_tides tides/raw/brest.txt brest 48.38`.

## Marées exactes (déjà activées)

Les constantes de Socoa et de Boucau-Bayonne sont dans `tides/constants/`, calculées sur un an de mesures REFMAR validées.
Écart constaté avec des mesures réelles jamais utilisées pour le calcul : 5 minutes en moyenne, 15 minutes au pire.

Pour les rafraîchir (une fois par an suffit) :

1. `python -m tools.get_refmar socoa` : télécharge les mesures depuis l'API publique du Shom, sans compte (`tides/raw/socoa.txt`).
2. `python -m tools.fit_tides tides/raw/socoa.txt socoa 43.395`
3. Pareil pour Boucau : `python -m tools.get_refmar boucau` puis `python -m tools.fit_tides tides/raw/boucau.txt boucau 43.52`
4. Envoie les fichiers de `tides/constants/` sur GitHub. Les mesures brutes (`tides/raw/`) ne sont pas envoyées.

Chaque spot est rattaché à un port (`tide_port` dans `pipeline/spots.json`). Le champ `tide_offset_min` permet de décaler un spot de quelques minutes, à calibrer sur le terrain.

## Tester en local

```
pip install -r requirements.txt
python -m tests.test_offline        # pipeline complet avec données simulées, sans internet
python -m pipeline.build            # vraies données (internet nécessaire)
cd web && python -m http.server     # puis ouvrir http://localhost:8000
```

Si `forecast.json` est absent, le site interroge Open-Meteo directement (mode secours, sans bouée, sans MARC, sans marées exactes).

## Sources et licences

- **Open-Meteo** (CC BY 4.0) : gratuit en usage non commercial. Pour un usage commercial, il faut un abonnement.
- **Ifremer MARC** : Licence Ouverte.
- **Mesures REFMAR** : © Shom, Licence Ouverte. Nos horaires de marée sont un calcul indépendant, **non officiel**. Pour afficher les prédictions officielles, il faut une licence Shom.
- **Bouée Gascogne** : Météo-France, diffusée par Copernicus Marine In Situ (accès libre). La NOAA (NDBC) sert de secours.
