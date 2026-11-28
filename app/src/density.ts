/** Densité et collisions des repères de la carte (P0 du porteur, 28/11), sans dépendance (testé par tests/regles_app.test.mjs).
 *  Trois niveaux de lecture selon le zoom :
 *   - « loin »    : un regroupement par région (nom + fourchette de la donnée affichée), les bouées en simples points ;
 *   - « milieu »  : pastilles lisibles choisies sans chevauchement, les autres spots en petits points ;
 *   - « près »    : pastilles détaillées (nom + valeurs), repli en pastille simple puis en point s'il n'y a pas la place.
 *  Le placement se calcule en pixels « monde » à l'échelle du PALIER de zoom (pas de la position) : un déplacement de la
 *  carte ne change rien, seul un changement de palier (avec hystérésis) recalcule. Aucun repère ne bouge : seul son aspect
 *  change, ce qui évite clignotements et déplacements intempestifs. */

export type Level = 'far' | 'mid' | 'near';
const FAR = 3.2, NEAR = 0.7;   // écart de longitude visible (degrés) : > 3,2 = loin ; < 0,7 = près

/** Niveau selon l'écart de longitude visible, avec 15 % d'hystérésis autour des seuils (pas d'aller-retour au pincement). */
export function levelOf(lonDelta: number, prev?: Level): Level {
  const h = 1.15;
  if (prev === 'far' && lonDelta > FAR / h) return 'far';
  if (prev === 'near' && lonDelta < NEAR * h) return 'near';
  if (prev === 'mid' && lonDelta <= FAR * h && lonDelta >= NEAR / h) return 'mid';
  return lonDelta > FAR ? 'far' : lonDelta < NEAR ? 'near' : 'mid';
}

/** Palier de zoom (demi-octaves) avec hystérésis : ne change que si l'on s'écarte de plus de 0,35 palier. */
export function bucketOf(lonDelta: number, prev?: number): number {
  const z = Math.log2(Math.max(1e-6, lonDelta)) * 2;
  return prev != null && Math.abs(z - prev) < 0.85 ? prev : Math.round(z);
}

/** Position en pixels « monde » (Mercator) pour une échelle donnée : px par degré de longitude. */
export function worldPx(lat: number, lon: number, pxPerDeg: number): [number, number] {
  const y = (Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) * 180) / Math.PI;
  return [lon * pxPerDeg, -y * pxPerDeg];
}

export type Box = { w: number; h: number; dx?: number; dy?: number };   // taille et décalage du rectangle par rapport au point
export type Item = { id: string; lat: number; lon: number; prio: number; sizes: Box[] };   // tailles par ordre de préférence

/** Placement glouton par priorité décroissante : chaque élément prend la PREMIÈRE taille qui ne chevauche rien de déjà
 *  placé (marge m), sinon -1 (il reste un point). `obstacles` : rectangles réservés d'abord (points des bouées…). */
export function place(items: Item[], pxPerDeg: number, m = 3, obstacles: Item[] = []): Record<string, number> {
  const cell = 64, grid = new Map<string, [number, number, number, number][]>();
  const keys = (r: [number, number, number, number]) => {
    const out: string[] = [];
    for (let gx = Math.floor(r[0] / cell); gx <= Math.floor(r[2] / cell); gx++)
      for (let gy = Math.floor(r[1] / cell); gy <= Math.floor(r[3] / cell); gy++) out.push(`${gx}:${gy}`);
    return out;
  };
  const rect = (it: Item, b: Box): [number, number, number, number] => {
    const [x, y] = worldPx(it.lat, it.lon, pxPerDeg), cx = x + (b.dx ?? 0), cy = y + (b.dy ?? 0);
    return [cx - b.w / 2 - m, cy - b.h / 2 - m, cx + b.w / 2 + m, cy + b.h / 2 + m];
  };
  const free = (r: [number, number, number, number]) => keys(r).every(k => !(grid.get(k) || []).some(o => r[0] < o[2] && r[2] > o[0] && r[1] < o[3] && r[3] > o[1]));
  const take = (r: [number, number, number, number]) => keys(r).forEach(k => { const a = grid.get(k); if (a) a.push(r); else grid.set(k, [r]); });
  obstacles.forEach(o => o.sizes.forEach(b => take(rect(o, b))));
  const res: Record<string, number> = {};
  [...items].sort((a, b) => b.prio - a.prio || (a.id < b.id ? -1 : 1)).forEach(it => {
    res[it.id] = -1;
    for (let k = 0; k < it.sizes.length; k++) { const r = rect(it, it.sizes[k]); if (free(r)) { take(r); res[it.id] = k; break; } }
  });
  return res;
}

/** Regroupements par région : position = spot le plus proche du centre (la pastille reste sur la côte), fourchette des
 *  valeurs, nombre de spots. */
export type Cluster = { region: string; lat: number; lon: number; n: number; min: number | null; max: number | null; bounds: [number, number, number, number] };
export function clusters<T extends { region: string; lat: number; lon: number }>(spots: T[], val: (s: T) => number | null | undefined): Cluster[] {
  const by = new Map<string, T[]>();
  spots.forEach(s => { const a = by.get(s.region); if (a) a.push(s); else by.set(s.region, [s]); });
  return [...by.entries()].map(([region, list]) => {
    const la = list.reduce((a, s) => a + s.lat, 0) / list.length, lo = list.reduce((a, s) => a + s.lon, 0) / list.length;
    const c = list.reduce((a, s) => ((s.lat - la) ** 2 + (s.lon - lo) ** 2 < (a.lat - la) ** 2 + (a.lon - lo) ** 2 ? s : a));
    const v = list.map(val).filter((x): x is number => x != null && Number.isFinite(x));
    return {
      region, lat: c.lat, lon: c.lon, n: list.length, min: v.length ? Math.min(...v) : null, max: v.length ? Math.max(...v) : null,
      bounds: [Math.min(...list.map(s => s.lat)), Math.min(...list.map(s => s.lon)), Math.max(...list.map(s => s.lat)), Math.max(...list.map(s => s.lon))],
    };
  });
}
