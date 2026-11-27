# Revue des guides Houlalah — 27 novembre 2026

Issue [#13](https://github.com/sharpeye64/meteo-surf/issues/13). PR d’origine [#15](https://github.com/sharpeye64/meteo-surf/pull/15), relue au commit `1823131`. Corrections sur `codex/geo-guides-audit`, avec le repère local `avant-geo-guides-audit`.

## Contenu et preuves

| Page | Ce que le lecteur peut vérifier | Référence |
|---|---|---|
| Lire une bouée | Moyenne du tiers supérieur comme illustration de Hs, différence avec Hm0 spectral, période de pic et fraîcheur du relevé | [NOAA/NDBC](https://www.ndbc.noaa.gov/faq/wavecalc.shtml), [guide Cerema/CANDHIS](https://candhis.cerema.fr/doc/01_UtilisationFR.pdf) |
| Comprendre la houle | Quatre cycles de 7 s contre deux de 14 s, réorientation des fronts sur une côte idéalisée, abri partiel derrière un cap, somme quadratique des hauteurs des partitions | [Coastal Wiki](https://www.coastalwiki.org/wiki/Shallow-water_wave_theory), [analyse NOAA de la houle et de la mer du vent](https://www.ndbc.noaa.gov/waveobs.shtml) |
| Comprendre la houle, comparateur | Le flux en eau profonde est proportionnel à Hs² × Te. Te est une période énergétique issue du spectre. Le calcul ne fournit pas la hauteur au déferlement | [Soukissian et Karathanasi, 2021, équations 1 à 3](https://doi.org/10.3390/pr9030460) |
| Modèles de houle | Trois modèles proches peuvent partager un biais. Dans l’exemple fictif, l’étendue est de 0,2 m et l’écart entre moyenne et mesure de +0,7 m. L’échéance propre au modèle part de son initialisation. Les horizons de l’archive Houlalah partent de l’heure enregistrée dans `issued` | [Open-Meteo, modèles marins](https://open-meteo.com/en/docs/marine-weather-api), [cycles des modèles](https://open-meteo.com/en/docs/model-updates), [présentation d’Ifremer sur MARC](https://www.cerema.fr/fr/system/files?file=documents%2F2026%2F01%2F02-jfpiolle_odatis.pdf), [code de l’archive](../pipeline/history.py) |

Le lien général vers la NOAA a été remplacé par la page pertinente. Pour la réfraction, la référence Coastal Wiki distingue l’effet de la profondeur sur la vitesse de propagation de la dissipation par frottement. Les cinq SVG sont des illustrations hors échelle ou des exemples calculés, sans donnée réelle de spot.

## Corrections

- Précision sur la période de pic, la direction de provenance, la réfraction et les périodes des modèles. Un exemple de deux composantes à 1,2 m et 0,9 m montre comment obtenir 1,5 m pour le spectre total.
- Comparateur en eau profonde. L’interface indique les bornes et accepte les décimales. Elle conserve le résultat de l’autre état quand un champ devient invalide. L’affichage garde jusqu’à quatre chiffres significatifs pour représenter les petits flux et rapports positifs. Les champs et résultats sont associés et les valeurs initiales restent lisibles sans JavaScript.
- Le gabarit Premium Ocean, les quatre URL, leurs canoniques et leur présence dans le sitemap et `llms.txt` sont conservés. Le comparateur reste indépendant du moteur météo.
- L’aperçu HTML regroupe l’index, les trois guides et la méthode. Il embarque le symbole et le mot-symbole officiels de `web/brand/`, fonctionne avec JavaScript local et renvoie vers le site public pour les autres pages.

## Vérification

- [CI de la PR #15](https://github.com/sharpeye64/meteo-surf/actions/runs/45977773987) au commit `1823131`. Les cinq suites du job `surete` ont réussi. Les jobs de génération et de déploiement ont été ignorés selon les conditions du workflow.
- Chromium à 1 440, 390 et 320 px. Vérification des liens entre guides, des canoniques, des cinq SVG, du logo, de l’absence de débordement horizontal et du comparateur au clavier. Valeurs testées : état initial, rapport 1, doublement de hauteur à période constante (×4), décimales, bornes, champ vide, zéro et valeurs hors limites. Valeurs initiales et aide vérifiées sur le guide avec JavaScript désactivé.
- Cinq suites locales en Python 3.12 réussies : `test_offline`, `simulate_pannes` (37 scénarios), `panne_bout_en_bout`, `test_cache` et `test_alignement`. Le contrôle `tools.check_site` a aussi accepté le site régénéré localement à partir des données publiques de 10 h 39 (heure de Paris) et du diagnostic de la même génération : 258 pages générées, 259 URL dans le sitemap avec la racine, 214 spots et 22 bouées. Un avertissement préexistant concerne l’absence de fichier récent pour la station `ibi_6200084`.
- Aperçu HTML ouvert depuis un fichier local, avec navigation, bouton Retour du navigateur et ouverture directe du guide de la houle. Les contrôles navigateur ont neutralisé les requêtes aux polices et aux statistiques externes. Le contrôle mobile a été effectué sur des tailles de fenêtre émulées dans Chromium.

La mise en ligne reste soumise à la validation d’Andréa. Après publication, vérifier les chemins publics puis suivre l’indexation et les citations avec le protocole décrit dans [GEO.md](GEO.md).
