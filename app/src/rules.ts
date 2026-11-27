/** Règles métier communes au site, à l'appli et au robot (issue #4). Aucune dépendance : le test commun
 *  (tests/regles_communes.json, lancé par tests/regles_app.test.mjs) les exécute directement avec Node.
 *  Toute modification ici doit être faite aussi dans web/index.html (pvLim, pvFresh, windInfo, buoyChoices, pickBuoy) et dans
 *  le robot (pipeline/bouees.py : station, fresh_state ; pipeline/seo.py : wind_for_spot), puis vérifiée par le test commun.
 *  Détail : docs/regles-communes.md. */

// ---------- Fraîcheur d'une mesure de bouée, selon la cadence de la station ----------
/** Âge (h) jusqu'auquel une mesure est « en direct » : 1 h pour les houlographes CANDHIS (une mesure toutes les 30 min),
 *  2 h pour les bouées horaires (Météo-France 62001, Copernicus). Le robot l'écrit dans les données (« lim ») ; à défaut
 *  (ancien fichier en cache), même règle que le site : identifiant CANDHIS à 5 chiffres commençant par 0. */
export const liveLim = (b: { id?: string | null; lim?: number | null }) => (b.lim ? b.lim : /^0\d{4}$/.test(String(b.id ?? '')) ? 1 : 2);

export type Fresh = 'live' | 'recent' | 'old' | 'off';
/** Tolérance d'horloge : une mesure datée jusqu'à 15 min dans le futur (horloge du téléphone en retard) vaut « à l'instant ».
 *  Au-delà, l'heure est incohérente : jamais « en direct ». */
export const CLOCK_SKEW_H = 0.25;
/** en direct < lim, récente < 3 × lim, ancienne < 48 h, muette au-delà (ou bouée signalée muette par le robot). */
export function freshState(ageH: number, lim: number, silent = false): Fresh {
  if (silent || !(ageH === ageH)) return 'off';
  if (ageH < -CLOCK_SKEW_H) return 'old';
  const a = Math.max(0, ageH);
  return a < lim ? 'live' : a < 3 * lim ? 'recent' : a < 48 ? 'old' : 'off';
}

// ---------- Direction en 16 secteurs (d'où vient la houle ou le vent) : site sector, robot seo.sector ----------
export const SECT = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO'];
export const sector = (d?: number | null) => (d == null ? '—' : SECT[Math.round(((d % 360) + 360) % 360 / 22.5) % 16]);

// ---------- Vent rapporté à l'orientation du spot ----------
export type WindCat = 'lisse' | 'offshore' | 'side-off' | 'de côté' | 'onshore';
/** Mêmes catégories et mêmes seuils que le site (windInfo) et le robot (seo.wind_for_spot).
 *  ori = direction vers le large ; le vent offshore vient donc de ori + 180°. Moins de 8 km/h : plan d'eau lisse.
 *  Donnée absente (vitesse, direction ou orientation) : null, jamais « lisse ». */
export function windCat(v?: number | null, wdir?: number | null, ori?: number | null): WindCat | null {
  if (v == null || wdir == null || ori == null) return null;
  if (v < 8) return 'lisse';
  const x = Math.abs((((wdir - (ori + 180)) % 360) + 360) % 360), d = x > 180 ? 360 - x : x;
  return d <= 45 ? 'offshore' : d <= 80 ? 'side-off' : d <= 120 ? 'de côté' : 'onshore';
}
/** Mots affichés, les mêmes que sur le site (windWord). */
export const WIND_WORD: Record<WindCat, string> = { lisse: 'Lisse', offshore: 'Offshore', 'side-off': 'Side-offshore', 'de côté': 'Side-shore', onshore: 'Onshore' };

// ---------- Bouée de référence d'un spot ----------
/** Bouées abritées : elles ne valent que pour les spots listés (pipeline/config.py : BUOY_ONLY ; site : BUOY_ONLY). */
export const BUOY_ONLY: Record<string, string[]> = { 'Saint-Jean-de-Luz': ['Sainte Barbe'] };
/** Nord des Landes : Cap Ferret jusqu'à 70 km (pipeline/config.py : LANDES_CF_KM ; site : LANDES_CF_KM). */
export const LANDES_CF_KM = 70;

