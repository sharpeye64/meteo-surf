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
<p>Consultez le <a href="../guide/lire-une-bouee/">guide de lecture des houlographes</a> et les <a href="../bouees/">mesures des bouées</a> pour retrouver la station, la hauteur, la période, la direction lorsqu'elle est disponible, la source et l'heure de mesure.</p>

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

GUIDE_BUOY = {
    "slug": "guide/lire-une-bouee",
    "title": "Comment lire une bouée houlographe ? | Houlalah",
    "desc": "Comprendre la hauteur significative, la période, la direction et la fraîcheur des mesures de houle avant de les comparer aux prévisions.",
    "h1": "Comment lire une bouée houlographe ?",
    "body": """
<p class="muted">GUIDE · OBSERVATIONS EN MER</p><p><a href="../">Tous les guides</a></p>
<p class="lead">Une bouée décrit l'état de la mer à son emplacement. Pour interpréter une mesure, lis ensemble la hauteur significative, la période, la direction et l'heure du relevé.</p>
<dl class="fiche"><div><dt>Hauteur significative</dt><dd>Hs · en mètres</dd></div><div><dt>Période et direction</dt><dd>Tp / Tm · secteur</dd></div><div><dt>Fraîcheur</dt><dd>Date et heure</dd></div></dl>
<h2>Hauteur significative ou vague maximale ?</h2>
<p>La hauteur significative (Hs) caractérise l'état de mer et correspond approximativement à la moyenne du tiers des vagues les plus hautes. La hauteur maximale, lorsqu'elle est disponible, décrit une vague individuelle observée pendant la mesure. Ni l'une ni l'autre n'est une mesure de la taille au bord.</p>
<figure class="guide-figure"><svg viewBox="0 0 540 230" role="img" aria-label="Six vagues fictives de 0,7 à 2,2 mètres, les deux plus hautes en or"><g fill="#5795B7"><rect x="35" y="144" width="55" height="42" rx="4"/><rect x="115" y="120" width="55" height="66" rx="4"/><rect x="195" y="138" width="55" height="48" rx="4"/><rect x="355" y="102" width="55" height="84" rx="4"/></g><g fill="#E9C694"><rect x="275" y="54" width="55" height="132" rx="4"/><rect x="435" y="78" width="55" height="108" rx="4"/></g><path d="M20 186H510" stroke="#F3EFE6"/><g fill="#F3EFE6" font-size="15" text-anchor="middle"><text x="62" y="135">0,7</text><text x="142" y="111">1,1</text><text x="222" y="129">0,8</text><text x="302" y="45">2,2</text><text x="382" y="93">1,4</text><text x="462" y="69">1,8</text></g><text x="20" y="216" fill="#F3EFE6" font-size="14">Hauteurs individuelles (m) · ordre d'observation</text></svg><figcaption>Exemple simplifié de six vagues : le tiers supérieur contient 2,2 et 1,8 m, soit une moyenne de 2,0 m. Hmax = 2,2 m. En pratique, les houlographes exploitent des séries bien plus longues.</figcaption></figure><p><b>Comment le lire :</b> si la bouée indique Hs 2 m, tu ne dois pas t'attendre à des vagues toutes identiques. Hmax renseigne sur un extrême de la fenêtre observée, pas sur un maximum possible dans les prochaines heures. La définition spectrale de Hs utilisée par certains instruments est une estimation statistique proche de cette moyenne.</p><h2>Période et direction : lire les deux ensemble</h2>
<p>La période de pic (Tp) correspond au maximum d'énergie du spectre de vagues. La période moyenne (Tm) est une autre statistique : ne les compare pas comme si elles étaient identiques. La direction de provenance indique d'où viennent les vagues. Une mer peut contenir plusieurs trains de houle ; une direction unique n'en décrit pas toute la complexité.</p>
<h2>La mesure est-elle récente ?</h2>
<p>Vérifie l'heure du relevé plutôt que l'heure de mise à jour du site. Les stations CANDHIS publient normalement des mesures toutes les 30 minutes ; les retards ou interruptions restent possibles. Une ancienne observation ne décrit pas nécessairement la mer actuelle.</p>
<p><b>Exemple fictif :</b> une mesure de 08 h 30 consultée à 11 h a 2 h 30 d'âge, même si le site a été régénéré à 10 h 55. Avant de conclure à une montée ou à une baisse de houle, consulte la série des relevés plutôt qu'un chiffre isolé.</p><h2>Comparer la bouée à une prévision</h2>
<p>Privilégie une comparaison au même emplacement et à la même heure. Une prévision à un spot voisin peut différer pour des raisons géographiques. L'exposition de la côte, la bathymétrie et la marée influencent le déferlement ; une bouée ne suffit donc pas à déterminer la taille au bord.</p>
<h2>Observer les stations</h2>
<ul class="near"><li><a href="../../bouees/cap-ferret/">Cap Ferret<small>Houlographe CANDHIS</small></a></li><li><a href="../../bouees/anglet/">Anglet<small>Houlographe CANDHIS</small></a></li><li><a href="../../bouees/gascogne/">Gascogne<small>Bouée du large</small></a></li></ul>
<p><a class="cta" href="../../bouees/">Toutes les bouées</a></p>
<h2>Sources et méthode</h2>
<p>Consulte le <a href="https://candhis.cerema.fr/">réseau CANDHIS du Cerema</a>, la <a href="https://open-meteo.com/en/docs/marine-weather-api">documentation marine Open-Meteo</a> et <a href="../../comment-ca-marche/">la méthode Houlalah</a> pour distinguer observations et prévisions.</p>
""",
}

