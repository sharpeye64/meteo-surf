# Application iOS : audit et vision (chantier #8)

_27/11/2026, Claude Code, branche `appli-experience` (repère `avant-appli-experience`), à partir de `main` qui contient la PR #22. Rien n'est développé dans l'interface : ce document et les maquettes servent à valider la direction avant toute modification majeure._

**Maquettes iPhone 15 Pro** : canevas « Houlalah iOS — vision » (lien donné au porteur). Sept écrans, en clair et en sombre, tous construits avec les **valeurs réelles** de la génération du 27/11 à 19 h 47.

## 1. Audit de l'existant

L'appli fonctionne et ses règles métier sont justes depuis la PR #22. Les problèmes sont surtout de **navigation**, d'**usage quotidien** et de **performance de la carte**.

### Navigation (le plus pénalisant)
| # | Constat | Effet pour le surfeur |
|---|---|---|
| N1 | Pile d'écrans maison, sans transition native ni **retour par glissement** (geste iOS) | l'appli « ne fait pas iPhone » ; retour seulement par le bouton ‹ |
| N2 | Ouvrir un spot depuis la carte **démonte la carte** ; au retour, elle repart sur toute la côte | on perd sa zone à chaque spot consulté : la carte ne sert pas à comparer |
| N3 | Changer d'onglet vide la pile et recrée l'écran (la carte se recharge) | lenteur, perte de contexte |
| N4 | Aucun **lien profond** (le schéma `houlalah://` est déclaré mais pas géré) | bloque les futurs widgets, alertes et partages, qui doivent ouvrir un spot précis |
| N5 | Quatre onglets qui se recouvrent (« Spots » contient déjà les favoris, « Favoris » les répète) | hésitation, aucun écran n'est le réflexe |

### Carte
| # | Constat | Effet |
|---|---|---|
| C1 | L'étiquette dit « Houle à 21 h » (heure actuelle), mais les valeurs sont celles de l'heure de **génération** de l'index | décalage silencieux quand l'index a quelques heures (hors connexion, robot en retard) |
| C2 | Pas de choix du moment (demain matin…) ni de la donnée (période, vent) : seulement la houle « maintenant » | la carte n'aide pas à décider pour demain |
| C3 | 236 repères dessinés en vues React ; leur clé change avec le zoom (remontage) ; les bouées animées redessinent leur image en continu (`tracksViewChanges`) | saccades au zoom, batterie |
| C4 | Pas de géolocalisation ni de mémoire de la dernière zone | il faut chercher sa côte à chaque ouverture |
| C5 | Satellite par défaut | joli mais peu lisible pour lire des pastilles colorées |

### Usage quotidien, réseau, finition
| # | Constat | Effet |
|---|---|---|
| U1 | Les fiches des favoris ne sont pas préchargées | sur la côte sans réseau, un favori jamais ouvert n'a rien à montrer |
| U2 | Le rafraîchissement à la minute redessine **tout** l'arbre, carte comprise | travail inutile toutes les minutes |
| U3 | « Réduire les animations » (iOS) n'est pas respecté (pastilles qui clignotent, ondes) | accessibilité |
| U4 | Palette de l'appli : l'ancienne « Nuit », pas Premium Ocean (sable `#F3EFE6`, nuit `#0B1B26`, or des mesures) | l'appli ne ressemble pas encore au site |
| U5 | Aucun retour haptique ; pas de partage ; pas de préférences | — |
| U6 | Données légères : index 65 Ko (12 Ko compressés), fiche 2,5 Ko, bouée 1,3 Ko | **pas un problème** : on peut précharger sans crainte |

Déjà réglé par la PR #22 (pas à refaire) : fraîcheur selon la cadence, bouée de référence, vent, copie hors connexion protégée, reprise réseau des fiches, écran sans bouée.

## 2. Vision

**Une appli que le surfeur ouvre trois fois par jour, qui répond en trois secondes, et qui montre toujours d'où vient chaque chiffre.**

