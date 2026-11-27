/** Chargement d'une fiche (spot ou bouée) avec reprises, sans dépendance (issue #4 ; testé par tests/regles_app.test.mjs).
 *  - Seule la réponse de la DERNIÈRE demande compte : une réponse lente d'une demande plus ancienne (même fiche) est ignorée.
 *  - Un échec garde les données déjà affichées (panne partielle) ; l'erreur ne s'affiche que s'il n'y a rien à montrer.
 *  - « offline » : données tirées du cache du téléphone, ou rafraîchissement impossible. */
export type LoadState<T> = { data: T | null; offline: boolean; err: boolean };

export function createReloader<T>(load: () => Promise<{ data: T; offline: boolean }>, emit: (s: LoadState<T>) => void) {
  let seq = 0, alive = true;
  let cur: LoadState<T> = { data: null, offline: false, err: false };
  const set = (s: LoadState<T>) => { cur = s; if (alive) emit(s); };
  return {
    run(): Promise<void> {
      const my = ++seq;
      return load().then(
        r => { if (alive && my === seq) set({ data: r.data, offline: r.offline, err: false }); },
        () => { if (alive && my === seq) set({ data: cur.data, offline: !!cur.data, err: !cur.data }); });
    },
    stop() { alive = false; },
    get state() { return cur; },
  };
}
