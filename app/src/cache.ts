/** Téléchargement avec copie hors connexion, sans dépendance (issue #4, revue PR #22 ; testé par tests/regles_app.test.mjs).
 *  Ordre des demandes protégé PAR CLÉ : une réponse lente d'une demande plus ancienne ne remplace jamais, dans le stockage du
 *  téléphone, la copie déjà écrite par une demande plus récente. En cas de panne, la copie la plus récente reçue est rendue. */
export type Store = { getItem(k: string): Promise<string | null>; setItem(k: string, v: string): Promise<void> };

export function createCachedLoader(fetchJson: (path: string) => Promise<unknown>, store: Store) {
  const started: Record<string, number> = {}, written: Record<string, number> = {};
  return async function get<T>(path: string, key: string): Promise<{ data: T; offline: boolean }> {
    const my = (started[key] = (started[key] || 0) + 1);
    try {
      const data = (await fetchJson(path)) as T;
      if (my > (written[key] || 0)) {   // seule une demande plus récente que la dernière copie écrite la remplace
        written[key] = my;
        await store.setItem(key, JSON.stringify(data)).catch(() => {});
      }
      return { data, offline: false };
    } catch (e) {
      const c = await store.getItem(key).catch(() => null);   // hors connexion : dernière copie reçue
      if (c) return { data: JSON.parse(c) as T, offline: true };
      throw e;
    }
  };
}
