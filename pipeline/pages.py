"""Pages de contenu statiques (méthode, mentions légales, confidentialité), rendues avec le même gabarit que les pages de spots.

Texte rédigé d'après le fonctionnement réel du pipeline (voir CLAUDE.md). À relire si une source ou un outil change.
"""
from .seo import BRAND, page

CONTACT = "contact@houlalah.fr"

HOW = {
    "slug": "comment-ca-marche",
    "title": f"Comment {BRAND} calcule ses prévisions de surf",
    "desc": "D'où viennent les prévisions de houle, de vent et de marée de Houlalah, comment elles sont corrigées avec les bouées et comment leur fiabilité est mesurée.",
    "h1": "Comment ça marche",
    "body": """
<p class="lead">Houlalah est un service indépendant de prévisions surf de la Bretagne au Portugal. Il combine plusieurs estimations de hauteur significative de vagues en mer et affiche les observations des bouées avec leur date de mesure. Voici comment lire ces données, comment elles sont calculées et quelles sont leurs limites.</p>

<h2>La houle : plusieurs modèles croisés</h2>
<p>La hauteur significative des vagues est calculée par moyenne pondérée des modèles disponibles : Météo-France MFWAM, DWD EWAM, ECMWF WAM et NOAA GFS-Wave, accessibles via <a href="https://open-meteo.com/en/docs/marine-weather-api">Open-Meteo</a>, et le modèle côtier <a href="https://marc.ifremer.fr/">Ifremer MARC</a> lorsqu'il couvre le point de prévision. Les poids sont renormalisés selon les valeurs disponibles. La période, la direction et les composantes de houle proviennent de la prévision marine de référence d'Open-Meteo : elles ne font pas l'objet de la même moyenne pondérée. L'accord entre modèles décrit leur dispersion, pas une probabilité que la prévision soit exacte.</p>

<h2>Le vent</h2>
<p>Le vent privilégie la prévision Météo-France, avec un repli sur DWD ICON, ECMWF IFS puis NOAA GFS lorsque des valeurs manquent. La comparaison de ces modèles aide à repérer leurs divergences ; elle ne mesure pas à elle seule leur erreur réelle.</p>

<h2>Les bouées : la mesure réelle</h2>
<ul>
<li><b>Bouée Gascogne (Météo-France, 62001)</b> : station au large. Lorsque la mesure permet de calculer une correction, le moteur ajuste la hauteur prévue avec un rapport mesure/prévision dont l'effet décroît jusqu'à zéro sur 24 heures à partir de la mesure. Cette correction est actuellement appliquée aux spots du catalogue ; son bénéfice selon les régions reste à évaluer.</li>
<li><b>Houlographes CANDHIS (Cerema)</b> : les stations côtières fournissent normalement des mesures toutes les 30 minutes. Les autres stations sont notamment accessibles via Copernicus Marine. La fraîcheur dépend de la dernière mesure reçue et de la cadence de chaque station. Une station interrompue peut afficher des mesures anciennes ; les observations en temps réel peuvent être provisoires.</li>
</ul>
<p>Consultez les <a href="../bouees/">mesures des bouées</a> pour retrouver la station, la hauteur, la période, la direction lorsqu'elle est disponible, la source et l'heure de mesure.</p>

<h2>Que signifie la hauteur significative Hs ?</h2>
<p>La hauteur significative caractérise un état de mer : elle correspond approximativement à la moyenne du tiers des vagues les plus hautes. Elle ne représente ni la hauteur de chaque vague ni la taille des vagues qui déferlent sur une plage. Le relief sous-marin, l'exposition du spot, la période et la marée influencent notamment le déferlement. Une observation à une bouée ne constitue donc pas une mesure au bord.</p>

<h2>La marée et le coefficient</h2>
<p>Les horaires de pleine et de basse mer sont issus de calculs harmoniques indépendants à partir de mesures REFMAR (Shom), pour les spots associés à un port de référence. Le coefficient est estimé à partir de la marée de Brest. Les horaires ne sont pas disponibles pour tous les spots. Ces calculs indicatifs ne constituent pas les prédictions officielles du Shom.</p>

<h2>La fiabilité, mesurée</h2>
<p>Les archives permettent actuellement de comparer des hauteurs prévues au point de la bouée Gascogne avec ses mesures, aux échéances de 24, 48, 72 et 96 heures, sur une fenêtre de 30 jours. L'écart absolu moyen indique l'amplitude moyenne de l'erreur, et le biais moyen indique une tendance à surestimer ou sous-estimer. Les résultats ne sont calculés que si suffisamment de comparaisons sont disponibles. Ils ne constituent pas une validation de la hauteur au bord ni du mélange corrigé sur chaque spot. Une comparaison complète des modèles à d'autres bouées reste un chantier en cours.</p>

<h2>Mises à jour et limites</h2>
<p>Le robot actualise régulièrement les données. La date de génération du site, la date de récupération d'une prévision et la date d'observation à une bouée ne sont pas nécessairement identiques. Les prévisions sont des estimations : un modèle ne voit ni un banc de sable qui a bougé ni une rafale locale. Elles ne remplacent ni un coup d'œil sur place ni les consignes de sécurité des plages surveillées.</p>
""",
}

