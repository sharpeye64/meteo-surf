/** Contrat horaire (issue #2), même règle que le site (web/index.html, bloc « CONTRAT HORAIRE ») et le robot (pipeline/timefmt.py).
 *  Heures publiées : « 2026-11-27T10:00+01:00 » = heure LOCALE du lieu + décalage, instant exact quel que soit le fuseau du
 *  téléphone. Ancien format sans décalage = heure de Paris, EXPLICITEMENT (jamais le fuseau du téléphone).
 *  L'affichage se fait à l'heure du lieu (fuseau IANA « tz » du spot ou de la bouée : Europe/Lisbon au Portugal). */
const OFF = /([+-]\d\d:\d\d|Z)$/;
const fmts: Record<string, Intl.DateTimeFormat> = {};
const fmt = (tz: string) => (fmts[tz] ||= new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }));

export type Parts = { date: string; h: number; m: number; wd: number; d: number };

/** Jour, heure, minute et jour de la semaine d'un instant, à l'heure du fuseau tz. */
export function partsIn(ms: number, tz = 'Europe/Paris'): Parts {
  const p: Record<string, string> = {};
  fmt(tz).formatToParts(new Date(ms)).forEach(x => { p[x.type] = x.value; });
  const date = `${p.year}-${p.month}-${p.day}`;
  return { date, h: +p.hour % 24, m: +p.minute, wd: new Date(`${date}T12:00:00Z`).getUTCDay(), d: +p.day };
}

function offMs(tz: string, ms: number) {
  const p = partsIn(ms, tz);
  return Date.UTC(+p.date.slice(0, 4), +p.date.slice(5, 7) - 1, +p.date.slice(8, 10), p.h, p.m) - Math.floor(ms / 6e4) * 6e4;
}

/** Instant (ms) d'une heure publiée, avec ou sans décalage. Heure répétée d'octobre (ancien format) : la première, comme le robot. */
export function tMs(t?: string | null): number {
  if (!t) return NaN;
  if (OFF.test(t)) return Date.parse(t);
  const g = Date.parse((t.length === 10 ? t + 'T12:00' : t.slice(0, 16)) + 'Z');
  if (isNaN(g)) return NaN;
  const oa = offMs('Europe/Paris', g - 432e5), ob = offMs('Europe/Paris', g + 432e5);
  const ok = [oa, ob].filter(o => offMs('Europe/Paris', g - o) === o).map(o => g - o);
  return ok.length ? Math.min(...ok) : g - oa;
}

/** Fuseau d'un spot ou d'une bouée : champ « tz » du robot, sinon d'après la région (Portugal → Lisbonne), sinon Paris. */
export const placeTz = (x?: { tz?: string | null; region?: string } | null) =>
  (x && x.tz) || (x && x.region && /^Portugal/.test(x.region) ? 'Europe/Lisbon' : 'Europe/Paris');

/** « 10 h » ou « 10 h 30 » à l'heure du lieu. */
export const hhIn = (ms: number, tz: string) => { const p = partsIn(ms, tz); return `${p.h} h${p.m ? ' ' + String(p.m).padStart(2, '0') : ''}`; };
