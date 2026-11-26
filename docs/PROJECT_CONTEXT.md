# Houlalah — contexte du projet

> **À lire en premier** par tout agent ou contributeur. Pour l'état du jour, voir [HANDOFF.md](HANDOFF.md).

## En une phrase

Houlalah (houlalah.fr) donne des prévisions surf pour **214 spots, de la Bretagne au Portugal**, **vérifiées par 22 bouées de mesure en mer**. La différence avec les autres sites : on montre ce que les modèles annoncent **et** ce que la mer mesure vraiment, avec la fraîcheur de chaque mesure.

## Vision et positionnement

- **Public visé** : le **surfeur confirmé** du Sud-Ouest (puis de toute la façade atlantique), qui sait lire une houle et veut se faire **sa propre idée**. Il ne veut pas qu'un site lui dise « c'est bon, vas-y ». Il veut des données justes, claires et vérifiables.
- **Promesse** : « La houle prévue, vérifiée par les bouées. » Fiabilité affichée (accord des modèles, écart mesuré entre prévision et bouée, âge des mesures) plutôt qu'avis subjectif.
- **Concurrents de référence** : Yadusurf, Surf-Forecast, Windy, Allosurf, surf-report. Houlalah se distingue par :
  1. la comparaison de plusieurs modèles ;
  2. les mesures réelles des bouées au premier plan ;
  3. l'honnêteté sur la fraîcheur et les limites ;
  4. une identité graphique soignée.
- **Ce que Houlalah ne fait pas** : pas de note de surf, pas d'étoiles, pas de « créneau favorable » automatique, pas de recommandation « va surfer maintenant ». Les raisons sont dans [DECISIONS.md](DECISIONS.md).

## Historique (résumé)

| Période (2026) | Étape |
|---|---|
| Début novembre | Prototype « météo surf » : robot Python + page statique, océan animé en WebGL. Nom choisi : **Houlalah** (logo fourni par le porteur du projet) |
| 6–9 nov. | Bouée Gascogne (Copernicus, puis API Météo-France), bouées CANDHIS, archive « prévision contre réalité », marées harmoniques REFMAR |
| 9–18 nov. | Pages SEO (spots, régions, bouées), accueil « carte de la côte », application mobile Expo (publiée sur `main` le 18/11, pas sur les stores) |
| 18–25 nov. | Extension à 214 spots et 22 bouées (Espagne, Portugal), bouées muettes, règles de bouée de référence |
| 26 nov. | Refonte des pages de prévisions : V2, V3, trois directions artistiques, choix de **Premium Ocean** (publié) ; nouvel accueil cartographique Premium Ocean (publié) ; audit et premier lot SEO (publié) |

Le détail est dans [CHANGELOG.md](CHANGELOG.md).

## État actuel (fin novembre 2026)

- **Site en production** sur houlalah.fr : accueil cartographique, pages de prévisions Premium Ocean, pages SEO de spots, de régions et de bouées.
- **Application mobile** : fonctionnelle en développement (Expo Go). Pas encore de compte Apple développeur, ni de publication sur les stores.
- **Audience** (Search Console, 26/11) : 204 pages indexées, 831 impressions sur 7 jours, 0 clic, position moyenne 31,4. Les requêtes portent surtout sur les **bouées et houlographes** (Anglet, Cap Ferret, Plateau du Four, Pierres Noires).
- **Statut** : prototype **non commercial**. Les données de prévision viennent de l'API gratuite d'Open-Meteo, réservée à un usage non commercial (voir [DATA_SOURCES.md](DATA_SOURCES.md)).

## Le porteur du projet

- Il n'est pas développeur. Les agents lui expliquent les choses **simplement, en français, une étape à la fois**.
- **Toute décision produit importante et toute mise en production passent par sa validation explicite** (« Oui, publie »). Voir [AGENTS.md](../AGENTS.md).

## Carte de la documentation

| Document | Contenu |
|---|---|
| [../AGENTS.md](../AGENTS.md) | Règles communes à tous les agents IA |
| [HANDOFF.md](HANDOFF.md) | État du jour, derniers changements, problèmes ouverts, prochaines étapes |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Stack, flux de données, robot, hébergement, environnements, coûts |
| [DATA_SOURCES.md](DATA_SOURCES.md) | Sources, modèles, licences, fréquences, méthodes de calcul |
| [PRODUCT.md](PRODUCT.md) | Fonctionnalités, règles métier, expérience utilisateur |
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Direction artistique Premium Ocean, composants, règles UX/UI |
| [MOBILE_APP.md](MOBILE_APP.md) | L'application Expo |
| [SEO.md](SEO.md) | Stratégie, audits, actions, suivi |
| [DECISIONS.md](DECISIONS.md) | Décisions, raisons, alternatives écartées (à lire avant de proposer) |
| [ROADMAP.md](ROADMAP.md) | Fait, en cours, envisagé |
| [CHANGELOG.md](CHANGELOG.md) | Historique des évolutions |
| [COLLABORATION.md](COLLABORATION.md) | Processus de travail entre le porteur, Claude Code et ChatGPT |
| [ONBOARDING_CHATGPT.md](ONBOARDING_CHATGPT.md) | Synthèse d'entrée pour ChatGPT |
| [../CLAUDE.md](../CLAUDE.md) | Carnet de bord détaillé de Claude Code (historique technique fin, à garder) |