Ce n'est pas le site en petit. Le site sert à **explorer** (une grande frise, sept jours, les modèles). L'appli sert à **décider vite**, là où l'on est : au réveil, avant de prendre la voiture, sur le parking.

**Les arbitrages proposés :**
1. **La carte est l'accueil.** Elle est l'identité de Houlalah et le seul écran qui répond d'un coup d'œil à « où est-ce que ça marche autour de moi ? ».
2. **Rien ne quitte la carte sans raison.** Spots et bouées s'ouvrent dans un **panneau natif** qui glisse par-dessus (iOS : trois crans). La carte garde sa zone, son zoom et son moment.
3. **Le temps est un réglage de la carte**, pas un écran : « Maintenant · Demain 7 h · Demain 12 h · Dim. 7 h » en pastilles, plus une réglette pour l'heure exacte. La donnée affichée (houle, période, vent) est un sélecteur à trois positions.
4. **La mesure est en or, toujours à côté de la prévision.** Elle ne vaut que pour maintenant : sur un moment futur, la bouée passe en retrait avec la mention « une mesure ne vaut que pour le moment présent ».
5. **Pas de note, pas de classement.** La comparaison met les données côte à côte ; le surfeur décide (D2, D3).
6. **Trois onglets au lieu de quatre** : Carte, Ma côte, Bouées. « Spots » disparaît (la recherche est sur la carte), « Favoris » devient « Ma côte ».

**Ce que je challenge :**
- Le satellite par défaut : un fond **plan « sable et mer »** rend les pastilles plus lisibles. Le satellite reste à un toucher.
- La liste de toute la côte par régions, sur l'accueil : elle double la carte. Elle reste accessible par la recherche.
- Les quatre carrés de la fiche spot (houle, vent, eau, soleil) : le soleil et l'eau passent sous la frise. En haut, il ne reste que trois colonnes, houle, vent et marée, comme sur le site.
- La « mini-frise » de l'accueil : elle est remplacée par « Demain 7 h » sur chaque favori. C'est la question qu'on se pose le soir.

## 3. Architecture de navigation recommandée

```
Onglets (3) : Carte · Ma côte · Bouées
  Carte (accueil)
    ├─ recherche flottante (spot, bouée, ville) + me localiser
    ├─ sélecteur Houle | Période | Vent  ·  moment (pastilles + réglette)
    └─ panneau natif à trois crans (petit / moyen / grand)
         ├─ « Autour de vous » (spots proches + bouée de référence)
         ├─ fiche d'un spot  ─┐  ouverts DANS le panneau,
         └─ fiche d'une bouée ┘  la carte reste derrière
  Ma côte : favoris (maintenant + demain 7 h), « Comparer demain matin », bouées de ma côte, préférences
  Bouées : liste par zone + mesuré / prévu
Liens profonds : houlalah://spot/<slug>, houlalah://bouee/<slug>  (widgets, alertes, partage)
```

**Technique** : passer à **Expo Router**, recommandé par Expo et attendu par `app/AGENTS.md`. Il apporte :
- la pile native : retour par glissement, transitions iOS ;
- les panneaux natifs à crans (`presentation: 'formSheet'`) ;
- les liens profonds automatiques ;
- les onglets.

La pile maison actuelle ne fait rien de tout cela. La migration ne touche que la navigation : les écrans, les règles (`rules.ts`), le cache et les données restent. Tout fonctionne dans **Expo Go**, vérifié dans la documentation du SDK 58 : `react-native-screens`, `gesture-handler`, `reanimated`, haptique, localisation, `netinfo`, effet « Liquid Glass » d'iOS 26.

## 4. Les écrans (maquettes)

