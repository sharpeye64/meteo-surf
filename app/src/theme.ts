// Direction artistique de Houlalah, reprise du site (thème clair mobile) : encre marine, gris d'eau, sable du logo,
// polices Unbounded (chiffres, titres) et Manrope (texte), cases colorées de la frise horaire.
export const C = {
  ink: '#10202c',
  ink2: '#5b6b75',
  ink3: '#8a98a0',
  bg: '#eef1f2',
  card: '#ffffff',
  soft: '#f4f6f7',
  line: 'rgba(16,32,44,0.10)',
  sand: '#e9c694',
  sandA: '#f4e2b8',
  sandB: '#e3c283',
  sandText: '#2a2112',
  gold: '#b8892f',
  live: '#2fb47c',
  aqua: '#3f8f80',
  coral: '#c9644a',
};
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
function stops(v: number | null | undefined, st: Stop[]) {
  if (v == null || isNaN(v)) return 'transparent';
  if (v <= st[0][0]) v = st[0][0];
  for (let i = 1; i < st.length; i++) {
    if (v <= st[i][0]) {
      const a = st[i - 1], b = st[i], t = (v - a[0]) / (b[0] - a[0]), l = (x: number, y: number) => (x + (y - x) * t).toFixed(0);
      return `hsl(${l(a[1], b[1])}, ${l(a[2], b[2])}%, ${l(a[3], b[3])}%)`;
    }
  }
  const z = st[st.length - 1]; return `hsl(${z[1]}, ${z[2]}%, ${z[3]}%)`;
}
export const sizeCell = (h?: number | null) => stops(h, SZ);
export const periodCell = (t?: number | null) => stops(t, PE);
export const windCell = (v?: number | null) => stops(v, WI);