LEGAL = {
    "slug": "mentions-legales",
    "title": f"Mentions légales | {BRAND}",
    "desc": f"Mentions légales du site {BRAND} : éditeur, hébergeur, propriété intellectuelle et responsabilité.",
    "h1": "Mentions légales",
    "body": f"""
<h2>Éditeur</h2>
<p>Le site houlalah.fr est un projet personnel non commercial, édité à titre non professionnel. Conformément à l'article 6 III 2 de la loi pour la confiance dans l'économie numérique (LCEN), l'éditeur a choisi de rester anonyme et communique à la place l'identité de son hébergeur. Contact : <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>

<h2>Hébergeur</h2>
<p>GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis (GitHub Pages).</p>

<h2>Propriété intellectuelle</h2>
<p>Le code, le design, les textes, les visuels et les données archivées du site sont la propriété exclusive de Houlalah. Toute reproduction ou réutilisation sans autorisation écrite préalable est interdite.</p>
<p>Les données de tiers affichées restent soumises à leurs licences : Open-Meteo (CC BY 4.0), Météo-France, DWD, ECMWF, NOAA, Ifremer MARC (Licence Ouverte), Copernicus Marine, Shom / REFMAR (Licence Ouverte) et Cerema / CANDHIS (Licence Ouverte Etalab 2.0).</p>

<h2>Responsabilité</h2>
<p>Les prévisions de houle, de vent et de marée sont des estimations fournies à titre indicatif, sans garantie d'exactitude ni de disponibilité. Elles ne remplacent ni l'observation sur place ni les consignes de sécurité locales. L'éditeur ne peut être tenu responsable d'un dommage lié à leur utilisation. Les liens vers des sites tiers (webcams, services de marée) sont gérés par leurs propriétaires.</p>
""",
}

PRIVACY = {
    "slug": "confidentialite",
    "title": f"Politique de confidentialité | {BRAND}",
    "desc": f"Données personnelles sur {BRAND} : aucun compte, aucun cookie, des statistiques de visite anonymes. Ce qui reste sur ton appareil, et les services tiers.",
    "h1": "Politique de confidentialité",
    "body": f"""
<p class="lead">Houlalah ne te demande aucune donnée personnelle : pas de compte, pas de formulaire, pas de cookie, pas de publicité, pas de suivi individuel. Seules des statistiques de visite anonymes sont comptées, sans cookie (voir plus bas).</p>

<h2>Ce qui est enregistré sur ton appareil</h2>
<p>Le site mémorise dans le stockage local de ton navigateur tes préférences : spots favoris, choix « Large / Côte » du radar, et le fait d'avoir déjà vu l'écran d'accueil. Ces informations restent sur ton appareil et ne sont envoyées nulle part. Tu peux les effacer en vidant les données du site dans ton navigateur.</p>

<h2>Services tiers</h2>
<ul>
<li><b>Statistiques de visite (GoatCounter)</b> : service sans cookie qui compte les pages vues (page, pays, type d'appareil, site d'origine) sans te suivre d'une visite à l'autre et sans enregistrer ton adresse IP.</li>
<li><b>Hébergement (GitHub Pages)</b> : comme tout serveur web, il enregistre l'adresse IP des visiteurs dans ses journaux techniques.</li>
<li><b>Polices de caractères (Google Fonts)</b> : le navigateur les télécharge auprès de Google, qui voit l'adresse IP de ta connexion.</li>
<li><b>Bibliothèques de cartes (jsDelivr)</b> : la carte des spots et la carte de l'accueil chargent un script depuis ce réseau de diffusion.</li>
<li><b>Fond de carte de l'accueil (OpenFreeMap, données OpenStreetMap)</b> : le navigateur télécharge les images de la carte auprès de ce service, qui voit l'adresse IP de ta connexion.</li>
<li><b>Open-Meteo</b> : en cas de panne du serveur de prévisions de Houlalah, ton navigateur interroge directement Open-Meteo, qui voit alors ton adresse IP.</li>
</ul>
<p>Ces services ont leurs propres politiques de confidentialité. Houlalah n'a pas accès aux données qu'ils collectent.</p>

<h2>Tes droits</h2>
<p>Houlalah ne conserve aucune donnée personnelle te concernant : les statistiques de visite sont anonymes. Pour toute question ou demande liée aux données personnelles : <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
""",
}