| Maquette | Ce qu'elle montre | Choix |
|---|---|---|
| **1 · Carte, le réflexe du matin** | votre position, pastilles de houle, bouée Cap Ferret en direct, panneau « Autour de vous » | trois réponses sans toucher l'écran : la houle autour de soi, le vent (offshore / onshore en couleur), la mesure réelle |
| **1b · Carte, mode sombre** | « Période » et « Demain 7 h » choisis ; la bouée passe en retrait | le moment et la donnée sont des réglages de la carte ; la mesure n'est pas présentée comme une prévision |
| **2 · Un spot sans quitter la carte** | panneau au grand cran sur Lacanau : houle, vent, marée ; frise 6 h – 12 h ; bouée de référence | le spot choisi reste visible en haut ; la frise reprend les couleurs du site |
| **3 · Demain matin : comparer** | quatre favoris, 6 h → 12 h, houle et période heure par heure, vent | aucun classement ; la marée commune est en tête |
| **4 · La bouée confirme-t-elle ?** | mesuré (or) contre prévu (pointillés) sur 48 h, record, moyenne | la vérification, notre différence (D4), en un seul graphique |
| **5 · Ma côte** | favoris : maintenant et demain 7 h ; bouées de ma côte | cet écran préfigure les widgets (mêmes blocs) |
| **6 · Réseau faible** | données reçues il y a 2 h 23, prévision de 22 h, aucune pastille verte | honnêteté : on dit l'âge, on ne prétend jamais au direct |

## 5. Les parcours

| Situation | Parcours |
|---|---|
| **Je me réveille** | j'ouvre l'appli : la carte est centrée sur ma dernière zone (ou ma position), en « Maintenant ». Le panneau « Autour de vous » donne mes 2 ou 3 spots et la bouée de référence. Zéro toucher. |
| **Je compare avant de prendre la voiture** | Ma côte → « Comparer demain matin » (ou le moment choisi), ou bien la carte en « Vent » pour voir où c'est offshore. |
| **J'anticipe demain matin** | carte → « Demain 7 h » : toutes les pastilles basculent. Toucher un spot ouvre sa fiche au même moment. |
| **La bouée confirme-t-elle ?** | depuis un spot : « Bouée de référence » → mesuré contre prévu sur 48 h, à la bouée et pas sur le spot. |
| **Mauvaise connexion sur la côte** | tout reste lisible depuis le cache, avec un bandeau « reçu il y a… ». Les fiches des favoris sont préchargées (U1). Aucune pastille verte n'est montrée sans mesure fraîche. Mise à jour automatique au retour du réseau. |

## 6. Gestes, haptique, mouvement

- **Panneau** : glisser entre les crans ; toucher la carte le réduit ; un retour haptique léger à chaque cran.
- **Moment** : réglette horaire avec un petit cran haptique à chaque heure. Les pastilles changent de valeur en fondu, sans tout redessiner.
- **Favori** : appui long sur un repère de la carte pour l'ajouter à Ma côte (haptique de confirmation).
- **Mouvement** : seules restent les animations déjà autorisées (pastille verte, halo des bouées en direct). Tout s'arrête avec « Réduire les animations ».
- **Une main** : les commandes fréquentes sont en bas (panneau, moment, onglets) ; la recherche en haut s'ouvre aussi en tirant le panneau.
- **Barre d'onglets en bulle** (demande du porteur, 28/11/2026) : une pilule flottante en verre dépoli, posée au-dessus du contenu à 24 px du bas. L'onglet actif est marqué par une bulle dorée qui glisse d'un onglet à l'autre. En sombre : verre nuit. Sur iOS 26, elle utilisera l'effet « Liquid Glass » natif (`expo-glass-effect`, inclus dans Expo Go), avec un repli en verre dépoli.

## 7. Données nécessaires

