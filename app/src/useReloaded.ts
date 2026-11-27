import { useEffect, useState } from 'react';
import { AppState } from 'react-native';
import { createReloader, LoadState } from './reload';

/** Fiche chargée par son identifiant, redemandée au retour de l'appli au premier plan (reprise réseau, issue #4).
 *  Les réponses d'une ancienne demande, ou d'une autre fiche, sont ignorées (src/reload.ts). */
export function useReloaded<T>(load: (slug: string) => Promise<{ data: T; offline: boolean }>, slug: string): LoadState<T> {
  const [s, setS] = useState<LoadState<T>>({ data: null, offline: false, err: false });
  useEffect(() => {
    setS({ data: null, offline: false, err: false });
    const r = createReloader(() => load(slug), setS);
    r.run();
    const sub = AppState.addEventListener('change', st => { if (st === 'active') r.run(); });
    return () => { r.stop(); sub.remove(); };
  }, [load, slug]);
  return s;
}