GUIDE_INDEX = {
    "slug": "guide",
    "title": "Comprendre la houle : les guides Houlalah",
    "desc": "Lire les houlographes, comprendre la houle et interpréter les différences entre modèles de prévision marine.",
    "h1": "Comprendre la houle",
    "type": "CollectionPage",
    "body": """
<p class="lead">Des repères techniques pour confronter les prévisions à la réalité de l'océan. À chacun de faire sa propre lecture des conditions.</p>
<ul class="near">
<li><a href="lire-une-bouee/"><b>Lire une bouée houlographe</b><small>Mesures, période, direction et fraîcheur</small></a></li>
<li><a href="comprendre-la-houle/"><b>Hauteur, période et direction</b><small>Interpréter les composantes de l'état de mer</small></a></li>
<li><a href="modeles-meteo-surf/"><b>Les modèles de houle</b><small>Résolution, échéance et divergence</small></a></li>
</ul>
<h2>De la théorie aux observations</h2>
<p>Retrouve les <a href="../bouees/">mesures des bouées</a>, les <a href="../spots/">prévisions par spot</a> et <a href="../comment-ca-marche/">la méthode Houlalah</a>.</p>
""",
}

GUIDE_SWELL = {
    "slug": "guide/comprendre-la-houle",
    "title": "Houle : hauteur, période et direction | Houlalah",
    "desc": "Comprendre la hauteur significative, la période, la direction et les composantes de houle pour interpréter une prévision surf.",
    "h1": "Hauteur, période et direction de houle",
    "body": """
<p class="muted">GUIDE · ÉTAT DE MER</p><p><a href="../">Tous les guides</a></p>
<p class="lead">Une hauteur seule ne suffit pas à décrire la houle. La période renseigne sur son échelle temporelle, la direction sur sa provenance et les composantes sur la coexistence de plusieurs trains de vagues.</p>
<dl class="fiche"><div><dt>Hauteur</dt><dd>Hs · mètres</dd></div><div><dt>Période</dt><dd>Secondes</dd></div><div><dt>Direction</dt><dd>Provenance</dd></div></dl>
<h2>Hauteur significative et énergie</h2>
<p>La hauteur significative décrit statistiquement l'état de mer. Dans les approximations usuelles en eau profonde, l'énergie moyenne des vagues par unité de surface est proportionnelle au carré de leur hauteur significative. Ce n'est pas une prédiction de la hauteur d'une vague individuelle.</p>
<h2>Pourquoi la période change la lecture</h2>
<p>La période exprime une durée en secondes. En eau profonde, pour des vagues de gravité linéaires, les composantes de période plus longue se propagent plus rapidement. À hauteur significative comparable, deux états de mer peuvent donc présenter des flux d'énergie différents. La période de pic et la période moyenne sont des statistiques distinctes.</p>
<figure class="guide-figure"><svg viewBox="0 0 540 240" role="img" aria-label="Deux trains de vagues de même amplitude, de périodes 7 et 14 secondes"><g font-size="16" fill="#F3EFE6"><text x="30" y="27">7 s · période courte</text><text x="30" y="127">14 s · période longue</text></g><g stroke="#526873" stroke-dasharray="4 5"><path d="M30 65H510M30 165H510"/></g><g fill="none" stroke="#E9C694" stroke-width="3"><path d="M30.0 65.0 L31.6 63.0 L33.2 61.0 L34.8 59.0 L36.4 57.1 L38.0 55.2 L39.6 53.4 L41.2 51.7 L42.8 50.1 L44.4 48.6 L46.0 47.2 L47.6 45.9 L49.2 44.7 L50.8 43.7 L52.4 42.9 L54.0 42.2 L55.6 41.6 L57.2 41.3 L58.8 41.0 L60.4 41.0 L62.0 41.1 L63.6 41.4 L65.2 41.9 L66.8 42.5 L68.4 43.3 L70.0 44.2 L71.6 45.3 L73.2 46.5 L74.8 47.9 L76.4 49.3 L78.0 50.9 L79.6 52.6 L81.2 54.3 L82.8 56.2 L84.4 58.1 L86.0 60.0 L87.6 62.0 L89.2 64.0 L90.8 66.0 L92.4 68.0 L94.0 70.0 L95.6 71.9 L97.2 73.8 L98.8 75.7 L100.4 77.4 L102.0 79.1 L103.6 80.7 L105.2 82.1 L106.8 83.5 L108.4 84.7 L110.0 85.8 L111.6 86.7 L113.2 87.5 L114.8 88.1 L116.4 88.6 L118.0 88.9 L119.6 89.0 L121.2 89.0 L122.8 88.7 L124.4 88.4 L126.0 87.8 L127.6 87.1 L129.2 86.3 L130.8 85.3 L132.4 84.1 L134.0 82.8 L135.6 81.4 L137.2 79.9 L138.8 78.3 L140.4 76.6 L142.0 74.8 L143.6 72.9 L145.2 71.0 L146.8 69.0 L148.4 67.0 L150.0 65.0 L151.6 63.0 L153.2 61.0 L154.8 59.0 L156.4 57.1 L158.0 55.2 L159.6 53.4 L161.2 51.7 L162.8 50.1 L164.4 48.6 L166.0 47.2 L167.6 45.9 L169.2 44.7 L170.8 43.7 L172.4 42.9 L174.0 42.2 L175.6 41.6 L177.2 41.3 L178.8 41.0 L180.4 41.0 L182.0 41.1 L183.6 41.4 L185.2 41.9 L186.8 42.5 L188.4 43.3 L190.0 44.2 L191.6 45.3 L193.2 46.5 L194.8 47.9 L196.4 49.3 L198.0 50.9 L199.6 52.6 L201.2 54.3 L202.8 56.2 L204.4 58.1 L206.0 60.0 L207.6 62.0 L209.2 64.0 L210.8 66.0 L212.4 68.0 L214.0 70.0 L215.6 71.9 L217.2 73.8 L218.8 75.7 L220.4 77.4 L222.0 79.1 L223.6 80.7 L225.2 82.1 L226.8 83.5 L228.4 84.7 L230.0 85.8 L231.6 86.7 L233.2 87.5 L234.8 88.1 L236.4 88.6 L238.0 88.9 L239.6 89.0 L241.2 89.0 L242.8 88.7 L244.4 88.4 L246.0 87.8 L247.6 87.1 L249.2 86.3 L250.8 85.3 L252.4 84.1 L254.0 82.8 L255.6 81.4 L257.2 79.9 L258.8 78.3 L260.4 76.6 L262.0 74.8 L263.6 72.9 L265.2 71.0 L266.8 69.0 L268.4 67.0 L270.0 65.0 L271.6 63.0 L273.2 61.0 L274.8 59.0 L276.4 57.1 L278.0 55.2 L279.6 53.4 L281.2 51.7 L282.8 50.1 L284.4 48.6 L286.0 47.2 L287.6 45.9 L289.2 44.7 L290.8 43.7 L292.4 42.9 L294.0 42.2 L295.6 41.6 L297.2 41.3 L298.8 41.0 L300.4 41.0 L302.0 41.1 L303.6 41.4 L305.2 41.9 L306.8 42.5 L308.4 43.3 L310.0 44.2 L311.6 45.3 L313.2 46.5 L314.8 47.9 L316.4 49.3 L318.0 50.9 L319.6 52.6 L321.2 54.3 L322.8 56.2 L324.4 58.1 L326.0 60.0 L327.6 62.0 L329.2 64.0 L330.8 66.0 L332.4 68.0 L334.0 70.0 L335.6 71.9 L337.2 73.8 L338.8 75.7 L340.4 77.4 L342.0 79.1 L343.6 80.7 L345.2 82.1 L346.8 83.5 L348.4 84.7 L350.0 85.8 L351.6 86.7 L353.2 87.5 L354.8 88.1 L356.4 88.6 L358.0 88.9 L359.6 89.0 L361.2 89.0 L362.8 88.7 L364.4 88.4 L366.0 87.8 L367.6 87.1 L369.2 86.3 L370.8 85.3 L372.4 84.1 L374.0 82.8 L375.6 81.4 L377.2 79.9 L378.8 78.3 L380.4 76.6 L382.0 74.8 L383.6 72.9 L385.2 71.0 L386.8 69.0 L388.4 67.0 L390.0 65.0 L391.6 63.0 L393.2 61.0 L394.8 59.0 L396.4 57.1 L398.0 55.2 L399.6 53.4 L401.2 51.7 L402.8 50.1 L404.4 48.6 L406.0 47.2 L407.6 45.9 L409.2 44.7 L410.8 43.7 L412.4 42.9 L414.0 42.2 L415.6 41.6 L417.2 41.3 L418.8 41.0 L420.4 41.0 L422.0 41.1 L423.6 41.4 L425.2 41.9 L426.8 42.5 L428.4 43.3 L430.0 44.2 L431.6 45.3 L433.2 46.5 L434.8 47.9 L436.4 49.3 L438.0 50.9 L439.6 52.6 L441.2 54.3 L442.8 56.2 L444.4 58.1 L446.0 60.0 L447.6 62.0 L449.2 64.0 L450.8 66.0 L452.4 68.0 L454.0 70.0 L455.6 71.9 L457.2 73.8 L458.8 75.7 L460.4 77.4 L462.0 79.1 L463.6 80.7 L465.2 82.1 L466.8 83.5 L468.4 84.7 L470.0 85.8 L471.6 86.7 L473.2 87.5 L474.8 88.1 L476.4 88.6 L478.0 88.9 L479.6 89.0 L481.2 89.0 L482.8 88.7 L484.4 88.4 L486.0 87.8 L487.6 87.1 L489.2 86.3 L490.8 85.3 L492.4 84.1 L494.0 82.8 L495.6 81.4 L497.2 79.9 L498.8 78.3 L500.4 76.6 L502.0 74.8 L503.6 72.9 L505.2 71.0 L506.8 69.0 L508.4 67.0 L510.0 65.0"/><path d="M30.0 165.0 L31.6 164.0 L33.2 163.0 L34.8 162.0 L36.4 161.0 L38.0 160.0 L39.6 159.0 L41.2 158.1 L42.8 157.1 L44.4 156.2 L46.0 155.2 L47.6 154.3 L49.2 153.4 L50.8 152.6 L52.4 151.7 L54.0 150.9 L55.6 150.1 L57.2 149.3 L58.8 148.6 L60.4 147.9 L62.0 147.2 L63.6 146.5 L65.2 145.9 L66.8 145.3 L68.4 144.7 L70.0 144.2 L71.6 143.7 L73.2 143.3 L74.8 142.9 L76.4 142.5 L78.0 142.2 L79.6 141.9 L81.2 141.6 L82.8 141.4 L84.4 141.3 L86.0 141.1 L87.6 141.0 L89.2 141.0 L90.8 141.0 L92.4 141.0 L94.0 141.1 L95.6 141.3 L97.2 141.4 L98.8 141.6 L100.4 141.9 L102.0 142.2 L103.6 142.5 L105.2 142.9 L106.8 143.3 L108.4 143.7 L110.0 144.2 L111.6 144.7 L113.2 145.3 L114.8 145.9 L116.4 146.5 L118.0 147.2 L119.6 147.9 L121.2 148.6 L122.8 149.3 L124.4 150.1 L126.0 150.9 L127.6 151.7 L129.2 152.6 L130.8 153.4 L132.4 154.3 L134.0 155.2 L135.6 156.2 L137.2 157.1 L138.8 158.1 L140.4 159.0 L142.0 160.0 L143.6 161.0 L145.2 162.0 L146.8 163.0 L148.4 164.0 L150.0 165.0 L151.6 166.0 L153.2 167.0 L154.8 168.0 L156.4 169.0 L158.0 170.0 L159.6 171.0 L161.2 171.9 L162.8 172.9 L164.4 173.8 L166.0 174.8 L167.6 175.7 L169.2 176.6 L170.8 177.4 L172.4 178.3 L174.0 179.1 L175.6 179.9 L177.2 180.7 L178.8 181.4 L180.4 182.1 L182.0 182.8 L183.6 183.5 L185.2 184.1 L186.8 184.7 L188.4 185.3 L190.0 185.8 L191.6 186.3 L193.2 186.7 L194.8 187.1 L196.4 187.5 L198.0 187.8 L199.6 188.1 L201.2 188.4 L202.8 188.6 L204.4 188.7 L206.0 188.9 L207.6 189.0 L209.2 189.0 L210.8 189.0 L212.4 189.0 L214.0 188.9 L215.6 188.7 L217.2 188.6 L218.8 188.4 L220.4 188.1 L222.0 187.8 L223.6 187.5 L225.2 187.1 L226.8 186.7 L228.4 186.3 L230.0 185.8 L231.6 185.3 L233.2 184.7 L234.8 184.1 L236.4 183.5 L238.0 182.8 L239.6 182.1 L241.2 181.4 L242.8 180.7 L244.4 179.9 L246.0 179.1 L247.6 178.3 L249.2 177.4 L250.8 176.6 L252.4 175.7 L254.0 174.8 L255.6 173.8 L257.2 172.9 L258.8 171.9 L260.4 171.0 L262.0 170.0 L263.6 169.0 L265.2 168.0 L266.8 167.0 L268.4 166.0 L270.0 165.0 L271.6 164.0 L273.2 163.0 L274.8 162.0 L276.4 161.0 L278.0 160.0 L279.6 159.0 L281.2 158.1 L282.8 157.1 L284.4 156.2 L286.0 155.2 L287.6 154.3 L289.2 153.4 L290.8 152.6 L292.4 151.7 L294.0 150.9 L295.6 150.1 L297.2 149.3 L298.8 148.6 L300.4 147.9 L302.0 147.2 L303.6 146.5 L305.2 145.9 L306.8 145.3 L308.4 144.7 L310.0 144.2 L311.6 143.7 L313.2 143.3 L314.8 142.9 L316.4 142.5 L318.0 142.2 L319.6 141.9 L321.2 141.6 L322.8 141.4 L324.4 141.3 L326.0 141.1 L327.6 141.0 L329.2 141.0 L330.8 141.0 L332.4 141.0 L334.0 141.1 L335.6 141.3 L337.2 141.4 L338.8 141.6 L340.4 141.9 L342.0 142.2 L343.6 142.5 L345.2 142.9 L346.8 143.3 L348.4 143.7 L350.0 144.2 L351.6 144.7 L353.2 145.3 L354.8 145.9 L356.4 146.5 L358.0 147.2 L359.6 147.9 L361.2 148.6 L362.8 149.3 L364.4 150.1 L366.0 150.9 L367.6 151.7 L369.2 152.6 L370.8 153.4 L372.4 154.3 L374.0 155.2 L375.6 156.2 L377.2 157.1 L378.8 158.1 L380.4 159.0 L382.0 160.0 L383.6 161.0 L385.2 162.0 L386.8 163.0 L388.4 164.0 L390.0 165.0 L391.6 166.0 L393.2 167.0 L394.8 168.0 L396.4 169.0 L398.0 170.0 L399.6 171.0 L401.2 171.9 L402.8 172.9 L404.4 173.8 L406.0 174.8 L407.6 175.7 L409.2 176.6 L410.8 177.4 L412.4 178.3 L414.0 179.1 L415.6 179.9 L417.2 180.7 L418.8 181.4 L420.4 182.1 L422.0 182.8 L423.6 183.5 L425.2 184.1 L426.8 184.7 L428.4 185.3 L430.0 185.8 L431.6 186.3 L433.2 186.7 L434.8 187.1 L436.4 187.5 L438.0 187.8 L439.6 188.1 L441.2 188.4 L442.8 188.6 L444.4 188.7 L446.0 188.9 L447.6 189.0 L449.2 189.0 L450.8 189.0 L452.4 189.0 L454.0 188.9 L455.6 188.7 L457.2 188.6 L458.8 188.4 L460.4 188.1 L462.0 187.8 L463.6 187.5 L465.2 187.1 L466.8 186.7 L468.4 186.3 L470.0 185.8 L471.6 185.3 L473.2 184.7 L474.8 184.1 L476.4 183.5 L478.0 182.8 L479.6 182.1 L481.2 181.4 L482.8 180.7 L484.4 179.9 L486.0 179.1 L487.6 178.3 L489.2 177.4 L490.8 176.6 L492.4 175.7 L494.0 174.8 L495.6 173.8 L497.2 172.9 L498.8 171.9 L500.4 171.0 L502.0 170.0 L503.6 169.0 L505.2 168.0 L506.8 167.0 L508.4 166.0 L510.0 165.0"/></g><g font-size="13" fill="#F3EFE6"><text x="30" y="222">0 s</text><text x="488" y="222">28 s</text></g></svg><figcaption>Schéma théorique : même amplitude, quatre cycles contre deux sur 28 secondes. Ce ne sont pas des mesures.</figcaption></figure><p><b>Exemple théorique :</b> à Hs identique de 1,5 m, si la période énergétique double de 7 à 14 s, le flux d'énergie en eau profonde double approximativement. La période énergétique n'est pas nécessairement la période de pic affichée par le site. Cette relation ne permet pas de déduire une hauteur au déferlement.</p><h2>Direction et exposition</h2>
<p>La direction de provenance indique d'où viennent les vagues. Une houle peut être atténuée derrière un cap, ou être réorientée par la réfraction lorsque la profondeur diminue. La direction au large ne permet pas à elle seule de prévoir le déferlement sur un banc de sable.</p>
<figure class="guide-figure"><svg viewBox="0 0 540 280" role="img" aria-label="Vue en plan schématique de vagues obliques se réorientant près du littoral"><rect width="540" height="280" rx="8" fill="#163746"/><path d="M430 0 Q390 100 445 165T425 280H540V0Z" fill="#E9C694"/><g fill="none" stroke="#7195A4" stroke-dasharray="5 6"><path d="M350 0Q310 100 365 165T345 280"/><path d="M270 0Q230 100 285 165T265 280"/></g><g stroke="#F3EFE6" stroke-width="3" fill="none"><path d="M30 0L175 135Q230 180 230 280"/><path d="M130 0L260 115Q310 160 310 280"/><path d="M230 0L340 90Q375 135 385 280"/></g><g font-size="15" fill="#F3EFE6"><text x="15" y="260">Large</text><text x="235" y="26">Profondeur décroissante</text></g><text x="465" y="245" fill="#0B1B26" font-size="16">Terre</text></svg><figcaption>Vue en plan conceptuelle : les fronts de vagues changent progressivement d'orientation quand leur vitesse varie avec la profondeur. Ce dessin n'est ni une carte réelle ni une simulation bathymétrique.</figcaption></figure><figure class="guide-figure"><svg viewBox="0 0 540 230" role="img" aria-label="Houle venant de l'ouest, plage exposée et secteur partiellement abrité derrière un cap"><rect width="540" height="230" rx="8" fill="#163746"/><path d="M410 0H540V230H410V160L275 115L410 83Z" fill="#E9C694"/><g stroke="#F3EFE6" stroke-width="3" fill="none"><path d="M25 35H370l-12 -7m12 7l-12 7M25 80H310l-12 -7m12 7l-12 7M25 180H240l-12 -7m12 7l-12 7"/></g><g fill="#F3EFE6" font-size="15"><text x="20" y="20">Houle d'ouest</text><text x="300" y="58">Secteur exposé</text><text x="290" y="205">Secteur abrité*</text></g><text x="360" y="121" fill="#0B1B26" font-size="16">Cap</text></svg><figcaption>*Abri géométrique simplifié. Une partie de l'énergie peut atteindre le secteur par diffraction ou réfraction ; le degré d'abri ne se déduit pas de ce dessin.</figcaption></figure><p>En pratique, commence par la direction de provenance et l'orientation de la plage, puis considère la période et la hauteur. Deux spots voisins peuvent recevoir une fraction différente de la même houle. Sans bathymétrie et observations locales, on ne chiffre pas cette différence.</p><h2>Houle primaire, secondaire et mer du vent</h2>
<p>La mer du vent correspond aux vagues générées par le vent local ; la houle peut avoir quitté sa zone de génération. Plusieurs systèmes peuvent coexister. Les hauteurs significatives des composantes ne s'additionnent pas directement : pour des composantes indépendantes, leurs énergies s'ajoutent.</p>
<section class="guide-calc"><h2>Comparer deux états de mer</h2><p>Modèle théorique en eau profonde : fais varier la hauteur significative Hs et la période énergétique Te. Le flux par mètre de crête est approximativement 0,49 × Hs² × Te (kW/m), pour une masse volumique de 1 025 kg/m³ et g = 9,81 m/s². Ce calcul ne prédit pas la taille au bord.</p><div class="guide-inputs"><fieldset><legend>État A</legend><label>Hs (m) <input id="gh-a" type="number" min="0.1" max="15" step="0.1" value="1.5"></label><label>Te (s) <input id="gt-a" type="number" min="1" max="30" step="1" value="7"></label><output id="gp-a">7,7 kW/m</output></fieldset><fieldset><legend>État B</legend><label>Hs (m) <input id="gh-b" type="number" min="0.1" max="15" step="0.1" value="1.5"></label><label>Te (s) <input id="gt-b" type="number" min="1" max="30" step="1" value="14"></label><output id="gp-b">15,4 kW/m</output></fieldset></div><p id="gp-r" aria-live="polite">B transporte environ 2 fois le flux d'énergie de A.</p><p class="muted">Exemples théoriques, pas de mesures ni de prévisions réelles. Te n'est pas nécessairement Tp.</p></section><script>(function(){const ids=['gh-a','gt-a','gh-b','gt-b'];const el=ids.map(id=>document.getElementById(id));const fmt=n=>n.toLocaleString('fr-FR',{maximumFractionDigits:2});function update(){const v=el.map(e=>e.valueAsNumber);if(el.some(e=>!e.validity.valid)||v.some(n=>!Number.isFinite(n)||n<=0)){document.getElementById('gp-a').textContent='—';document.getElementById('gp-b').textContent='—';document.getElementById('gp-r').textContent='Renseigne des valeurs valides.';return;}const a=.49*v[0]*v[0]*v[1],b=.49*v[2]*v[2]*v[3];document.getElementById('gp-a').textContent=fmt(a)+' kW/m';document.getElementById('gp-b').textContent=fmt(b)+' kW/m';document.getElementById('gp-r').textContent='Rapport du flux B / A : '+fmt(b/a)+' ×';}el.forEach(e=>e.addEventListener('input',update));update();})();</script><h2>Passer de la prévision à l'observation</h2>
<p>Compare les mêmes variables à la même heure et au même emplacement, en vérifiant la fraîcheur de la mesure. La hauteur au large ne représente pas la hauteur au bord.</p>
<p><a href="../lire-une-bouee/">Lire une bouée houlographe</a> · <a href="../modeles-meteo-surf/">Comprendre les modèles</a></p>
<h2>Sources</h2><p><a href="https://www.ndbc.noaa.gov/">NOAA National Data Buoy Center</a> · <a href="https://open-meteo.com/en/docs/marine-weather-api">Open-Meteo, variables marines</a> · <a href="../../comment-ca-marche/">Méthode Houlalah</a>.</p>
""",
}

