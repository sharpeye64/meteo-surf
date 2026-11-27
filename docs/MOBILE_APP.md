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
| `src/data.ts` | Chargement, favoris, règles bouée / spot (`buoyFits`, `prefBuoy`, `perTxt`) |
| `src/theme.ts` | Deux palettes (clair, sombre) de mêmes clés ; styles via `themed(() => StyleSheet.create(...))` |

## Règles
- **Heures** (issue #2) : toujours passer par `src/time.ts` (`tMs`, `partsIn`, `placeTz`), jamais `new Date(t + ':00')` ni `getHours()` du téléphone. Affichage à l'heure du spot (champ `tz`). Voir [heures.md](heures.md).

- **Couleurs** : toujours passer par `C` (theme.ts). Une couleur en dur casse le mode sombre.
- **Mode sombre** : automatique, il suit le réglage du téléphone (`userInterfaceStyle: automatic`).
- **Bouée de référence** : mêmes règles que le site (`buoyFits`, `prefBuoy` : Landes, Sainte-Barbe).
- **Période de Gascogne** : c'est une période moyenne, écrite « 9 s moy. ».
- **Icône et écran de démarrage** « A · Nuit » : `python -m tools.app_icons`. Ils sont invisibles dans Expo Go.

## Tester

- **Sur l'iPhone** : `& .\app\tester-sur-telephone.ps1`, dans un onglet du panneau Terminal. Le script lance le serveur de données du PC (`tools/serveur_local.py web 8766`), puis Metro (port 8082). Le PC et le téléphone doivent être sur le même Wi-Fi.
- **Aperçu web** : configuration `appli-web` (port 8081) de `.claude/launch.json`.

## Limitations et écarts connus

- **Fraîcheur des bouées** : l'application utilise ses propres seuils (« en direct » < 2 h, référence < 6 h). Elle ne suit pas encore la règle « selon la cadence » du site (< 1 h pour CANDHIS). **À aligner.**
- **Design** : l'application n'a pas encore reçu la direction Premium Ocean (palette « Nuit » d'origine).
- **Fonctionnalités** : pas d'alertes, pas de widgets. Elles sont prévues après la vraie version installée, et ce sont elles qui justifient une application.
- **Android** : pour une vraie version Android, il faudra installer `expo-system-ui` (mode sombre automatique), avec l'accord du porteur.
- **Webcams** : liens externes seulement, comme sur le site.
