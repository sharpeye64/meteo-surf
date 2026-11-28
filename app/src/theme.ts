// Direction artistique de Houlalah, reprise du site (thème clair mobile) : encre marine, gris d'eau, sable du logo,
// polices Unbounded (chiffres, titres) et Manrope (texte), cases colorées de la frise horaire.
// Deux palettes de mêmes clés : claire, et sombre (fond nuit de l'icône et du site). L'appli suit le réglage du téléphone.
const LIGHT = {
  ink: '#0b1b26',            // bleu nuit Premium Ocean (prévisions, textes)
  ink2: '#5d6a70',
  ink3: '#7d8a90',
  bg: '#f3efe6',             // sable (fond)
  card: '#fffdf8',           // crème (cartes)
  soft: '#efe9dc',
  line: 'rgba(11,27,38,0.10)',
  night: '#0b1b26',          // surfaces nuit (bouées, bulle d'onglet active)
  onNight: '#f3efe6',
  measure: '#8a6418',        // or des MESURES réelles, sur clair (rien d'autre n'est doré)
  measureOnNight: '#f2c66b',
  sand: '#e9c694',          // sable du logo (accent : anneaux des bouées, onglet actif)
  sandA: '#f4e2b8',
  sandB: '#e3c283',
  sandText: '#2a2112',
  gold: '#8a6418',
  live: '#12925a',
  off: '#1f8a7c', side: '#5b6b75', on: '#c0582f',   // orientation du vent (comme le site)
  aqua: '#3f8f80',
  coral: '#c9644a',
  sandCard: '#e9c694',      // fond des grandes cartes sable (votre spot, bouée de votre spot)
  sandMuted: '#7a5f33',     // petits textes sur sable
  sandMuted2: '#6b5a33',
  pill: '#e3c283',          // pastilles de valeur (hauteur mesurée)
  sunTile: '#f4e2b8',
  cream: '#f4efe3',         // pastilles du bandeau « Bouées en direct »
  creamText: '#7a6f55',
  creamText2: '#a89c7e',
  water: '#dcebf3', waterK: '#3d6a82', waterT: '#123c55',
  tideFill: '#e3ebf1',
  glass: 'rgba(255,253,248,0.94)',   // boutons flottants et barre d'onglets
  map: '#b4ccd8',
  onInk: '#ffffff', onInk2: 'rgba(255,255,255,0.7)',
  cellU: 'rgba(16,32,44,0.7)',
  lampOld: '#c9c3b4',
  // Surfaces « mesure en mer » (cartes bouée) : MÊMES valeurs en clair et en sombre, exception voulue (or = mesure, D11)
  buoySurface: '#0b1b26', onBuoy: 'rgba(243,239,230,0.78)', onBuoy2: 'rgba(243,239,230,0.55)', measureOnBuoy: '#f2c66b', liveOnBuoy: '#2fc48a',
  warn: '#a4501f', warnBg: '#f6dfcc',   // données anciennes (jamais une note de surf)
};
type Palette = typeof LIGHT;
const DARK: Palette = {
  ink: '#f3efe6',
  ink2: '#aebac0',
  ink3: '#7d8f98',
  bg: '#0b1620',
  card: '#16242c',
  soft: '#1d2c35',
  line: 'rgba(243,239,230,0.10)',
  night: '#f3efe6',          // en sombre, la bulle active est crème
  onNight: '#0b1b26',
  measure: '#f2c66b',
  measureOnNight: '#f2c66b',
  sand: '#e9c694',
  sandA: '#f4e2b8',
  sandB: '#c9a463',
  sandText: '#f1d9ad',
  gold: '#f2c66b',
  live: '#2fc48a',
  off: '#4fc2b0', side: '#9fb0b8', on: '#e07a5f',
  aqua: '#5fb3a2',
  coral: '#e07a5f',
  sandCard: '#2a2318',
  sandMuted: '#c9a463',
  sandMuted2: '#b89b68',
  pill: '#45391f',
  sunTile: '#2a2318',
  cream: '#232019',
  creamText: '#b5a684',
  creamText2: '#8a7f66',
  water: '#122a3a', waterK: '#8bb6cc', waterT: '#d3e9f4',
  tideFill: '#1a2c38',
  glass: 'rgba(24,40,49,0.92)',
  map: '#0c1e2a',
  onInk: '#0a1114', onInk2: 'rgba(10,17,20,0.7)',
  cellU: 'rgba(232,238,241,0.72)',
  lampOld: '#4a5357',
  buoySurface: '#0b1b26', onBuoy: 'rgba(243,239,230,0.78)', onBuoy2: 'rgba(243,239,230,0.55)', measureOnBuoy: '#f2c66b', liveOnBuoy: '#2fc48a',
  warn: '#f0a271', warnBg: '#3a2418',
};

