// Données de l'appli : les fichiers allégés que le robot publie avec le site (web/data/app/).
// En développement, EXPO_PUBLIC_DATA_URL peut pointer vers le serveur local du PC.
import AsyncStorage from '@react-native-async-storage/async-storage';

export const DATA_URL = (process.env.EXPO_PUBLIC_DATA_URL || 'https://houlalah.fr/data/app').replace(/\/$/, '');

export type Now = { t: string | null; hs: number | null; tp: number | null; dir: number | null; wind: number | null; wdir: number | null };
export type SpotLite = { name: string; slug: string; region: string; commune?: string; lat: number; lon: number; ori?: number; now: Now };
export type Buoy = { id: string; slug: string; name: string; sub: string; lat: number; lon: number; large?: boolean; time: string; hs: number; tp?: number | null; tm?: number | null; dir?: number | null; sst?: number | null };
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
/** Bouées de référence par région : les Landes se comparent à la Gascogne ou à Cap Ferret seulement (pipeline/config.py : REGION_BUOYS). */
const REGION_BUOYS: Record<string, string[]> = { Landes: ['Cap Ferret', 'Gascogne'] };
export const buoyFits = (b: { name: string }, spot: { name: string; region?: string }) =>
  (!BUOY_ONLY[b.name] || BUOY_ONLY[b.name].includes(spot.name)) && (!spot.region || !REGION_BUOYS[spot.region] || REGION_BUOYS[spot.region].includes(b.name));

export const ageH =(t: string) => (Date.now() - new Date(t + ':00').getTime()) / 36e5;
export function ageTxt(t: string) {
  const h = (Date.now() - new Date(t + ':00').getTime()) / 36e5;
  return h < 1 ? "à l'instant" : h < 36 ? `il y a ${Math.round(h)} h` : `il y a ${Math.round(h / 24)} j`;
}
export const JOURS = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
