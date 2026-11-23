// Données de l'appli : les fichiers allégés que le robot publie avec le site (web/data/app/).
// En développement, EXPO_PUBLIC_DATA_URL peut pointer vers le serveur local du PC.
import AsyncStorage from '@react-native-async-storage/async-storage';

export const DATA_URL = (process.env.EXPO_PUBLIC_DATA_URL || 'https://houlalah.fr/data/app').replace(/\/$/, '');

export type Now = { t: string | null; hs: number | null; tp: number | null; dir: number | null; wind: number | null; wdir: number | null };
export type SpotLite = { name: string; slug: string; region: string; commune?: string; ref?: string | null; lat: number; lon: number; ori?: number; now: Now };
export type Buoy = { id: string; slug: string; name: string; sub: string; lat: number; lon: number; large?: boolean; silent?: boolean; time: string; hs: number; tp?: number | null; tm?: number | null; dir?: number | null; sst?: number | null };
/** Période d'une bouée : la période pic si elle est mesurée, sinon la période MOYENNE (Gascogne, Météo-France), dite comme telle. */
export const perTxt = (b: { tp?: number | null; tm?: number | null }) => (b.tp ? `${Math.round(b.tp)} s` : b.tm ? `${Math.round(b.tm)} s moy.` : '');
export type Index = { v: number; generated: string; spots: SpotLite[]; buoys: Buoy[] };
export type Obs = { t: string; hs: number | null; tp?: number | null; dir?: number | null; hmax?: number | null; sst?: number | null };
export type BuoySheet = {
  id: string; slug: string; name: string; sub: string; lat: number; lon: number;
  latest: { time: string; hs: number; hmax?: number | null; tp?: number | null; tm?: number | null; dir?: number | null; sst?: number | null };
  obs: Obs[]; model: { t: string; hs: number | null }[]; model_src: string;
  stats: { since: string; days: number; hs_max: number; hs_max_t: string; hs_mean: number; sst_mean?: number | null } | null;
  spots: { name: string; slug: string; km: number }[];
};
export type TideEx = { t: string; type: 'PM' | 'BM'; h: number };
export type Sheet = {
  name: string; slug: string; region: string; commune?: string; lat: number; lon: number; ori?: number;
  t0: string; hs: (number | null)[]; tp: (number | null)[]; dir: (number | null)[]; sw: (number | null)[]; swp: (number | null)[];
  wind: (number | null)[]; gust: (number | null)[]; wdir: (number | null)[]; sea: (number | null)[]; sst: (number | null)[];
  tide: { port: string; label: string; extremes: TideEx[] } | null;
  sun: { time: string[]; sunrise: string[]; sunset: string[] } | null;
};

async function getJSON<T>(path: string, cacheKey: string): Promise<{ data: T; offline: boolean }> {
  try {
    const r = await fetch(`${DATA_URL}/${path}?v=${Math.floor(Date.now() / 6e5)}`);
    if (!r.ok) throw new Error(String(r.status));
    const data = (await r.json()) as T;
    AsyncStorage.setItem(cacheKey, JSON.stringify(data)).catch(() => {});
    return { data, offline: false };
  } catch (e) {
    const c = await AsyncStorage.getItem(cacheKey).catch(() => null);   // hors connexion : dernière version reçue
    if (c) return { data: JSON.parse(c) as T, offline: true };
    throw e;
  }
}

export const loadIndex = () => getJSON<Index>('index.json', 'cache:index');
export const loadBuoy = (slug: string) => getJSON<BuoySheet>(`bouees/${slug}.json`, `cache:buoy:${slug}`);
export const loadSheet = (slug: string) => getJSON<Sheet>(`spots/${slug}.json`, `cache:spot:${slug}`);

export async function loadFavs(): Promise<string[]> {
  try { return JSON.parse((await AsyncStorage.getItem('favs')) || '[]'); } catch { return []; }
}
export async function saveFavs(f: string[]) { try { await AsyncStorage.setItem('favs', JSON.stringify(f)); } catch {} }

// ---------- petites fonctions d'affichage ----------
export const SECT = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO'];
export const sector = (d?: number | null) => (d == null ? '—' : SECT[Math.round(((d % 360) + 360) % 360 / 22.5) % 16]);
export const fr = (v?: number | null, nd = 1) => (v == null ? '—' : v.toFixed(nd).replace('.', ','));
export function sizeCol(h?: number | null) {
  const ST: [number, string][] = [[0, '#9ed8f0'], [0.6, '#43b8c9'], [1.2, '#6bc46d'], [1.8, '#e8d54a'], [2.4, '#f39a2b'], [3.2, '#e24a3b']];
  let c = ST[0][1]; for (const [k, v] of ST) if ((h ?? 0) >= k) c = v; return c;
}
export const country = (r: string) => (/^Portugal/.test(r) ? 'Portugal' : r === 'Espagne Nord' || r === 'Galice' ? 'Espagne' : 'France');
export const regionName = (r: string) => r.replace('Pays Basque', 'Pays basque').replace('Espagne Nord', 'Espagne du Nord');

/** Vent de terre / de mer / de travers, d'après l'orientation de la plage (ori = direction vers le large). */
export function windRel(wdir?: number | null, ori?: number) {
  if (wdir == null || ori == null) return null;
  const d = Math.abs((((wdir - ori) % 360) + 540) % 360 - 180);   // 0 = le vent vient du large, 180 = il vient de la terre
  return d >= 120 ? 'de terre' : d <= 60 ? 'de mer' : 'de travers';
}
/** Bouées abritées : elles ne valent que pour les spots listés (même règle que pipeline/config.py : BUOY_ONLY). */
const BUOY_ONLY: Record<string, string[]> = { 'Saint-Jean-de-Luz': ['Sainte Barbe'] };
export const buoyFits = (b: { name: string }, spotName: string) => !BUOY_ONLY[b.name] || BUOY_ONLY[b.name].includes(spotName);

/** Distance en km entre deux points (assez précis à l'échelle de la côte). */
export const km = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => {
  const r = Math.PI / 180, x = (b.lon - a.lon) * r * Math.cos(((a.lat + b.lat) / 2) * r), y = (b.lat - a.lat) * r;
  return Math.sqrt(x * x + y * y) * 6371;
};

/** Bouée de référence par défaut, calculée par le robot (champ « ref » : Landes, Cap Ferret au nord, Gascogne ailleurs,
 *  pipeline/config.py : ref_buoy). Prise si sa mesure a moins de 6 h ; Cap Ferret trop ancienne → la Gascogne. */
export function prefBuoy(buoys: Buoy[], spot: { ref?: string | null }): Buoy | null {
  if (!spot.ref) return null;
  const ids = spot.ref === 'gascogne' ? ['gascogne'] : [spot.ref, 'gascogne'];
  return ids.map(id => buoys.find(b => b.id === id)).find((b): b is Buoy => !!b && ageH(b.time) < 6) || null;
}

export const ageH =(t: string) => (Date.now() - new Date(t + ':00').getTime()) / 36e5;
/** « le 18/11 » : date d'une mesure (bouée muette). */
export const dayTxt = (t: string) => `le ${t.slice(8, 10)}/${t.slice(5, 7)}`;
export function ageTxt(t: string) {
  const h = (Date.now() - new Date(t + ':00').getTime()) / 36e5;
  // au-delà de 2 jours (bouée muette, en panne) : la date de la dernière mesure, plus parlante que « il y a 5 j »
  return h < 1 ? "à l'instant" : h < 48 ? `il y a ${Math.round(h)} h` : dayTxt(t);
}
export const JOURS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
