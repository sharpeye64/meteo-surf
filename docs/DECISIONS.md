# Décisions : quoi, pourquoi, et ce qui a été écarté

> **À lire avant toute proposition.** Si une idée figure dans « Écarté », ne la reproposez pas sans un élément nouveau. Si un élément nouveau existe, le dire explicitement et demander l'avis du porteur.
> Pour toute nouvelle décision importante, ajouter une entrée (date, décision, raisons, alternatives écartées).

## Produit

### D1 — Public visé : le surfeur confirmé
- **Décision** : on s'adresse d'abord au surfeur confirmé du Sud-Ouest, puis de toute la façade atlantique.
- **Pourquoi** :
  - il sait lire une houle (hauteur, période, direction, vent, marée) et veut **se faire sa propre idée** ;
  - les sites grand public simplifient à l'excès (notes, couleurs « bon / mauvais »), et ce public n'en veut pas ;
  - c'est une niche où la **justesse et la vérification** font la différence.
- **Écarté** : un produit débutant avec des conseils (« conditions idéales pour débuter »). Une version « Light / Pro » est une idée en réserve, non décidée.

### D2 — Pas de note, pas d'étoiles, pas de score de surf
- **Pourquoi** :
  - une note mélange des critères personnels (niveau, planche, goût) et cache la donnée ;
  - elle donne une fausse précision : nos réglages de spots n'ont jamais été validés sur le terrain ;
  - elle va à l'encontre de la promesse « vérifié ».
- Le score interne `h.score` existe encore dans le code mais **ne s'affiche pas**.
- **Écarté** : note sur 10, étoiles, « Petit / Bon / Excellent », couleurs de qualité sur la carte ou la liste.

### D3 — Pas de « créneau favorable » automatique, pas de « va surfer maintenant »
- **Pourquoi** : même raison que D2. De plus, un créneau automatique engage la responsabilité (sécurité) et se trompe souvent sans calibration locale.
- Le trait doré de la frise est désactivé (`winA=99, winB=-1`). L'idée est en réserve, à repenser plus tard avec des réglages validés.
- **Écarté** : bandeau « meilleur moment », trait ou zone colorée dans la frise, notification « c'est bon maintenant ».

### D4 — Les mesures des bouées au centre de la proposition de valeur
- **Pourquoi** :
  - les modèles se trompent ; une **mesure réelle** permet de le voir ;
  - c'est notre différence (« La houle prévue, vérifiée par les bouées ») ;
  - c'est aussi ce que Google nous renvoie : nos premières requêtes portent sur les bouées et houlographes.
- **Règles qui en découlent** :
  - **couleur dédiée (or)** ;
  - fraîcheur toujours affichée, honnête, selon la cadence de chaque station ;
  - la mesure n'est **jamais** présentée comme la taille au spot ;
  - l'archive prévision / mesure sert à afficher une fiabilité chiffrée.
- **Écarté** :
  - la mesure de bouée sur la frise horaire (essayée, retirée : confusion avec la prévision) ;
  - une « heure d'arrivée de la houle » en premier plan ;
  - une « taille au bord » affichée avant d'avoir été apprise et validée (au moins 30 jours d'archive côtière).

### D5 — La période toujours avec la hauteur, période et direction ensemble
- **Pourquoi** : à hauteur égale, une houle de 14 s arrive bien plus grosse et puissante qu'une houle de 7 s. Séparer les deux induit en erreur.
- **Écarté** : un tableau avec la période et la direction sur des lignes séparées.

### D6 — Accord des modèles plutôt que « fiabilité » en mots
- **Pourquoi** : l'accord est une donnée objective (écart entre modèles). Une pastille « Prévision fiable / incertaine » ressemblait à un avis.
- **Écarté** : la pastille de fiabilité du haut de page (retirée le 09/11).

### D7 — Pas d'équipement conseillé
- **Pourquoi** : jugé inutile par le porteur ; la précision en volume et en modèle de planche était excessive.
- **Écarté** : le bandeau « L'équipement idéal » (retiré le 09/11 ; code `GEAR` encore présent).

### D8 — Webcams en liens sortants seulement
- **Pourquoi** : conditions d'utilisation des tiers, et pas de rediffusion. On le dit quand la caméra est gérée par un tiers et peut être hors ligne.

### D9 — Bouée de référence par défaut, sans interdiction
- **Décision** : dans les Landes, Cap Ferret (nord) ou Gascogne (sud) sont proposées **par défaut**, sans retirer les autres bouées. Sainte-Barbe (abritée) n'est utilisée que pour son spot.
- **Écarté** : interdire Anglet ou les bouées espagnoles (essai annulé : le porteur voulait un défaut, pas une interdiction).

### D10 — Aucune donnée inventée, aucune différenciation artificielle
- **Pourquoi** : la confiance est le produit.
- Les 21 groupes de spots qui partagent un même point de prévision gardent des valeurs **identiques**. On ne les différencie que par des faits réels (orientation, fond, marée conseillée).
- **Écarté** : texte de remplissage, valeurs « ajustées », pages créées par variante de mot-clé.

