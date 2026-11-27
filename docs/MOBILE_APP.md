# Application mobile (dossier `app/`)

## Statut

- **Code** : publié sur `main` le 18/11/2026.
- **Distribution** : **pas sur les stores**. Elle fonctionne en développement avec Expo Go, sur iPhone.
- **Étape suivante** (décidée avec le porteur) : prendre un compte Apple développeur (99 $/an), faire une vraie version installée sur l'iPhone, puis viser les stores.

## Stack

- **Expo SDK 58**, React Native 0.88, React 19, TypeScript.
- **Avant tout code Expo** : lire [app/AGENTS.md](../app/AGENTS.md). Il faut se référer aux docs versionnées et ajouter les paquets avec `npx expo install`.
- **Navigation maison** (onglets et pile d'écrans dans `App.tsx`), **sans Expo Router**. Attention : `app/AGENTS.md` décrit Expo Router de façon générique, mais ce projet ne l'utilise pas.
- **Carte** : `react-native-maps` (pas de carte dans l'aperçu web). Polices Unbounded et Manrope (`@expo-google-fonts`). Stockage : `@react-native-async-storage/async-storage` (favoris).
- **Vérifier** avec `npx tsc --noEmit` dans `app/`.

## Données

- **Adresse** : `EXPO_PUBLIC_DATA_URL`, par défaut `https://houlalah.fr/data/app`.
- **Fichiers** écrits par le robot (`pipeline/appdata.py`) : `index.json` (tous les spots et toutes les bouées, version allégée), `spots/<slug>.json`, `bouees/<slug>.json`.
- **Tests** : `python -m tests.test_offline` écrit dans un dossier temporaire et ne touche plus `web/data/app/`. Pour tester l'appli avec de vraies données en local, voir [HANDOFF.md](HANDOFF.md).

## Écrans

| Fichier | Rôle |
|---|---|
| `src/Home.tsx` | Onglet « Spots » (« Mon tableau ») : recherche, votre spot en grand avec une mini-frise, spots autour, bouées en direct, côte par pays et région |
| `src/MapScreen.tsx` | Onglet « Carte » : plein écran, satellite ou plan, tous les spots, bouées qui pulsent |
| `src/BuoyScreens.tsx` | Onglet « Bouées » (« Autour de mon spot », puis par zone) et page d'une bouée |
| `src/SpotList.tsx` | Onglet « Favoris » |
| `src/SpotSheet.tsx` | Fiche d'un spot : 4 carrés (houle, vent, eau, soleil), frise horaire avec la courbe de marée alignée, PM/BM à leur heure |
| `src/TabBar.tsx` | Barre d'onglets flottante (`useBarSpace()`) |
| `src/Live.tsx` | Pastille « en direct » qui clignote |
| `src/data.ts` | Chargement, favoris, fraîcheur et bouée de référence (`freshOf`, `isLive`, `refBuoy`, `perTxt`) |
| `src/rules.ts` | **Règles métier communes avec le site et le robot**, sans dépendance : fraîcheur selon la cadence, vent, secteurs, bouée de référence ([regles-communes.md](regles-communes.md)) |
| `src/theme.ts` | Deux palettes (clair, sombre) de mêmes clés ; styles via `themed(() => StyleSheet.create(...))` |

## Règles
- **Heures** (issue #2) : toujours passer par `src/time.ts` (`tMs`, `partsIn`, `placeTz`), jamais `new Date(t + ':00')` ni `getHours()` du téléphone. Affichage à l'heure du spot (champ `tz`). Voir [heures.md](heures.md).

- **Couleurs** : toujours passer par `C` (theme.ts). Une couleur en dur casse le mode sombre.
- **Mode sombre** : automatique, il suit le réglage du téléphone (`userInterfaceStyle: automatic`).
- **Règles métier** (issue #4) : fraîcheur selon la cadence de chaque station, vent, secteurs et bouée de référence passent par `src/rules.ts`. Ce sont les mêmes règles que le site, vérifiées sur les mêmes cas (`tests/regles_communes.json`). Ne jamais écrire de seuil en dur (`ageH < 2`…) dans un écran. Voir [regles-communes.md](regles-communes.md).
- **Âges** : recalculés chaque minute et au retour au premier plan. Les données sont alors redemandées (`App.tsx`).
- **Période de Gascogne** : c'est une période moyenne, écrite « 9 s moy. ».
- **Icône et écran de démarrage** « A · Nuit » : `python -m tools.app_icons`. Ils sont invisibles dans Expo Go.

## Tester

- **Sur l'iPhone** : `& .\app\tester-sur-telephone.ps1`, dans un onglet du panneau Terminal. Le script lance le serveur de données du PC (`tools/serveur_local.py web 8766`), puis Metro (port 8082). Le PC et le téléphone doivent être sur le même Wi-Fi.
- **Aperçu web** : configuration `appli-web` (port 8081) de `.claude/launch.json`.

## Limitations et écarts connus

- **Valeurs « maintenant » de l'index** : elles sont calculées à l'heure de la génération. Hors connexion, avec un index ancien, elles datent de cette heure-là (voir [regles-communes.md](regles-communes.md), écarts connus).
- **Design** : l'application n'a pas encore reçu la direction Premium Ocean (palette « Nuit » d'origine).
- **Fonctionnalités** : pas d'alertes, pas de widgets. Elles sont prévues après la vraie version installée, et ce sont elles qui justifient une application.
- **Android** : pour une vraie version Android, il faudra installer `expo-system-ui` (mode sombre automatique), avec l'accord du porteur.
- **Webcams** : liens externes seulement, comme sur le site.
