import { tMs } from './time';
import { ageWords, BUOY_ONLY, candidates, Fresh, freshState, liveLim, pickRef, WIND_WORD, WindCat, windCat } from './rules';
export { dayTxt } from './rules';
export { windCat, WIND_WORD } from './rules';
export type { Fresh, WindCat } from './rules';
// Données de l'appli : les fichiers allégés que le robot publie avec le site (web/data/app/).
// En développement, EXPO_PUBLIC_DATA_URL peut pointer vers le serveur local du PC.
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createCachedLoader } from './cache';

export const DATA_URL = (process.env.EXPO_PUBLIC_DATA_URL || 'https://houlalah.fr/data/app').replace(/\/$/, '');

export type Now = { t: string | null; hs: number | null; tp: number | null; dir: number | null; wind: number | null; wdir: number | null };
export type SpotLite = { name: string; slug: string; region: string; commune?: string; tz?: string | null; ref?: string | null; lat: number; lon: number; pt?: [number, number]; ori?: number; now: Now };
export type Buoy = { id: string; slug: string; name: string; sub: string; lat: number; lon: number; tz?: string | null; large?: boolean; silent?: boolean; kind?: 'gascogne' | 'coast' | 'offshore'; lim?: number; time: string; hs: number; tp?: number | null; tm?: number | null; dir?: number | null; sst?: number | null };
/** Période d'une bouée : la période pic si elle est mesurée, sinon la période MOYENNE (Gascogne, Météo-France), dite comme telle. */
export const perTxt = (b: { tp?: number | null; tm?: number | null }) => (b.tp ? `${Math.round(b.tp)} s` : b.tm ? `${Math.round(b.tm)} s moy.` : '');
export type Index = { v: number; generated: string; spots: SpotLite[]; buoys: Buoy[] };
export type Obs = { t: string; hs: number | null; tp?: number | null; dir?: number | null; hmax?: number | null; sst?: number | null };
export type BuoySheet = {
  id: string; slug: string; name: string; sub: string; lat: number; lon: number; tz?: string | null; lim?: number; silent?: boolean;
  latest: { time: string; hs: number; hmax?: number | null; tp?: number | null; tm?: number | null; dir?: number | null; sst?: number | null };
  obs: Obs[]; model: { t: string; hs: number | null }[]; model_src: string;
  stats: { since: string; days: number; hs_max: number; hs_max_t: string; hs_mean: number; sst_mean?: number | null } | null;
  spots: { name: string; slug: string; km: number }[];
};
export type TideEx = { t: string; type: 'PM' | 'BM'; h: number };
export type Sheet = {
  name: string; slug: string; region: string; commune?: string; tz?: string | null; lat: number; lon: number; ori?: number;
  t0: string; hs: (number | null)[]; tp: (number | null)[]; dir: (number | null)[]; sw: (number | null)[]; swp: (number | null)[];
  wind: (number | null)[]; gust: (number | null)[]; wdir: (number | null)[]; sea: (number | null)[]; sst: (number | null)[];
  tide: { port: string; label: string; extremes: TideEx[] } | null;
  sun: { time: string[]; sunrise: string[]; sunset: string[] } | null;
};

// copie hors connexion : une réponse lente d'une demande plus ancienne n'écrase jamais une copie plus récente (src/cache.ts)
const getJSON = createCachedLoader(async (path: string) => {
  const r = await fetch(`${DATA_URL}/${path}?v=${Math.floor(Date.now() / 6e5)}`);
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}, AsyncStorage);

export const loadIndex = () => getJSON<Index>('index.json', 'cache:index');
export const loadBuoy = (slug: string) => getJSON<BuoySheet>(`bouees/${slug}.json`, `cache:buoy:${slug}`);
export const loadSheet = (slug: string) => getJSON<Sheet>(`spots/${slug}.json`, `cache:spot:${slug}`);
/** Même fiche, sans nouvelle requête si elle a été reçue il y a moins de 10 min (préchargement des favoris, Ma côte,
 *  comparateur) : une seule demande réseau par fiche et par passage du robot, au lieu d'une par écran. */
const memSheets = new Map<string, { at: number; p: Promise<{ data: Sheet; offline: boolean }> }>();
export function loadSheetShared(slug: string, maxAgeMs = 6e5) {
  const m = memSheets.get(slug);
  if (m && Date.now() - m.at < maxAgeMs) return m.p;
  const p = loadSheet(slug);
  memSheets.set(slug, { at: Date.now(), p });
  p.then(r => { if (r.offline) memSheets.delete(slug); }, () => memSheets.delete(slug));   // copie hors connexion ou échec : on réessaiera
  return p;
}

