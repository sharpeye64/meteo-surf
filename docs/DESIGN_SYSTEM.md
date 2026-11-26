# Design system : Premium Ocean

**Retenue le 26/11/2026** comme direction de référence de tout Houlalah : site, pages SEO et, à terme, l'application. **On ne change plus la direction générale.** On ne fait que des finitions, et seulement à la demande du porteur.

## Intention

Une **nuit marine** élégante qui s'ouvre sur un papier sable chaleureux. Du minimalisme avec du caractère. Une carte vivante, mais jamais agitée. Une interface riche, mais jamais encombrée.

## Couleurs

| Rôle | Valeur | Usage |
|---|---|---|
| Bleu nuit | `#0B1B26` | en-têtes, panneaux, boutons principaux, **prévisions** |
| Sable (fond) | `#F3EFE6` (pages), `#ECE5D5` (terres de la carte) | fond général |
| Crème (cartes) | `#FFFDF8` | cartes, tableaux, panneaux clairs |
| **Or** | `#F2C66B` sur nuit, `#8A6418` à `#7A5410` sur clair | **mesures réelles des bouées uniquement** (plus l'accent d'accroche « vérifiée par les bouées ») |
| Vert « en direct » | `#12925A` sur clair, `#2FC48A` / `#4BE3A4` sur nuit | pastille animée d'une mesure réellement fraîche, **rien d'autre** |
| Mer de la carte | `#B4CCD8` | bleu désaturé (pas gris) |
| Texte secondaire | `#38474F`, `#5D6A70` | |
| Orientation du vent | offshore `#1F8A7C`, side `#5B6B75`, onshore `#C0582F` | texte et pastille de l'orientation |

**Échelles du tableau et des marqueurs** (`PV_PAL.a`) :

| Donnée | Teintes |
|---|---|
| Houle | du bleu clair (0 m) au bleu nuit (5 m) |
| Période | du sable (5 s) au vert profond (17 s) |
| Vent | du bleu pâle au rouge orangé (42 km/h) |

## Typographie

- **Unbounded** (700–800) : titres, grands chiffres, valeurs des marqueurs et des bouées. Lettrage serré (−0,04 em).
- **Manrope** (500–800) : texte, étiquettes, boutons.
- **Petites étiquettes** : capitales espacées (0,1 em), 10,5 à 11,5 px.

## Motifs et matières

- **Lignes de houle** discrètes dans les en-têtes bleu nuit. Sur l'accueil, elles dérivent très lentement (deux nappes).
- **Bord en vague** entre l'en-tête nuit et la partie claire.
- **Matière** : grain très léger sur l'en-tête de l'accueil, reflets doux sur les surfaces nuit, ombres en plusieurs couches, naturelles (pas d'effet de carte « surélevée »).
- **Titres de section** soulignés d'un petit trait en forme de houle.

## Composants

- **Résumé houle / vent / bouée** : trois colonnes séparées par un filet, **sans cartes imbriquées**.
- **Tableau horaire** : cellules colorées par l'échelle ; période et direction **dans la même cellule** ; cadre de sélection qui glisse ; pastille de l'heure choisie ; info-bulle de colonne. Sur téléphone, colonne de pictogrammes de 28 px.
- **Calendrier** vertical (jour en capitales, date en grand, houle, petit trait de hauteur doré sur le jour choisi).
- **Marqueurs de carte** :

| Marqueur | Apparence |
|---|---|
| Spot | pastille colorée, contour crème, valeur et unité |
| Spot favori | petite étoile dorée |
| Spot sélectionné | anneau bleu nuit et halo qui respire |
| Groupe de spots | pastille de la valeur la plus haute, effet de pile discret, sans compteur |
| Bouée | bleu nuit et or |
| Bouée en direct | halo doré lent et pastille verte |
| Bouée récente | anneau doré, sans point |
| Bouée ancienne | sourde |
| Bouée muette | grisée |

- **Pastille de fraîcheur** : point, puis « En direct » / « il y a 12 min » / « il y a 3 h » / date.
- **Sélecteurs** (Houle / Période / Vent, jours) : pastille crème qui glisse sous le bouton actif.
- **Pictogrammes** : traits fins (1,8 px), arrondis, toujours accompagnés d'un texte ou d'une info-bulle. La période est un **chronomètre** sur l'accueil.
- **Flèches de direction** : elles pointent vers où va la houle ou le vent. Le secteur d'où ça vient est écrit à côté (« ONO »).

## Mouvement

- **Transitions** : 0,2 à 0,4 s, courbes douces, ressort léger sur les sélecteurs.
- **Animations en boucle autorisées** : la pastille verte « en direct », le halo des bouées en direct, l'anneau de sélection, la houle de l'en-tête. **Rien d'autre ne bouge en permanence.**
- **Réduction des animations** : tout s'arrête si l'appareil le demande (`prefers-reduced-motion`).

## Mode sombre

En **option** sur les pages de prévisions (bouton lune, `html[data-theme="dark"]`), clair par défaut. Il n'a été vérifié que partiellement : la barre d'onglets du bas reste claire.

## Explorations écartées

Les raisons sont dans [DECISIONS.md](DECISIONS.md).

- V1 (pages d'origine) : référence visuelle, mais vieillissante.
- V2 : trop dense, « tableau de bord SaaS ».
- V3 : trop fade.
- Direction B « Surf Editorial » (papier, filets, Instrument Serif italique) et direction C « Modern Weather » (grille pointillée, mono JetBrains Mono) : non retenues. Leur code est encore présent (`?da=b|c`), à supprimer.
- Accueil v1 Premium Ocean : panneau pleine hauteur, grande frise avec lecture, panneau inférieur en trois crans sur téléphone. Trop chargé.
- Anciennes pistes de logo redessiné : abandonnées. **Le logo est celui fourni par le porteur** (`brand/logo-source.webp`), vectorisé fidèlement, jamais redessiné.
- Décors dessinés (arbres, montagnes) dans l'ancien océan animé : jugés « cheap ».

## Captures de référence

Le dossier `captures/v2/` n'est pas suivi par git ; les captures n'existent que sur le poste du porteur. Repères git :

| Tag | Version |
|---|---|
| `avant-v2-previsions` | V1 |
| `avant-v3-previsions` | V2 |
| `avant-directions` | V3 |
| `accueil-ocean-v1` à `v4` | itérations de l'accueil |
