# Application mobile (dossier `app/`)

## Statut

- **Code** : publié sur `main` le 18/11/2026.
- **Distribution** : **pas sur les stores**. Elle fonctionne en développement avec Expo Go, sur iPhone.
- **Étape suivante** (décidée avec le porteur) : prendre un compte Apple développeur (99 $/an), faire une vraie version installée sur l'iPhone, puis viser les stores.

## Stack

- **Expo SDK 58**, React Native 0.88, React 19, TypeScript.
- **Avant tout code Expo** : lire [app/AGENTS.md](../app/AGENTS.md). Il faut se référer aux docs versionnées et ajouter les paquets avec `npx expo install`.
- **Expo Router** (chantier #8, branche `appli-experience`) : routes dans `src/app/`. Trois onglets (`(tabs)/index` Carte, `macote`, `bouees`) avec la pilule flottante (`Tabs` de `expo-router/ui`), fiches `spot/[slug]` et `bouee/[slug]` en **panneau natif à crans** (`formSheet`, crans 55 % et 94 %) par-dessus la carte, `recherche` (panneau), `comparer` (écran). Liens profonds : `houlalah://spot/<slug>`, `houlalah://bouee/<slug>`.
- **État partagé** : `src/store.tsx` (index, favoris, comparaison, « réduire les animations », horloge à la minute dans un contexte séparé).
- **Modules Expo** ajoutés (tous présents dans Expo Go) : `expo-router`, `expo-location` (position demandée seulement au toucher « Me localiser »), `expo-haptics`, `react-native-screens`.
- **Carte** : `react-native-maps` (pas de carte dans l'aperçu web). Polices Unbounded et Manrope (`@expo-google-fonts`). Stockage : `@react-native-async-storage/async-storage` (favoris).
- **Vérifier** avec `npx tsc --noEmit` dans `app/`.

## Données

- **Adresse** : `EXPO_PUBLIC_DATA_URL`, par défaut `https://houlalah.fr/data/app`.
- **Fichiers** écrits par le robot (`pipeline/appdata.py`) : `index.json` (tous les spots et toutes les bouées, version allégée), `spots/<slug>.json`, `bouees/<slug>.json`.
- **Tests** : `python -m tests.test_offline` écrit dans un dossier temporaire et ne touche plus `web/data/app/`. Pour tester l'appli avec de vraies données en local, voir [HANDOFF.md](HANDOFF.md).

## Écrans

| Fichier | Rôle |
|---|---|
| `src/MapScreen.tsx` | Accueil = la carte seule : Houle / Période / Vent en bas, me localiser, recherche et fond de carte en haut, « Autour de vous » à la demande. Zone, fond et donnée mémorisés ; repères figés (`tracksViewChanges=false`) |
| `src/SpotSheet.tsx` | Fiche d'un spot : Houle / Vent / Marée en tête, jours, grande frise 6 h-21 h (nuit grisée, filet d'orientation du vent, rafales, courbe de marée), phrases factuelles, bouée de référence = mesure de maintenant ; favori et comparaison |
| `src/MaCote.tsx` | Onglet « Ma côte » : vos favoris avec la prévision de l'heure et la mesure de leur bouée ; « Comparer mes spots » |
| `src/Search.tsx` | Recherche (spots, bouées, communes, régions ; parcours par pays et région). `?pick=1` : ajoute au comparateur |
| `src/Comparer.tsx` | Comparateur, indépendant de la PR #21 : jour et heure libres (instant absolu, heure locale de chaque spot), Houle / Période / Vent et marée, sans classement |
| `src/BuoyScreens.tsx` | Onglet « Bouées » et page d'une bouée |
| `src/density.ts` | Densité de la carte : trois niveaux de lecture, collisions, regroupements par région (testé) |
| `src/series.ts` | Lecture exacte des séries, jours civils, « Aujourd'hui / Demain », âge des données (testé) |
| `src/Stamp.tsx` | Cartouche « Prévision … · calculée il y a … », avertissement si en retard ou ancienne |
| `src/TabBar.tsx` | Pilule flottante, bulle bleu nuit qui glisse (`useBarSpace()`, `barBottom`, `FLOAT_BAR_H`) |
| `src/Live.tsx` | Pastille « en direct » qui clignote |
| `src/data.ts` | Chargement, favoris, fraîcheur et bouée de référence (`freshOf`, `isLive`, `refBuoy`, `perTxt`) |
| `src/cache.ts`, `src/reload.ts`, `src/useReloaded.ts`, `src/selection.ts` | Copie hors connexion protégée contre les réponses dans le désordre, rechargement des fiches au retour au premier plan, sélection jour / heure gardée par instant (issue #4) |
| `src/rules.ts` | **Règles métier communes avec le site et le robot**, sans dépendance : fraîcheur selon la cadence, vent, secteurs, bouée de référence ([regles-communes.md](regles-communes.md)) |
| `src/theme.ts` | Deux palettes (clair, sombre) de mêmes clés ; styles via `themed(() => StyleSheet.create(...))` |

## Règles
- **Heures** (issue #2) : toujours passer par `src/time.ts` (`tMs`, `partsIn`, `placeTz`), jamais `new Date(t + ':00')` ni `getHours()` du téléphone. Affichage à l'heure du spot (champ `tz`). Voir [heures.md](heures.md).

- **Couleurs** : toujours passer par `C` (theme.ts). Une couleur en dur casse le mode sombre.
- **Mode sombre** : automatique, il suit le réglage du téléphone (`userInterfaceStyle: automatic`).
- **Règles métier** (issue #4) : fraîcheur selon la cadence de chaque station, vent, secteurs et bouée de référence passent par `src/rules.ts`. Ce sont les mêmes règles que le site, vérifiées sur les mêmes cas (`tests/regles_communes.json`). Ne jamais écrire de seuil en dur (`ageH < 2`…) dans un écran. Voir [regles-communes.md](regles-communes.md).
- **Âges** : recalculés chaque minute et au retour au premier plan. Les données sont alors redemandées (`src/store.tsx`, `useMinute()`).
- **Animations** : bulle d'onglet, feux « en direct » et ondes s'arrêtent si l'iPhone demande de réduire les animations (`reduceMotion`). Retour haptique léger sur les choix.
- **Période de Gascogne** : c'est une période moyenne, écrite « 9 s moy. ».
- **Icône et écran de démarrage** « A · Nuit » : `python -m tools.app_icons`. Ils sont invisibles dans Expo Go.

## Tester

- **Sur l'iPhone** : lancer `& "C:\Users\andre\Downloads\meteo-surf\meteo-surf\app\tester-sur-telephone.ps1"` dans un onglet du panneau Terminal.
  - Par défaut, l'appli lit les **données de production** (houlalah.fr).
  - `-Local` : elle lit les fichiers générés sur le PC (`tools/serveur_local.py web 8766`), qui peuvent avoir des heures de retard. C'était la cause des captures du 28/11.
  - Metro tourne sur le port 8082. Le PC et le téléphone doivent être sur le même Wi-Fi.
- **Aperçu web** : configuration `appli-web` (port 8081) de `.claude/launch.json`.

## Limitations et écarts connus

- **Valeurs « maintenant » de l'index** : elles sont calculées à l'heure de la génération. Hors connexion, avec un index ancien, elles datent de cette heure-là (voir [regles-communes.md](regles-communes.md), écarts connus).
- **Design** : direction Premium Ocean appliquée sur la branche `appli-experience` (non fusionnée). Les moments futurs sur la carte viendront après la stabilisation du contrat de la PR #21 (adaptateur `home-index.json` v1 côté appli).
- **Fonctionnalités** : pas d'alertes, pas de widgets. Elles sont prévues après la vraie version installée, et ce sont elles qui justifient une application.
- **Android** : pour une vraie version Android, il faudra installer `expo-system-ui` (mode sombre automatique), avec l'accord du porteur.
- **Webcams** : liens externes seulement, comme sur le site.
