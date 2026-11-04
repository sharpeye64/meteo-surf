# Météo surf · prototype

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

## Activer les marées exactes (une fois par port)

Sans cette étape, le site affiche des marées approximatives.

1. Va sur https://data.shom.fr, rubrique **REFMAR**.
2. Choisis le marégraphe **Socoa**, puis télécharge environ 1 an de hauteurs d'eau (« validées horaires » si possible, en heure UTC).
3. Mets le fichier dans `tides/raw/`, sous le nom `socoa.txt`.
4. Lance : `python -m tools.fit_tides tides/raw/socoa.txt socoa 43.39`
5. Recommence avec **Boucau-Bayonne** : `python -m tools.fit_tides tides/raw/boucau.txt boucau 43.52`
6. Envoie les fichiers créés dans `tides/constants/` sur GitHub. Le robot les utilisera au prochain passage.

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
