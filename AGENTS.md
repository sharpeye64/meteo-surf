# Règles communes aux agents IA — Houlalah

Ces règles s'appliquent à **tous** les agents : Claude Code, ChatGPT, ou tout autre agent. Avant de proposer quoi que ce soit, lire [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md), [docs/HANDOFF.md](docs/HANDOFF.md) et [docs/DECISIONS.md](docs/DECISIONS.md).

## Rôles

- **Porteur du projet** : il décide. Il n'est pas développeur : on lui écrit en français, simplement, une étape à la fois.
- **Claude Code** : architecte et développeur. Il implémente, teste et documente.
- **ChatGPT** : Product Manager, UX/UI, stratégie, analyse SEO et relecture technique. Il propose ; il n'implémente pas directement en production.

## Règles absolues

1. **Production** : **ne jamais pousser sur `main`** (ce qui publie houlalah.fr) sans un « Oui, publie » explicite du porteur.
2. **Décisions produit** : toute décision produit importante est soumise à la validation du porteur.
3. **Branches de test** : travailler sur une branche par chantier, avec un tag `avant-…` avant un gros chantier.
4. **Secrets** : aucun secret (clé API, jeton, mot de passe, identifiant sensible) dans le dépôt, la documentation, les issues ou les messages. Les secrets vivent dans GitHub → Settings → Secrets (`METEOFRANCE_APIKEY`).
5. **Données** : aucune donnée inventée. Pas de valeur météo modifiée artificiellement, pas de caractéristique de spot inventée.
6. **Choix produit déjà tranchés** : pas de note ou score de surf, pas d'étoiles, pas de « créneau favorable » automatique, pas de recommandation « va surfer maintenant ». Les raisons sont dans [docs/DECISIONS.md](docs/DECISIONS.md).
7. **Mesures des bouées** : elles ne sont jamais présentées comme la taille des vagues sur un spot. Toujours dire « à la bouée » ou « au large », et toujours montrer la période avec la hauteur.
8. **Fraîcheur des bouées** : « en direct » et la pastille verte seulement si la mesure le justifie, selon la cadence de chaque station (voir [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)).
9. **Webcams** : des liens sortants uniquement, jamais d'intégration.
10. **Direction artistique Premium Ocean** : on la conserve. Les finitions sont possibles, pas de refonte sans demande du porteur.
11. **Téléchargements, comptes, paiements** : rien sans l'accord explicite du porteur.

## Façon de travailler

- **Propositions** : une **issue GitHub** par proposition (voir [docs/COLLABORATION.md](docs/COLLABORATION.md)).
- **Implémentation** : sur une branche de test. On vérifie dans un navigateur, sur ordinateur et sur téléphone. `python -m tests.test_offline` doit rester vert (il n'écrit plus dans `web/`). Pour un aperçu local avec de vraies données, voir HANDOFF.
- **Commits** : explicites, en français, qui disent ce qui change et pourquoi.
- **Documentation** : après chaque évolution significative, mettre à jour le ou les documents de `docs/` concernés, ainsi que [docs/CHANGELOG.md](docs/CHANGELOG.md) et [docs/HANDOFF.md](docs/HANDOFF.md).
- **Avant de proposer** : vérifier dans [docs/DECISIONS.md](docs/DECISIONS.md) que l'idée n'a pas déjà été testée et écartée.

## Pièges techniques connus

- **`web/index.html`** est un seul gros fichier. L'ancien CSS a des classes génériques (`.live`, `.hl`, `.mk`, `.old`…) qui cassent le nouveau code : utiliser les préfixes `pv-` (prévisions) et `ho-` (accueil).
- **Tests du robot** : `tests.test_offline` écrit dans un dossier temporaire, jamais dans `web/`, et marque tout ce qu'il produit comme « test ». `tests.simulate_pannes` et `tests.panne_bout_en_bout` vérifient que le contrôle de publication (`tools/check_site.py`) refuse un site abîmé. Les trois tournent dans GitHub Actions (job `surete`), sans réseau. Voir [docs/securisation-publication.md](docs/securisation-publication.md).
- **Secrets** : toute erreur écrite dans un fichier publié ou dans les journaux passe par `pipeline/safe.py` (clés, en-têtes, identifiants et paramètres d'adresse masqués).
- **Fuseau horaire** : le robot GitHub tourne en UTC, alors que toutes les heures de données sont en heure de Paris. Utiliser `seo.paris_now()`.
- **Application mobile** : lire [app/AGENTS.md](app/AGENTS.md) (Expo SDK 58 : ne pas se fier à sa mémoire).