export type Mode = 'light' | 'dark';
let mode: Mode = 'light';
/** Couleurs courantes : l'objet est mis à jour sur place quand le téléphone passe en clair ou en sombre. */
export const C: Palette = { ...LIGHT };
export const isDark = () => mode === 'dark';
export function setMode(m: Mode) {
  if (m === mode) return;
  mode = m;
  Object.assign(C, m === 'dark' ? DARK : LIGHT);
}
/** Feuille de styles recalculée pour chaque mode (à la première utilisation), lue comme une feuille ordinaire : `st.titre`. */
export function themed<T extends object>(make: () => T): T {
  const cache: Partial<Record<Mode, T>> = {};
  return new Proxy({} as T, { get: (_, k) => (cache[mode] ??= make())[k as keyof T] });
}
export const F = {
  num: 'Unbounded_700Bold',
  numX: 'Unbounded_800ExtraBold',
  numM: 'Unbounded_500Medium',
  t: 'Manrope_600SemiBold',
  tR: 'Manrope_500Medium',
  tB: 'Manrope_700Bold',
  tX: 'Manrope_800ExtraBold',
};

// Mêmes échelles que la frise du site (web/index.html : SZ_ST, PE_ST, WI_ST), en teinte / saturation / luminosité.
type Stop = [number, number, number, number];
const SZ: Stop[] = [[0, 195, 60, 88], [0.5, 195, 65, 78], [1, 205, 75, 68], [1.5, 218, 80, 64], [2, 250, 70, 68], [3, 285, 65, 66], [4, 320, 70, 64]];
const PE: Stop[] = [[4, 60, 25, 90], [7, 90, 40, 82], [10, 130, 48, 72], [13, 150, 52, 64], [16, 165, 55, 56]];
const WI: Stop[] = [[0, 200, 35, 92], [6, 198, 60, 82], [14, 160, 48, 74], [22, 110, 52, 72], [30, 52, 78, 70], [40, 28, 85, 64], [55, 6, 72, 58]];
// En sombre, même teinte mais luminosité inversée : les petites valeurs se fondent dans la nuit, les grosses ressortent.
const lum = (l: number) => (mode === 'dark' ? Math.round(20 + (90 - l) * 0.8) : Math.round(l));
const sat = (s: number) => Math.round(mode === 'dark' ? s * 0.7 : s);   // un peu moins vif la nuit, pour ne pas éblouir
function stops(v: number | null | undefined, st: Stop[]) {
  if (v == null || isNaN(v)) return 'transparent';
  if (v <= st[0][0]) v = st[0][0];
  for (let i = 1; i < st.length; i++) {
    if (v <= st[i][0]) {
      const a = st[i - 1], b = st[i], t = (v - a[0]) / (b[0] - a[0]), l = (x: number, y: number) => x + (y - x) * t;
      return `hsl(${l(a[1], b[1]).toFixed(0)}, ${sat(l(a[2], b[2]))}%, ${lum(l(a[3], b[3]))}%)`;
    }
  }
  const z = st[st.length - 1]; return `hsl(${z[1]}, ${sat(z[2])}%, ${lum(z[3])}%)`;
}
export const sizeCell = (h?: number | null) => stops(h, SZ);
export const periodCell = (t?: number | null) => stops(t, PE);
export const windCell = (v?: number | null) => stops(v, WI);
