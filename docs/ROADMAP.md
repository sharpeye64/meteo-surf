# Roadmap

Statuts : ✅ fait · 🔧 en cours · 💡 envisagé (rien n'est lancé sans validation du porteur).

## ✅ Fait

- **Robot horaire** :
  - 5 modèles de vagues, dont MARC, mélangés et corrigés par la bouée Gascogne ;
  - 4 modèles de vent ;
  - marées harmoniques et coefficient ;
  - archive prévision / mesure.
- **22 bouées** (7 houlographes CANDHIS, Météo-France 62001, 14 Copernicus) : fraîcheur selon la cadence de chaque station, gestion des bouées muettes.
- **214 spots** de la Bretagne au Portugal, avec leur bouée de référence.
- **Site Premium Ocean** :
  - pages de prévisions (frise pleine largeur sur téléphone, marée, modèles, détail de la houle, 7 jours) ;
  - accueil cartographique (houle, période, vent, choix du jour et de l'heure, bouées vivantes).
- **SEO** : pages de spots, régions et bouées ; premier lot de corrections (houlographes, Dataset, heure par heure, marées, canonique de `/?spot=`).
- **Application mobile Expo** : onglets Spots, Carte, Bouées, Favoris ; mode sombre ; données allégées.
- **PWA** (mode hors ligne) et partage (images Open Graph).

## 🔧 En cours

- **Documentation commune** pour plusieurs agents : branche `docs-onboarding`.
- **Suivi Search Console** du lot SEO, 2 à 8 semaines (`docs/seo-suivi-search-console.md`).

## 💡 Envisagé — court terme

- **Spots partagés** : traiter les 21 groupes de spots à prévision partagée, **après l'export Search Console** (faits réels seulement).
- **Application** : aligner sa règle de fraîcheur des bouées sur celle du site.
- **Nettoyage de `web/index.html`** : fonctions `*_v1`, directions B et C, ancien océan WebGL.
- **Poids** : alléger les données chargées par l'accueil (résumé compact, détail à la demande).
- **Maillage** : « bouées de la zone » sur les pages de spots.
- **Frise du site** : marqueur « maint. » sur le créneau de l'heure en cours, au lieu de l'heure la plus proche (amélioration mineure, voir `docs/heures.md`).

## 💡 Envisagé — moyen terme

- **Fiabilité par bouée** (écart prévu / mesuré par échéance et par modèle), à partir de l'archive. Forte valeur, données déjà là.
- **Historique et records** des bouées (mois, saison).
- **« Taille au bord »** apprise par bouée côtière, après 30 jours ou plus d'archive. N'afficher qu'après validation.
- **Application** : compte Apple développeur, vraie version installée, **alertes de houle**, **widgets**, puis les stores (iOS, Android).
- **Marées** pour les spots d'Espagne et du Portugal (ports de référence et constantes).
- **API CANDHIS officielle** (jeton à demander au Cerema).
- **Calibration terrain** : `tide_offset_min`, réglages des spots.
- **Internationalisation** : espagnol, portugais puis anglais, en sous-dossiers avec `hreflang` et des gabarits traduits par une personne (voir [SEO.md](SEO.md)).
- **Statistiques publiques** de fiabilité.

## 💡 Envisagé — long terme

- **Offre « Pro »** : fiabilité détaillée, historique, alertes. Elle suppose de régler la licence des prévisions (Open-Meteo commercial, ou accès direct aux modèles).
- **Démarches légales** : recherche d'antériorité « Houlalah » à l'INPI avant de s'y installer ; créer l'adresse contact@houlalah.fr si ce n'est pas fait.

## En réserve (ni prévu, ni rejeté)

- **Version « Light / Pro »** du site.
- **« Créneau favorable »**, s'il est un jour repensé avec des réglages validés sur le terrain (aujourd'hui écarté, voir [DECISIONS.md](DECISIONS.md) D3).
