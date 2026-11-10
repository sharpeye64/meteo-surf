"""Pages de contenu statiques (méthode, mentions légales, confidentialité), rendues avec le même gabarit que les pages de spots.

Texte rédigé d'après le fonctionnement réel du pipeline (voir CLAUDE.md). À relire si une source ou un outil change.
"""
from .seo import BRAND, page

CONTACT = "contact@houlalah.fr"

HOW = {
    "slug": "comment-ca-marche",
    "title": f"Comment {BRAND} calcule ses prévisions de surf : modèles, bouées, marées",
    "desc": "D'où viennent les prévisions de houle, de vent et de marée de Houlalah, comment elles sont corrigées avec les bouées et comment leur fiabilité est mesurée.",
    "h1": "Comment ça marche",
    "body": """
<p class="lead">Houlalah ne produit pas ses propres modèles : il croise plusieurs prévisions publiques, les corrige avec des mesures réelles et dit ce qu'il en est de leur fiabilité. Voici d'où vient chaque chiffre.</p>

<h2>La houle : plusieurs modèles croisés</h2>
<p>La hauteur, la période et la direction de la houle viennent d'un mélange de modèles : Météo-France MFWAM, DWD EWAM, ECMWF WAM et NOAA GFS-Wave (via Open-Meteo), plus le modèle côtier Ifremer MARC (grille d'environ 3,7 km sur le golfe de Gascogne). Quand les modèles disent la même chose, l'accord est fort. Quand ils divergent, l'écart est affiché sous le grand chiffre du haut de page.</p>

<h2>Le vent</h2>
<p>Le vent vient du modèle Météo-France AROME, comparé à DWD ICON, NOAA GFS et ECMWF IFS. AROME ne va pas au-delà de 4 jours environ : au-delà, la prévision bascule sur ICON, et la fiabilité baisse.</p>

<h2>Les bouées : la mesure réelle</h2>
<ul>
<li><b>Bouée Gascogne (Météo-France, 62001)</b> : au large, à environ 300 km de la côte. Elle voit la houle arriver bien avant la côte. Elle mesure toutes les heures, avec environ 1 h de retard. Quand les modèles s'écartent de sa mesure, nos prévisions sont corrigées sur les 24 heures suivantes.</li>
<li><b>Bouées côtières CANDHIS (Cerema)</b> : Cap Ferret, Anglet, Saint-Jean-de-Luz. Mesures toutes les 30 minutes, fraîches. Le site compare la mesure de la bouée la plus proche du spot avec sa prévision. Ces mesures en temps réel ne sont pas validées.</li>
</ul>

<h2>La marée et le coefficient</h2>
<p>Les horaires de pleine et de basse mer sont calculés par méthode harmonique à partir de mesures officielles des marégraphes REFMAR (Shom) à Socoa et à Boucau-Bayonne. Sur des mesures indépendantes, l'écart moyen d'heure est d'environ 5 minutes. Le coefficient est calculé à partir de la marée de Brest, avec un écart moyen d'environ 2 points par rapport à la valeur officielle. Ces valeurs sont indicatives : à vérifier avant de sortir.</p>

<h2>La fiabilité, mesurée</h2>
<p>À chaque mise à jour, les prévisions sont archivées. Elles sont ensuite comparées à la mesure réelle de la bouée à 24, 48, 72 et 96 heures d'avance, sur les 30 derniers jours. Le résultat apparaît en bas de la page d'accueil dès qu'il y a assez de mesures. Houlalah ne dit jamais si les conditions sont « bonnes » : c'est à toi de juger, avec des données dont on connaît la précision.</p>

<h2>Mises à jour et limites</h2>
<p>Les prévisions sont recalculées toutes les 3 heures. Ce sont des estimations : un modèle ne voit ni un banc de sable qui a bougé ni une rafale locale. Elles ne remplacent ni un coup d'œil sur place ni les consignes de sécurité des plages surveillées.</p>
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
    "desc": f"Données personnelles sur {BRAND} : aucun compte, aucun cookie publicitaire, aucun suivi. Ce qui est stocké sur ton appareil et les services tiers utilisés.",
    "h1": "Politique de confidentialité",
    "body": f"""
<p class="lead">Houlalah ne te demande aucune donnée personnelle : pas de compte, pas de formulaire, pas de cookie publicitaire, pas d'outil de suivi.</p>

<h2>Ce qui est enregistré sur ton appareil</h2>
<p>Le site mémorise dans le stockage local de ton navigateur tes préférences : spots favoris, choix « Large / Côte » du radar, et le fait d'avoir déjà vu l'écran d'accueil. Ces informations restent sur ton appareil et ne sont envoyées nulle part. Tu peux les effacer en vidant les données du site dans ton navigateur.</p>

<h2>Services tiers</h2>
<ul>
<li><b>Hébergement (GitHub Pages)</b> : comme tout serveur web, il enregistre l'adresse IP des visiteurs dans ses journaux techniques.</li>
<li><b>Polices de caractères (Google Fonts)</b> : le navigateur les télécharge auprès de Google, qui voit l'adresse IP de ta connexion.</li>
<li><b>Bibliothèques de cartes (jsDelivr)</b> : la carte des spots et la carte de l'accueil chargent un script depuis ce réseau de diffusion.</li>
<li><b>Fond de carte de l'accueil (OpenFreeMap, données OpenStreetMap)</b> : le navigateur télécharge les images de la carte auprès de ce service, qui voit l'adresse IP de ta connexion.</li>
<li><b>Open-Meteo</b> : en cas de panne du serveur de prévisions de Houlalah, ton navigateur interroge directement Open-Meteo, qui voit alors ton adresse IP.</li>
</ul>
<p>Ces services ont leurs propres politiques de confidentialité. Houlalah n'a pas accès aux données qu'ils collectent.</p>

<h2>Tes droits</h2>
<p>Houlalah ne conserve aucune donnée te concernant. Pour toute question ou demande liée aux données personnelles : <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
""",
}

ALL = [HOW, LEGAL, PRIVACY]


def render(site, spec):
    canonical = f"{site}/{spec['slug']}/"
    body = f"<h1>{spec['h1']}</h1>{spec['body']}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": spec["title"], "description": spec["desc"], "url": canonical, "inLanguage": "fr",
           "isPartOf": {"@type": "WebSite", "name": BRAND, "url": site + "/"}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
              {"@type": "ListItem", "position": 2, "name": spec["h1"], "item": canonical}]}]
    return page(site, spec["title"], spec["desc"], canonical, body, ld, base="../")