export async function loadFavs(): Promise<string[]> {
  try { return JSON.parse((await AsyncStorage.getItem('favs')) || '[]'); } catch { return []; }
}
export async function saveFavs(f: string[]) { try { await AsyncStorage.setItem('favs', JSON.stringify(f)); } catch {} }

// ---------- petites fonctions d'affichage ----------
export { SECT, sector } from './rules';   // règle commune avec le site et le robot
export const fr = (v?: number | null, nd = 1) => (v == null ? '—' : v.toFixed(nd).replace('.', ','));
export function sizeCol(h?: number | null) {
  const ST: [number, string][] = [[0, '#9ed8f0'], [0.6, '#43b8c9'], [1.2, '#6bc46d'], [1.8, '#e8d54a'], [2.4, '#f39a2b'], [3.2, '#e24a3b']];
  let c = ST[0][1]; for (const [k, v] of ST) if ((h ?? 0) >= k) c = v; return c;
}
export const country = (r: string) => (/^Portugal/.test(r) ? 'Portugal' : r === 'Espagne Nord' || r === 'Galice' ? 'Espagne' : 'France');
export const regionName = (r: string) => r.replace('Pays Basque', 'Pays basque').replace('Espagne Nord', 'Espagne du Nord');

/** Vent rapporté à l'orientation du spot, en mots (règle commune avec le site : src/rules.ts, windCat). */
export const windText = (c: WindCat | null) => (c == null ? null : c === 'lisse' ? 'Plan d’eau lisse' : `Vent ${WIND_WORD[c].toLowerCase()}`);
/** Bouées abritées : elles ne valent que pour les spots listés (src/rules.ts : BUOY_ONLY). */
export const buoyFits = (b: { name: string }, spotName: string) => !BUOY_ONLY[b.name] || BUOY_ONLY[b.name].includes(spotName);

/** Distance en km entre deux points (assez précis à l'échelle de la côte). */
export const km = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => {
  const r = Math.PI / 180, x = (b.lon - a.lon) * r * Math.cos(((a.lat + b.lat) / 2) * r), y = (b.lat - a.lat) * r;
  return Math.sqrt(x * x + y * y) * 6371;
};

/** Type de station (règles communes) : champ « kind » du robot ; à défaut (ancien fichier en cache), d'après l'identifiant. */
export const buoyKind = (b: { id: string; kind?: Buoy['kind'] }): NonNullable<Buoy['kind']> =>
  b.kind || (b.id === 'gascogne' ? 'gascogne' : /^0\d{4}$/.test(b.id) ? 'coast' : 'offshore');
/** Fraîcheur d'une mesure, selon la cadence de SA station (règle commune avec le site et le robot : src/rules.ts).
 *  L'âge est recalculé à chaque affichage, y compris sur des données en cache hors connexion. */
export const freshOf = (b: { id: string; lim?: number | null; time: string; silent?: boolean }): Fresh => freshState(ageH(b.time), liveLim(b), !!b.silent);
export const isLive = (b: { id: string; lim?: number | null; time: string; silent?: boolean }) => freshOf(b) === 'live';

/** Bouée de référence d'un spot : MÊME règle que le site (src/rules.ts : candidates + pickRef ; web/index.html : buoyChoices +
 *  pickBuoy) : Landes (Cap Ferret au nord, Gascogne ailleurs, D9), Sainte-Barbe réservée à son spot, puis la plus proche en
 *  direct à 60 km au plus, puis la plus proche de moins de 6 h, puis la plus fraîche. Distances depuis le point du spot (pt). */
/** Point du spot pour les distances aux bouées : point de prévision (« pt ») si le point affiché est recalé sur la côte. */
export const spotPoint = (spot: SpotLite) => ({ name: spot.name, region: spot.region, lat: spot.pt ? spot.pt[0] : spot.lat, lon: spot.pt ? spot.pt[1] : spot.lon });
export { hav } from './rules';

export function refBuoy(buoys: Buoy[], spot: SpotLite): { b: Buoy; k: number } | null {
  const s = spotPoint(spot);
  const list = candidates(s, buoys.map(b => ({ ...b, kind: buoyKind(b), ageH: ageH(b.time), lim: liveLim(b) })));
  const r = pickRef(list);
  return r ? { b: r.b, k: r.km } : null;
}

// âge d'une mesure en INSTANTS (issue #2) : heures publiées avec décalage ; l'ancien format est lu comme heure de Paris
export const ageH = (t: string) => (Date.now() - tMs(t)) / 36e5;
/** Âge d'une mesure en mots (règle commune : src/rules.ts, ageWords) ; heure incohérente ou illisible dite comme telle. */
export const ageTxt = (t: string) => ageWords(ageH(t), t);
export const JOURS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