| Besoin | Source | Statut |
|---|---|---|
| Valeurs de tous les spots à un moment futur (carte « Demain 7 h ») | **index cartographique compact** du site (PR #21 de René, `home-index.json` : houle, période, direction, vent, direction du vent, heure par heure) | à réutiliser dès sa fusion, **sans toucher au robot ni au site**. En attendant : « Maintenant » seulement |
| Correction de C1 (heure réelle des valeurs) | `now.t` déjà présent dans l'index | côté appli seulement |
| Préchargement hors connexion | fichiers existants (`spots/`, `bouees/`) | côté appli seulement |

## 8. Plan de développement proposé (après validation)

1. **Socle** (aucun changement visuel) :
   - Expo Router : pile native, onglets, liens profonds ;
   - carte gardée en vie ;
   - repères stables et légers (C3) ;
   - mémoire de la dernière zone ;
   - préchargement des favoris ;
   - rafraîchissement ciblé (U2) ;
   - « Réduire les animations ».
2. **Carte d'accueil** : panneau à crans, « Autour de vous », sélecteur Houle / Période / Vent, géolocalisation, fond plan par défaut, correction C1.
3. **Fiches dans le panneau** : spot et bouée ; palette Premium Ocean en clair et en sombre.
4. **Ma côte** et « Comparer demain matin ».
5. **Moments futurs sur la carte**, dès que l'index compact est disponible.

Chaque étape est vérifiée sur iPhone avec Expo Go (`tester-sur-telephone.ps1`), et `npx tsc --noEmit` passe.

## 9. Anticiper sans développer

- **Widgets iOS** (`expo-widgets`, version installable requise) : les blocs de « Ma côte » sont les futurs widgets. Ils doivent être calculés par des fonctions pures, sans état d'écran (comme `rules.ts`).
- **Alertes de houle** : liens profonds `houlalah://spot/<slug>` ; préférences rangées sous une clé versionnée ; rien ne suppose une connexion permanente.
- **Préférences** : un seul objet versionné (fond de carte, donnée affichée, dernière zone, favoris).
- **Partage** : le bouton existe sur la fiche ; il partagera le lien public `houlalah.fr/spots/<slug>/`, qui a déjà son image.

## 10. Décisions à valider par le porteur

1. La **carte comme accueil**, et **trois onglets** (Carte, Ma côte, Bouées).
2. Le **panneau à crans** à la place des pages pleines pour les spots et les bouées.
3. Le **fond plan** par défaut (satellite à un toucher).
4. La **migration vers Expo Router** (socle technique, sans changement visuel).
5. La **palette Premium Ocean** dans l'appli, en clair et en sombre.
6. La **dépendance à l'index compact de René** pour les moments futurs sur la carte.

## 11. Itération 3 (28/11/2026) : carte, fiche spot, comparateur

Validé par le porteur :
- la carte en accueil ;
- trois onglets : Carte, Ma côte, Bouées ;
- la barre en pilule flottante ;
- le fond plan par défaut ;
- Premium Ocean en clair et en sombre ;
- Expo Router.

Les maquettes de cette itération sont dans le canevas « Houlalah iOS — itération 3 ». Elles reprennent les valeurs réelles de la génération du 28/11 à 10 h 36.

### Réponse aux deux revues de ChatGPT (PR #23)
| Point | Position | Ce qui change |
|---|---|---|
| Panneau permanent contraire à D13 | **D'accord.** | Carte seule. La fiche d'un spot ou d'une bouée est un panneau **à la demande**, ouvert par **un seul toucher** sur le repère. « Autour de vous » n'apparaît qu'après « Me localiser » et se referme (variante A′). |
| Or pour l'onglet actif | **D'accord**, l'or est réservé aux mesures. | Bulle active bleu nuit (crème en sombre). |
| D5 sur la carte | **D'accord pour la houle.** Les repères portent **toujours** hauteur, période et direction. **Nuance** : en mode Vent, le repère montre le vent et l'orientation ; ajouter la houle surchargerait la carte. La fiche, ouverte en un toucher, rend les trois ensemble. | Repères « ↗ 2,2 14 s ». |
| « Comparer demain matin » | **D'accord.** | « Comparer · dim. 7 h » ; moment libre (jour + heure). |
| Fuseaux dans la comparaison | **D'accord** : un instant absolu, l'heure locale affichée pour chaque spot. | Supertubos : « 6 h à Lisbonne ». Marée affichée par port, jamais supposée commune. |
| Géolocalisation | **D'accord** : demandée seulement au toucher de « Me localiser ». Sans autorisation ni favori : dernière zone, sinon toute la côte. | Aucun blocage au premier lancement. |
| Liste de tous les spots et régions | **D'accord**, sans quatrième onglet. | Recherche vide = « Parcourir par pays et région ». |
| Courbe prévu / mesuré de la bouée | **D'accord sur la provenance.** **Nuance** : la vraie comparaison « prévision faite avant la mesure » sera possible avec l'archive v2 (#1), après 30 jours. | Légende : « prévision actuelle au point le plus proche (spot Le Cap Ferret) ». |
| Expo Router et carte gardée en vie | **D'accord** : prototype technique sur iPhone **avant** de migrer les écrans. | Étape 1 du plan, avec critères de réussite. |
| Dépendance à la PR #21 | **D'accord, et on va plus loin** : le comparateur n'en a pas besoin. Il ne charge que 2 à 4 fiches (environ 10 Ko). Seuls les moments futurs sur la carte en dépendent. | Socle et comparateur sans #21 ; contrat proposé ci-dessous. |

### Les trois écrans
- **Carte** (A, recommandée) : la carte occupe tout l'écran. Les commandes sont en bas, dans la zone du pouce :
  - une barre « Houle · Période · Vent » et « Maint. sam. 10 h » ;
  - le bouton « Me localiser » à droite ;
  - la pilule d'onglets.

  Un toucher sur un repère ouvre sa fiche. Le moment (A″) s'ouvre dans la même barre : jours, réglette des heures avec la nuit grisée, lever et coucher du soleil. Sur un moment futur, la bouée passe en retrait.
- **Fiche spot** (B) : le panneau monte presque en haut et ne laisse voir que le repère choisi. La frise est agrandie :
  - colonnes de 46 px, cellule de houle de 50 px avec la flèche de direction ;
  - période, vent avec sa direction et un trait de couleur pour l'orientation (offshore, de côté, onshore, lisse), rafales ;
  - courbe de marée alignée sous les colonnes, heures de nuit grisées.

  Sous la frise, deux phrases **factuelles** tirées des données (houle, vent), sans conseil. Puis la bouée de référence, avec la date de sa mesure.
- **Comparateur** (C) : le moment est libre (jour + heure à une main) et les spots aussi, favoris ou non (« + Spot »).
  - Une section par donnée : houle et direction, période, vent et marée.
  - Pour la houle et la période, des barres à **la même échelle, partant de zéro** (les écarts ne sont pas grossis), et l'écart avec le premier spot.
  - Pas de classement.

### Contrat de données pour les moments futurs (à discuter avec ChatGPT, PR #21)
Proposition : un **seul** fichier compact, servi au site et à l'appli. La forme de `home-index.json` (v1) est complétée de ce dont l'appli a besoin :
```
{ "v": 2, "generated": "<ISO avec décalage>", "step_h": 1,
  "times": [["<t0 ISO avec décalage>", <n heures>], ...],      // axes partagés (instants exacts)
  "columns": ["H", "T", "D", "v", "wd"],                         // houle m, période s, direction °, vent km/h, direction du vent °
  "spots": [{ "slug", "name", "tz", "time": <indice d'axe>, "rows": [[H, T, D, v, wd] | null, ...] }] }
```
- Identifiant stable = `slug`, le même que `data/app` ; `null` = valeur absente.
- L'appli ne l'utilise que si `generated` est égal ou plus récent que celui de son index ; sinon, repli sur « Maintenant ».
- Écriture atomique ; version testée par les deux clients.

**Mesure à faire avant de décider** : le poids compressé de ce fichier, comparé aux fiches, sur une connexion lente. Si le site garde `home-index.json` v1, l'appli peut aussi lire ce v1 à travers un petit adaptateur côté appli. Les deux options n'imposent aucun changement au moteur de prévision.

### Tests prévus (en plus des tests de logique existants)
| Parcours | Vérification sur iPhone (Expo Go) |
|---|---|
| Réveil | ouverture sur la dernière zone ; un toucher sur un repère ouvre la fiche ; temps d'ouverture mesuré |
| Comparer | ajout d'un spot hors favoris ; changement d'heure ; Portugal à l'heure de Lisbonne |
| Demain matin | moment futur sur la carte (après le contrat) ; bouée en retrait |
| Vérifier par la bouée | courbe et légende de provenance ; fraîcheur selon la cadence |
| Réseau faible | mode avion : favoris lisibles, âge de réception ; retour du réseau |
| Accessibilité | VoiceOver (repères, frise), Dynamic Type, cibles ≥ 44 px, « Réduire les animations » |

## 12. Itération 4 (28/11/2026) : retours du test iPhone et revue technique de René

Commits `d881649` à `dd08f91` sur `appli-experience` (PR #23, brouillon). Rien n'est fusionné ni publié.

### P0 — Fraîcheur et fiabilité des données
- **Cause réelle des captures** (prévision de la veille à 19 h, aucune bouée en direct, « Aujourd'hui 27 ») : `app/tester-sur-telephone.ps1` servait les fichiers **générés sur le PC** (`web/data/app`, dernière génération le 27/11 à 19 h 47), pas ceux de houlalah.fr. La production, elle, était fraîche (générée à 11 h 47, bouées de 11 h 30). Le cache de l'appli n'est pas en cause : il passe toujours d'abord par le réseau.
  - Le script lit désormais **la production par défaut**. Avec `-Local`, il sert les fichiers du PC et affiche leur date.
  - L'option `--clear` est ajoutée, car l'adresse des données est fixée au moment de la compilation.
- **Défauts réels révélés, corrigés sans masquer le problème** :
  - La fiche appelait « Aujourd'hui » le **premier jour de la série**. Désormais, les jours partent de la vraie date à l'heure du spot, et « Aujourd'hui » / « Demain » sont calculés (`src/series.ts`).
  - **L'âge des données** (génération par le robot) s'affiche sur la carte, dans Ma côte et dans la fiche, et il est recalculé chaque minute (`Stamp.tsx`, `useDataAge`) :
    - « en retard » au-delà de 3 h ;
    - « ancienne » au-delà de 6 h ;
    - « hors connexion » quand c'est le cas.
  - La bouée de la fiche annonçait « Mesure de maintenant » pour une mesure vieille de 17 h. Elle dit désormais « Mesure en direct » ou « Dernière mesure ».
  - **Bouée de référence instable** : à âge égal, le choix dépendait de la milliseconde du calcul. Au même moment, la fiche affichait Anglet et Ma côte la Gascogne. `refBuoy` prend désormais une seule heure de référence ; à égalité, la plus proche l'emporte. **À vérifier sur le site** (`pickBuoy`, non modifié car hors périmètre).
- **Revue de René** :
  - valeur lue seulement à un **échantillon exact** (à 1 s près), sinon « heure indisponible » ;
  - jours **civils** de Paris dans le comparateur (passages à l'heure d'été et d'hiver) ;
  - pas de barre pour une valeur nulle ;
  - une comparaison vidée reste vide ;
  - graphe de la bouée : **mesuré en or, prévu en bleu nuit pointillé**, prévision coupée au cadre, provenance dite ;
  - couleurs des cartes de bouée centralisées (`buoySurface`, `measureOnBuoy`…).

### P0 — Carte
- **Trois niveaux de lecture** (`src/density.ts`, testé) :
  - **Loin** : un regroupement par région, avec le nom, le nombre de spots et la fourchette des valeurs avec l'unité. Un toucher zoome sur la région.
  - **Milieu** : des pastilles choisies pour ne pas se chevaucher (favoris d'abord, puis plus forte valeur) ; les autres spots restent des points touchables.
  - **Près** : des pastilles détaillées (nom et valeurs) ; à défaut de place, une pastille simple, puis un point.
- **Sans clignotement** :
  - le placement se calcule par palier de zoom, avec une marge de tolérance : déplacer la carte ne le recalcule pas ;
  - chaque repère garde une clé stable et ne bouge pas, seul son aspect change ;
  - les repères sont figés et ne se redessinent que pendant 0,7 s après un changement d'aspect.
- **Bouées** : leurs points sont réservés en premier et ne sont jamais cachés par un spot. Leur étiquette or ne s'affiche que s'il reste de la place, car les spots sont l'objet de l'écran.
- **Unités** partout (m, s, km/h).
- **Fond de carte (position défendue)** : plan épuré par défaut, où les pastilles sont plus lisibles ; satellite à un toucher. La clé mémorisée est renouvelée pour que tout le monde reparte sur le plan.
- **Barres du bas** : une seule rangée (Houle / Période / Vent et « Me localiser ») au lieu de deux étages ; la pilule d'onglets passe de 66 à 60 px.
- **Mesuré sur les vraies données** (iPhone de 393 px de large) :
  - côte entière : 12 regroupements, dont 3 réduits ;
  - Landes et Pays basque (niveau milieu) : 56 spots, dont 4 en pastille et 52 en point ;
  - Hossegor (niveau près) : 17 spots, dont 4 pastilles détaillées, 1 pastille simple et 12 points.
  - **Position défendue** : au niveau milieu, peu de pastilles mais lisibles, plutôt que beaucoup qui se chevauchent. Le détail vient en zoomant.

### P1 — Ma côte
- Tableau de bord : pour chaque favori, la prévision de l'heure, une **mini-frise des 48 h** et la dernière mesure de sa bouée avec son âge.
  - La mini-frise compte une colonne toutes les 3 h : barre de houle (de 0 à 3 m), filet d'orientation du vent, jours marqués.
- « + Ajouter un spot » ouvre la recherche en mode favori. « Comparer » est en haut de l'écran.
- **Aucune requête en plus** : une fiche reste partagée pendant 10 min entre le préchargement, Ma côte et le comparateur (`loadSheetShared`).
- **Non fait** : l'ordre personnalisable des favoris (remarque de René). Je le propose pour l'itération suivante.

### P1 — Fiche spot
- Sélecteur de jours plus compact, avec la légende « Houle la plus haute de 6 h à 21 h, en mètres ».
- Heures de nuit lisibles : bande discrète et lune, valeurs à plein contraste. Avant, la colonne était délavée à 42 %.
- La marée du lendemain est dite comme telle.
- Le panneau se déploie en plein écran (grand cran iOS).

### P2 — Bouées
- La fraîcheur se voit d'un coup d'œil :
  - en direct : feu vert, mention « en direct », pastille or ;
  - ancienne : pastille neutre, âge en couleur d'avertissement.
- Unités dans les pastilles.
- Fond sable conservé : il est de la famille de l'or, donc de la mesure.

### Tests
- `tests/heures_app.test.mjs`, dans 4 fuseaux : échantillon exact, valeurs avant et après la série, minutes décalées, 25/10 et 29/03, Paris et Lisbonne, jours civils, âge des données.
- `tests/regles_app.test.mjs` : niveaux de la carte, marge de tolérance, collisions, obstacles, repli, regroupements.
- Vérifications : `tsc`, `expo-doctor`, `tests.test_regles`, `tests.test_offline`.
- Aperçu web au format iPhone : Ma côte, fiche (jours, nuit, avertissement), bouées, comparateur.

### Limites
- **Non vérifié sur iPhone** :
  - le rendu de la carte : regroupements, absence de clignotement, fluidité avec 236 repères ;
  - le grand cran du panneau ;
  - VoiceOver.
- La carte ne s'affiche pas dans l'aperçu web : son placement n'a été vérifié que par le calcul.
