/** Lecture des séries horaires et âge des données, sans dépendance (testé par tests/heures_app.test.mjs).
 *  Revue de René (PR #23) : une valeur n'est rendue que pour un ÉCHANTILLON EXACT de la série (pas d'arrondi à l'heure
 *  voisine, pas d'interpolation silencieuse) ; les jours se comptent en jours CIVILS du fuseau, jamais par sauts de 24 h. */
/** Valeur d'une série horaire (début t0, pas d'une heure) à l'instant ms, à 1 seconde près ; null sinon (hors série,
 *  minutes décalées, valeur absente). */
export function valueAt(t0: number, s: (number | null | undefined)[], ms: number, tol = 1000): number | null {
  if (!Number.isFinite(t0) || !Number.isFinite(ms)) return null;
  const i = Math.round((ms - t0) / 36e5);
  if (i < 0 || i >= s.length || Math.abs(ms - (t0 + i * 36e5)) > tol) return null;
  const v = s[i];
  return v == null || !Number.isFinite(v) ? null : v;
}

/** Date civile (AAAA-MM-JJ) + k jours, par le calendrier (indépendant des changements d'heure). */
export function addDays(date: string, k: number): string {
  const d = new Date(Date.UTC(+date.slice(0, 4), +date.slice(5, 7) - 1, +date.slice(8, 10) + k));
  return d.toISOString().slice(0, 10);
}
/** Les n jours civils à partir de la date locale d0 (donnée par partsIn dans le fuseau voulu). */
export const civilDays = (d0: string, n: number) => Array.from({ length: n }, (_, k) => addDays(d0, k));

/** Jour civil en mots par rapport à aujourd'hui (même fuseau) : « Aujourd’hui », « Demain », sinon null (le jour s'écrit). */
export function dayWord(date: string, today: string): string | null {
  return date === today ? 'Aujourd’hui' : date === addDays(today, 1) ? 'Demain' : null;
}

/** Âge des données (génération du robot), et son niveau : à l'heure (≤ 3 h : le robot passe toutes les 1 h 30 environ),
 *  en retard (≤ 6 h : passages sautés par GitHub, déjà vu), ancienne au-delà. */
export type DataAge = { h: number; level: 'ok' | 'late' | 'old' };
export function dataAge(generated: string | null | undefined, tMsFn: (t: string) => number, now = Date.now()): DataAge {
  const g = generated ? tMsFn(generated) : NaN;
  const h = Number.isFinite(g) ? Math.max(0, (now - g) / 36e5) : Infinity;
  return { h, level: h <= 3 ? 'ok' : h <= 6 ? 'late' : 'old' };
}
/** « il y a 25 min », « il y a 3 h », « il y a 2 j » (âge des données reçues). */
export function agoWords(h: number): string {
  if (!Number.isFinite(h)) return 'à une date inconnue';
  const m = Math.round(h * 60);
  return m < 1 ? 'à l’instant' : m < 60 ? `il y a ${m} min` : h < 48 ? `il y a ${Math.round(h)} h` : `il y a ${Math.round(h / 24)} j`;
}
