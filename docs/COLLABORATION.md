# Collaboration : porteur, Claude Code, ChatGPT

L'objectif est un processus simple, que le porteur peut suivre sans être développeur. **Il valide toute décision produit importante et toute mise en production.**

## Qui fait quoi

| Rôle | Fait | Ne fait pas |
|---|---|---|
| **Porteur** | décide, priorise, valide (« Oui, publie »), donne les accès (Search Console, comptes) | — |
| **ChatGPT** | analyse produit, UX/UI, stratégie, SEO ; rédige les **issues** (propositions) ; relit les changements (diff, captures, documents) | ne pousse pas de code en production ; ne contourne pas [DECISIONS.md](DECISIONS.md) |
| **Claude Code** | architecture, implémentation sur branche de test, vérification dans le navigateur, tests, mise à jour de la documentation, préparation de la publication | ne publie pas sans le « Oui, publie » |

## Le circuit d'une évolution

1. **Proposer**, avec une issue GitHub (ChatGPT ou le porteur). Le modèle est plus bas. Avant d'ouvrir l'issue, vérifier que l'idée n'est pas déjà écartée dans [DECISIONS.md](DECISIONS.md).
2. **Valider** : le porteur dit oui, non ou à modifier, dans l'issue.
3. **Implémenter** (Claude Code) :
   - créer une branche `nom-du-chantier` et un tag `avant-nom-du-chantier` ;
   - écrire des commits explicites en français ;
   - vérifier sur ordinateur et téléphone ;
   - faire passer `python -m tests.test_offline` ;
   - remettre les vraies données.
4. **Relire** : ChatGPT ou le porteur regarde les captures, le diff et la documentation mise à jour.
5. **Publier** : Claude Code avance `main` seulement après le « Oui, publie », puis vérifie le site en ligne.
6. **Documenter**, à chaque évolution significative :
   - toujours : [CHANGELOG.md](CHANGELOG.md) et [HANDOFF.md](HANDOFF.md) ;
   - selon le sujet : PRODUCT, DESIGN_SYSTEM, DATA_SOURCES, SEO, MOBILE_APP, ROADMAP ;
   - en cas de décision : une entrée dans [DECISIONS.md](DECISIONS.md).

## Accès de ChatGPT au contexte

- **Via GitHub** : lire `AGENTS.md`, puis `docs/ONBOARDING_CHATGPT.md`, puis les documents utiles. La documentation vit dans le dépôt : pas besoin de recopier les conversations.
- **Ce qui n'est pas dans le dépôt** : les pages générées (`web/spots/`, etc.) et les captures (`captures/`). Pour voir le rendu réel, regarder houlalah.fr ou demander des captures à Claude Code.
- **Ce qu'il ne faut jamais demander ni écrire** : un secret, une clé ou un jeton (voir [AGENTS.md](../AGENTS.md)).

## Modèle d'issue

```
Titre : [Produit|UX|SEO|Données|App|Tech] Résumé court

Constat : ce qui pose problème (avec une capture, une donnée, une requête Search Console…)
Proposition : ce qu'on change, concrètement
Pourquoi : bénéfice attendu pour le surfeur confirmé / pour le SEO
Vérifié dans DECISIONS.md : oui (aucune décision contraire) / non (expliquer l'élément nouveau)
Hors périmètre : ce qu'on ne fait pas
Mesure de succès : comment on saura que ça marche
```

**Étiquettes suggérées** : `produit`, `ux`, `seo`, `donnees`, `app`, `tech`, `bug` ; puis `a-valider`, `valide`, `en-cours`, `fait`.

## Rythme

- **HANDOFF** : il reste **court** (une page) et toujours à jour. C'est le point d'entrée d'un agent qui reprend le travail.
- **Toutes les deux semaines** : remplir le tableau de suivi SEO ([seo-suivi-search-console.md](seo-suivi-search-console.md)).