GUIDE_MODELS = {
    "slug": "guide/modeles-meteo-surf",
    "title": "Modèles de houle : comprendre les écarts | Houlalah",
    "desc": "Comprendre pourquoi les modèles de houle divergent, comment Houlalah combine les hauteurs prévues et comment les confronter aux bouées.",
    "h1": "Comprendre les modèles de houle",
    "body": """
<p class="muted">GUIDE · PRÉVISIONS MARINES</p><p><a href="../">Tous les guides</a></p>
<p class="lead">Deux modèles peuvent annoncer des hauteurs différentes au même endroit et à la même heure. Leur accord est une information utile, mais il ne constitue pas une preuve d'exactitude.</p>
<h2>Quels modèles utilise Houlalah ?</h2>
<p>Le moteur combine les hauteurs significatives disponibles de Météo-France MFWAM, DWD EWAM, ECMWF WAM, NOAA GFS-Wave et Ifremer MARC dans sa zone de couverture. Les quatre premiers sont accessibles via Open-Meteo. Les poids sont renormalisés selon les données disponibles ; la période, la direction et les composantes proviennent de la prévision marine de référence.</p>
<h2>Pourquoi les prévisions divergent-elles ?</h2>
<p>Les modèles diffèrent notamment par leurs champs de vent, leurs grilles, leurs conditions initiales et la représentation des processus physiques. La résolution et la représentation de la côte influencent la valeur calculée près du littoral. Une maille plus fine n'est pas une garantie d'erreur plus faible.</p>
<h2>Heure de collecte et échéance</h2>
<p>Un modèle est recalculé par cycles. L'heure de collecte d'une réponse n'est pas nécessairement celle de l'initialisation du modèle. L'échéance est le délai séparant l'initialisation de l'heure prévue ; elle doit être distinguée de l'âge de la donnée affichée.</p>
<h2>Accord des modèles et erreur réelle</h2>
<p>Des modèles proches peuvent partager un biais. Pour mesurer l'erreur, il faut comparer des prévisions archivées à des observations correspondant au même point, à la même heure et à une échéance connue. L'écart absolu moyen et le biais répondent à deux questions différentes : amplitude de l'erreur et tendance à surestimer ou sous-estimer.</p>
<figure class="guide-figure"><svg viewBox="0 0 540 230" role="img" aria-label="Quatre prévisions proches de 2 mètres, observation à 1,4 mètre"><g font-size="15" fill="#F3EFE6"><text x="20" y="26">Hauteur significative · m</text><text x="25" y="72">Modèle A</text><text x="25" y="108">Modèle B</text><text x="25" y="144">Modèle C</text><text x="25" y="180">Bouée</text></g><g fill="#5795B7"><rect x="140" y="52" width="270" height="25" rx="3"/><rect x="140" y="88" width="297" height="25" rx="3"/><rect x="140" y="124" width="284" height="25" rx="3"/></g><rect x="140" y="160" width="189" height="25" rx="3" fill="#E9C694"/><g fill="#F3EFE6" font-size="15"><text x="419" y="71">2,0</text><text x="445" y="107">2,2</text><text x="433" y="143">2,1</text><text x="337" y="179">1,4</text></g></svg><figcaption>Exemple fictif, même lieu et heure. Les modèles sont proches entre eux mais surestiment l'observation.</figcaption></figure><p>Dans cet exemple, les trois prévisions s'étendent de 2,0 à 2,2 m, soit 0,2 m de dispersion au sens de l'étendue. Leur moyenne simple vaut 2,1 m, soit une surestimation de 0,7 m. Un seul exemple ne suffit pas pour classer les modèles : il faut une série de comparaisons à échéance identique.</p><h2>La correction par les bouées</h2>
<p>Houlalah utilise les observations de Gascogne pour ajuster ses hauteurs prévues lorsque les données le permettent. Cette correction ne démontre pas à elle seule une amélioration à tous les spots. Consulte la <a href="../../comment-ca-marche/">méthode Houlalah</a> pour le fonctionnement en vigueur et ses limites.</p>
<p><a href="../lire-une-bouee/">Lire une bouée</a> · <a href="../comprendre-la-houle/">Comprendre les variables de houle</a></p>
<h2>Sources</h2><p><a href="https://open-meteo.com/en/docs/marine-weather-api">Open-Meteo, modèles marins</a> · <a href="https://open-meteo.com/en/docs/model-updates">Cycles de mise à jour</a> · <a href="https://marc.ifremer.fr/">Ifremer MARC</a>.</p>
""",
}