ABOUT = {
    "slug": "a-propos",
    "title": f"À propos de {BRAND}",
    "desc": f"{BRAND} : des prévisions surf gratuites de la Bretagne au Portugal, vérifiées avec les mesures réelles des bouées en mer. Qui, quoi, comment, contact.",
    "h1": f"À propos de {BRAND}",
    "type": "AboutPage",
    "body": f"""
<p class="lead">{BRAND} donne des prévisions surf gratuites pour plus de 200 spots de la côte atlantique, de la Bretagne au Portugal, et permet de les confronter aux observations des bouées en mer.</p>

<h2>Pourquoi {BRAND}</h2>
<p>Une prévision de houle reste une estimation. Pour savoir si elle tient la route, le plus simple est de la confronter à ce que mesurent réellement les bouées. {BRAND} affiche donc, à côté de chaque prévision, la dernière mesure disponible d'une bouée de référence, son âge et, lorsque les données le permettent, une comparaison entre prévision et mesure. À chacun ensuite de se faire sa propre idée : le site ne donne pas d'avis sur les conditions.</p>

<h2>Ce que vous trouvez sur le site</h2>
<ul>
<li>Les prévisions de houle (hauteur, période, direction) et de vent, heure par heure sur 7 jours, ainsi que les marées et le coefficient lorsqu'ils sont disponibles.</li>
<li>Les <a href="../bouees/">mesures des bouées</a>, de la Bretagne au Portugal, avec leur fraîcheur et leur historique récent lorsqu'il est disponible.</li>
<li>Des prévisions de hauteur croisées entre plusieurs modèles, actualisées régulièrement.</li>
</ul>
<p>Le détail des sources et des calculs est sur la page <a href="../comment-ca-marche/">Comment ça marche</a>.</p>

<h2>Qui fait {BRAND}</h2>
<p>{BRAND} est un projet indépendant et non commercial, sans publicité ni compte utilisateur. Il est développé de façon indépendante, pour les surfeurs qui veulent des données claires et vérifiables.</p>

<h2>À savoir</h2>
<p>La hauteur affichée est celle de la houle au large ou à la bouée, pas la taille des vagues au bord, qui dépend du spot, de la période et de la marée. Les prévisions ne remplacent ni un coup d'œil sur place ni les consignes de sécurité locales.</p>

<h2>Contact</h2>
<p>Une remarque, une erreur sur un spot, une idée : <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
""",
}

ALL = [HOW, ABOUT, LEGAL, PRIVACY]


def render(site, spec):
    canonical = f"{site}/{spec['slug']}/"
    body = f"<h1>{spec['h1']}</h1>{spec['body']}"
    ld = [{"@context": "https://schema.org", "@type": spec.get("type", "WebPage"), "name": spec["title"], "description": spec["desc"], "url": canonical, "inLanguage": "fr",
           "isPartOf": {"@type": "WebSite", "name": BRAND, "url": site + "/"}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
              {"@type": "ListItem", "position": 2, "name": spec["h1"], "item": canonical}]}]
    return page(site, spec["title"], spec["desc"], canonical, body, ld, base="../")
