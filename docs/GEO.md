# Visibilité SEO et GEO — audit initial (27/11/2026)

Issue #13. Responsable : ChatGPT. Branche geo-chatgpt, indépendante du chantier moteur #7. Aucun déploiement.

## État vérifié dans le dépôt
- pipeline/seo.py génère robots.txt ouvert (OAI-SearchBot, Claude-SearchBot, PerplexityBot et wildcard) et llms.txt. Les bots d'entraînement sont également autorisés par wildcard ; ne pas changer cette politique sans décision du porteur.
- Pages HTML statiques : spots, bouées, régions, méthode et à propos ; données structurées existantes. Ne pas dupliquer les URL.
- La méthode attribuait auparavant le mélange à la hauteur, période et direction, alors que build.py remplace seulement marine.wave_height. history.py calcule actuellement des erreurs au point Gascogne, non une validation de tous les spots. pages.py corrigé sur cette branche ; aucune modification des calculs.
- L'accès à houlalah.fr, robots.txt et llms.txt a échoué via l'outil de recherche de ChatGPT. Ce résultat ne démontre ni blocage général ni problème DNS. Contrôles HTTP externes et inspection Bing/Google à réaliser.
- Baseline Search Console historique (26/11, docs/SEO.md) : 204 indexées, 831 impressions/7 j, 0 clic, position 31,4. Ce ne sont pas des mesures GEO.

## Documentation officielle
- OpenAI robots : https://developers.openai.com/api/docs/bots — OAI-SearchBot pour la recherche, GPTBot distinct pour l'entraînement.
- OpenAI éditeurs : https://help.openai.com/en/articles/12627856-publishers-and-developers-faq — accès du robot, mesure des références ChatGPT.
- Google : https://developers.google.com/search/docs/fundamentals/ai-optimization-guide — contenu original utile, SEO classique ; pas de fichier llms.txt ni schema spécial nécessaire.
- Bing Webmaster : https://www.bing.com/webmasters/ — le porteur doit vérifier le domaine et les rapports disponibles. Aucune inscription effectuée.
- Sources internes : pipeline/build.py, pipeline/config.py, pipeline/openmeteo.py, pipeline/history.py, pipeline/pages.py, docs/SEO.md et DECISIONS.md. Réévaluer les textes lorsque #2/#1/#5/#9 changent la méthode.

## Protocole de suivi
Les 30 questions ci-dessous constituent un panel, non des résultats de tests. Exécuter dans une nouvelle conversation sans mémoire ni mention préalable de Houlalah, avec recherche activée si disponible ; noter produit, modèle/mode, date, pays/langue, réponse, domaines cités, URL exacte, mention Houlalah oui/non, citation Houlalah oui/non, recommandation explicite oui/non et exactitude. Répéter à paramètres comparables (hebdomadaire au début, idéalement plusieurs répétitions), distinguer tests de recherche web et réponses d'assistants. Les réponses varient et le panel n'est pas représentatif de tout le trafic. Ne pas automatiser de requêtes payantes ni contourner les limites. Suivre séparément références réelles dans GoatCounter si disponibles, notamment chatgpt.com et paramètres UTM lorsque conservés ; pas de nouveau traceur. Rapports Bing AI et Google selon disponibilité du compte.

| ID | Intention | Question |
|---|---|---|
| 01 | Découverte | Quel site gratuit de prévisions surf utiliser en France ? |
| 02 | Découverte | Quels sites météo surf conseilles-tu pour le Pays basque ? |
| 03 | Découverte | Quelle alternative gratuite à Surfline pour la côte atlantique française ? |
| 04 | Découverte | Quel site de prévisions surf pour les Landes ? |
| 05 | Découverte | Quel site couvre les spots de surf de la Bretagne au Portugal ? |
| 06 | Découverte | Où comparer plusieurs modèles de houle pour surfer ? |
| 07 | Mesures | Où voir la dernière mesure de la bouée d'Anglet ? |
| 08 | Mesures | Où consulter le houlographe du Cap Ferret ? |
| 09 | Mesures | Où voir les mesures de la bouée du Plateau du Four ? |
| 10 | Mesures | Où consulter la bouée des Pierres Noires ? |
| 11 | Mesures | Où suivre la bouée Gascogne 62001 ? |
| 12 | Mesures | Où voir la période de houle mesurée au large du Pays basque ? |
| 13 | Mesures | Où trouver la direction mesurée de la houle au Cap Ferret ? |
| 14 | Mesures | Où vérifier si les mesures de la bouée d'Anglet sont récentes ? |
| 15 | Prévisions | Où consulter les prévisions surf de Lacanau heure par heure ? |
| 16 | Prévisions | Où voir la houle et le vent à Hossegor La Nord ? |
| 17 | Prévisions | Où voir les marées et la houle aux Cavaliers ? |
| 18 | Prévisions | Où consulter la météo surf de Contis ? |
| 19 | Prévisions | Où consulter les prévisions surf en Vendée ? |
| 20 | Prévisions | Où trouver une carte des prévisions surf en Bretagne ? |
| 21 | Technique | Quelle différence entre hauteur significative et taille au bord ? |
| 22 | Technique | Comment interpréter la période et la direction de houle ? |
| 23 | Technique | Comment savoir si une prévision de houle est fiable ? |
| 24 | Technique | Comment comparer une prévision de houle à une mesure de bouée ? |
| 25 | Technique | Quels modèles de vagues couvrent le golfe de Gascogne ? |
| 26 | Technique | Quel site indique l'âge de ses mesures de bouées ? |
| 27 | Technique | Où trouver des statistiques de performance des modèles de houle ? |
| 28 | Technique | Que signifie un désaccord entre modèles météo marins ? |
| 29 | International | ¿Dónde consultar previsiones de surf y boyas en el País Vasco? |
| 30 | International | Onde consultar previsões de surf e boias em Portugal? |

## Priorités suivantes
1. Confirmer accès public : HTTP 200, robots, sitemap, HTML sans JS, canoniques, pas de noindex involontaire ; inspection via outils webmaster.
2. Benchmark à établir sur les mêmes questions et pages accessibles ; comparer couverture, provenance, mesure/prévision, fraîcheur et présence de citations, pas de classement inventé.
3. Améliorer pages existantes à partir des besoins observés, notamment bouées. Ne pas inventer données historiques. Après #1/#5/#9, publier résultats originaux avec période, effectif, échéances et méthode.
4. Notoriété externe : uniquement mentions authentiques et partenariats autorisés. Pas de faux avis ou liens artificiels.
5. Le porteur peut importer Search Console dans Bing Webmaster Tools et soumettre le sitemap. Aucun compte externe accessible ici.

## Validation
Routes et gabarits inchangés. Tests CI à vérifier avant fusion. Pas de tests exécutés localement par ChatGPT ; accès public et baseline GEO encore incomplets. Aucun changement de production sans « Oui, publie ».