## Design et expérience

### D11 — Direction artistique Premium Ocean (26/11/2026)
- **Pourquoi** :
  - elle combine l'immersion et la chaleur de la V1 (chiffres forts, couleurs vives du tableau) avec une identité premium (nuit marine, sable, or des mesures) ;
  - elle porte le sens : or = mesure réelle, bleu nuit = prévision ;
  - le porteur l'a jugée « nettement plus » convaincante que les deux autres directions.
- **Écarté** :
  - **V2** : trop dense, « tableau de bord SaaS » ;
  - **V3** : trop fade ;
  - **B « Surf Editorial »** : papier, serif italique, sections numérotées ;
  - **C « Modern Weather »** : grille pointillée, typographie mono ;
  - les **cartes imbriquées** dans le résumé ;
  - les décors dessinés (arbres, montagnes) dans l'ancien océan animé, jugés « cheap ».

### D12 — Accueil : la carte d'abord, le reste à la demande
- **Pourquoi** : l'accueil est un **outil d'exploration**, pas une page commerciale. La v1 de la refonte voulait tout montrer à la fois, et le porteur l'a jugée trop chargée.
- **Écarté** :
  - une page d'accueil marketing (grande photo, sections, appels à l'action génériques) ;
  - le panneau pleine hauteur ;
  - la grande frise temporelle ;
  - le **bouton de lecture automatique** des prévisions (« démo technologique », peu utile au quotidien) ;
  - les compteurs sur les groupes de marqueurs ;
  - les paragraphes d'explication permanents.

### D13 — Téléphone : la carte d'abord, sans panneau permanent
- **Pourquoi** : un panneau inférieur rétractable, utile dans une application d'itinéraire, masque en permanence les spots et oblige à le manipuler sans cesse.
- **Retenu** :
  - recherche flottante en haut ;
  - un socle compact en bas (donnée affichée et bouées, puis jour et heure) ;
  - des fiches seulement à la demande.
- **Écarté** : panneau inférieur en trois crans, barres du bas séparées.

### D14 — Bouées toujours visibles sur la carte
- **Pourquoi** : demande du porteur. Les voir disparaître au zoom était déroutant. Si une bouée tombe sur un spot, elle passe en petite pastille **sous** le spot (la valeur du spot reste lisible).

### D15 — Vert seulement pour le « vraiment en direct »
- **Pourquoi** : une pastille verte qui clignote pour une mesure de 5 h est un mensonge visuel.
- **Retenu** : le point « Maintenant » de la page de prévisions est crème, pas vert. Le vert est réservé aux bouées dont la mesure est « en direct » selon la cadence de leur station.

### D16 — Le logo est celui fourni par le porteur
- **Pourquoi** : c'est son choix d'identité. Il est vectorisé fidèlement (`tools/trace_logo.py`), **jamais redessiné**.
- **Écarté** : les pistes redessinées (rond et houles, boussole, aileron, « h » en trait).

### D17 — Hauteur du haut de page constante (ancien océan WebGL)
- **Pourquoi** : redimensionner le canvas faisait saccader l'animation. Les règles anti-blocage de l'ancien océan sont dans `CLAUDE.md`.

## Technique

### D18 — Site 100 % statique, généré par un robot GitHub Actions
- **Pourquoi** : coût nul, aucun serveur à maintenir, et suffisant pour des données rafraîchies toutes les heures.
- **Écarté** : un serveur applicatif ou une base de données, pour l'instant.

### D19 — Classes préfixées (`pv-`, `ho-`) dans `index.html`
- **Pourquoi** : l'ancien CSS contient des classes génériques (`.live`, `.hl`, `.mk`, `.old`…) qui ont cassé plusieurs fois le nouveau code.

### D20 — Canonique de `/?spot=x` vers `/spots/x/` (26/11/2026)
- **Pourquoi** :
  - l'état « application ouverte sur un spot » montre le même contenu que la page indexable du spot ;
  - depuis que l'accueil ne construit plus la page d'un spot derrière la carte, pointer vers `/` aurait été incohérent.
- **Mise en œuvre** : canonique posée par un script d'en-tête (pas de balise contradictoire dans le HTML initial), tenue à jour par l'application.
- **Écarté** : `noindex` sur ces adresses, et le maintien de la canonique vers `/`.

### D21 — Heure de Paris partout
- **Pourquoi** : toutes les sources sont converties en `Europe/Paris`. Le robot tourne en UTC, et `datetime.now()` faussait l'âge des mesures d'une heure (corrigé le 26/11).

### D22 — Pas de lecture des sites tiers non autorisés
- Allosurf, surf-report, Meteociel et Surf-Forecast (pour les mesures), ainsi que Tourisme Landes : non utilisés.
