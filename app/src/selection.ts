/** Sélection jour / heure d'une fiche de spot, gardée par DATE et par INSTANT, pas par position (issue #4, revue PR #22).
 *  Après un rechargement de la même fiche, la série peut commencer plus tard ou être plus courte : la sélection ne peut ni
 *  sortir des limites (plantage) ni désigner une autre heure. Sans dépendance (testé par tests/regles_app.test.mjs). */
export type Day = { date: string; idx: number[] };
export type Pick = { date: string | null; ms: number | null };

/** { jour, heure } à afficher : le jour choisi s'il existe encore (sinon le premier), l'heure choisie si son instant est
 *  encore dans ce jour (sinon null : l'heure par défaut). null si la série est vide. */
export function resolveSel(days: Day[], t0: number, pick: Pick): { dayI: number; hourI: number | null } | null {
  if (!days.length || !Number.isFinite(t0)) return null;
  let dayI = pick.date ? days.findIndex(d => d.date === pick.date) : 0;
  if (dayI < 0) dayI = 0;
  let hourI: number | null = null;
  if (pick.ms != null) {
    const i = Math.round((pick.ms - t0) / 36e5);
    if (days[dayI].idx.includes(i)) hourI = i;
  }
  return { dayI, hourI };
}