ALL = [HOW, ABOUT, LEGAL, PRIVACY, GUIDE_INDEX, GUIDE_BUOY, GUIDE_SWELL, GUIDE_MODELS]


def render(site, spec):
    canonical = f"{site}/{spec['slug']}/"
    body = f"<h1>{spec['h1']}</h1>{spec['body']}"
    ld = [{"@context": "https://schema.org", "@type": spec.get("type", "WebPage"), "name": spec["title"], "description": spec["desc"], "url": canonical, "inLanguage": "fr",
           "isPartOf": {"@type": "WebSite", "name": BRAND, "url": site + "/"}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": BRAND, "item": site + "/"},
              {"@type": "ListItem", "position": 2, "name": spec["h1"], "item": canonical}]}]
    return page(site, spec["title"], spec["desc"], canonical, body, ld, base="../" * (spec["slug"].count("/") + 1), extra_css=".guide-figure{margin:24px 0;background:#0B1B26;border-radius:16px;padding:16px;color:#F3EFE6}.guide-figure svg{width:100%;height:auto;display:block}.guide-figure figcaption{font-size:13px;line-height:1.55;margin-top:12px;color:#F3EFE6}.guide-calc{background:var(--card);border-radius:16px;padding:18px;margin:24px 0}.guide-calc h2{margin-top:0}.guide-inputs{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}.guide-inputs fieldset{min-width:0;border:1px solid var(--edge);border-radius:12px;padding:12px}.guide-inputs label{display:block;margin:8px 0}.guide-inputs input{width:100%;font:inherit;padding:8px;border:1px solid #8a969b;border-radius:6px}.guide-inputs output{display:block;font-weight:800;font-size:22px;color:var(--navy)}" if spec["slug"].startswith("guide/") else "")