/** Distance (km), même formule que le site (hav). */
export function hav(a: { lat: number; lon: number }, b: { lat: number; lon: number }) {
  const r = Math.PI / 180, dl = (b.lat - a.lat) * r, dn = (b.lon - a.lon) * r;
  const x = Math.sin(dl / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dn / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(x));
}

/** Bouée telle que les règles la voient. kind : 'gascogne' (Météo-France 62001), 'coast' (houlographe CANDHIS), 'offshore' (Copernicus). */
export type RBuoy = { id: string; name: string; sub?: string; lat: number; lon: number; kind: 'gascogne' | 'coast' | 'offshore'; ageH: number; lim: number; hs?: number | null };
export type RSpot = { name: string; region: string; lat: number; lon: number };
export type Cand<B extends RBuoy> = { b: B; km: number; pref: number | null };

/** Rang de préférence (Landes, D9) : Cap Ferret au nord (≤ 70 km), puis Gascogne ; null ailleurs. */
export function prefRank(s: RSpot, c: { b: RBuoy; km: number }) {
  if (s.region !== 'Landes') return null;
  if (c.b.name === 'Cap Ferret' && c.km <= LANDES_CF_KM) return 0;
  if (c.b.id === 'gascogne') return 1;
  return null;
}

/** Bouées proposées pour un spot, de la plus proche à la plus lointaine (site : buoyChoices). */
export function candidates<B extends RBuoy>(s: RSpot, buoys: B[]): Cand<B>[] {
  const ok = buoys.filter(b => b.hs !== null);
  const out: Cand<B>[] = [];
  for (const b of ok.filter(x => x.kind === 'gascogne')) { const k = hav(s, b); if (k < 450) out.push({ b, km: k, pref: null }); }
  for (const b of ok.filter(x => x.kind === 'offshore')) {
    const k = hav(s, b);
    if (b.id === 'donostia' && k > 80) continue;
    if (k > 300 || (/côte/.test(b.sub || '') && k > 130)) continue;
    out.push({ b, km: k, pref: null });
  }
  const coast = ok.filter(x => x.kind === 'coast' && (!BUOY_ONLY[x.name] || BUOY_ONLY[x.name].includes(s.name)))
    .map(b => ({ b, km: hav(s, b) })).sort((x, y) => x.km - y.km)[0];
  if (coast && coast.km <= 130) out.push({ ...coast, pref: null });   // la bouée côtière la plus proche, à 130 km au plus
  if (s.region === 'Landes') {   // nord des Landes : Cap Ferret toujours proposée
    const cf = ok.find(x => x.kind === 'coast' && x.name === 'Cap Ferret'), k = cf && hav(s, cf);
    if (cf && k! <= LANDES_CF_KM && !out.some(o => o.b.id === cf.id)) out.push({ b: cf, km: k!, pref: null });
  }
  out.forEach(o => { o.pref = prefRank(s, o); });
  out.sort((x, y) => x.km - y.km);
  if (out.length > 5) {   // les 5 plus proches suffisent, en gardant la bouée de référence
    const keep = out.filter((o, i) => i < 5 || o.pref != null);
    while (keep.length > 5) { const j = keep.map(o => o.pref == null).lastIndexOf(true); if (j < 0) break; keep.splice(j, 1); }
    return keep;
  }
  return out;
}

/** Bouée affichée par défaut (site : pickBuoy, hors choix fait à la main) :
 *  1. bouée de référence des Landes, si sa mesure a moins de 6 h ;
 *  2. la plus proche EN DIRECT (selon sa cadence), à 60 km au plus ;
 *  3. la plus proche dont la mesure a moins de 6 h ;
 *  4. sinon la plus fraîche. Une bouée muette n'est jamais choisie tant qu'une autre a une mesure. */
export function pickRef<B extends RBuoy & { silent?: boolean }>(list: Cand<B>[]): Cand<B> | null {
  if (!list.length) return null;
  const pf = list.filter(o => o.pref != null && o.b.ageH < 6).sort((x, y) => x.pref! - y.pref!)[0]; if (pf) return pf;
  const live = list.filter(o => o.km <= 60 && freshState(o.b.ageH, o.b.lim, o.b.silent) === 'live')[0]; if (live) return live;
  const fresh = list.filter(o => o.b.ageH < 6 && !o.b.silent)[0]; if (fresh) return fresh;
  const talk = list.filter(o => !o.b.silent);
  return (talk.length ? talk : list).slice().sort((x, y) => x.b.ageH - y.b.ageH)[0];
}
