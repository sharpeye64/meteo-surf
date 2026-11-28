/** État partagé de l'appli (chantier #8) : index des données, favoris, comparaison, horloge et préférences d'accessibilité.
 *  - L'index est chargé par `createReloader` (src/reload.ts) : seule la dernière demande compte, une panne garde les données.
 *  - Retour au premier plan : données redemandées, âges recalculés (horloge à la minute, dans un contexte séparé pour que
 *    les écrans qui n'affichent pas d'âge ne se redessinent pas).
 *  - Hors connexion : les fiches des favoris sont préchargées pour être lisibles sans réseau (copie protégée, src/cache.ts). */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AccessibilityInfo, AppState } from 'react-native';
import { Index, loadFavs, loadIndex, loadSheet, saveFavs } from './data';
import { createReloader } from './reload';
import { dataAge, DataAge } from './series';
import { tMs } from './time';

type Data = {
  index: Index | null; offline: boolean; err: boolean; receivedAt: number | null;
  reload: () => Promise<void>;
  favs: string[]; toggleFav: (slug: string) => void; isFav: (slug: string) => boolean;
  /** null : comparaison jamais réglée (le comparateur propose alors les favoris) ; [] : l'utilisateur a tout retiré. */
  compare: string[] | null; setCompare: (s: string[]) => void;
  reduceMotion: boolean;
};
const DataCtx = createContext<Data | null>(null);
const ClockCtx = createContext<number>(0);
const COMPARE_KEY = 'houlalah.compare';

export function DataProvider({ children }: { children: ReactNode }) {
  const [index, setIndex] = useState<Index | null>(null);
  const [offline, setOffline] = useState(false);
  const [err, setErr] = useState(false);
  const [receivedAt, setReceivedAt] = useState<number | null>(null);
  const [favs, setFavs] = useState<string[]>([]);
  const [compare, setCmp] = useState<string[] | null>(null);
  const [reduceMotion, setReduce] = useState(false);
  const [minute, setMinute] = useState(() => Math.floor(Date.now() / 6e4));

  const rl = useRef<ReturnType<typeof createReloader<Index>> | null>(null);
  if (!rl.current) rl.current = createReloader<Index>(loadIndex, s => {
    if (s.data) setIndex(s.data);
    setOffline(s.offline); setErr(s.err);
    if (s.data && !s.offline) setReceivedAt(Date.now());
  });
  const reload = useCallback(() => rl.current!.run(), []);

  useEffect(() => {
    reload();
    loadFavs().then(setFavs);
    AsyncStorage.getItem(COMPARE_KEY).then(v => { try { const a = v == null ? null : JSON.parse(v); if (Array.isArray(a)) setCmp(a.slice(0, 4)); } catch {} }).catch(() => {});
    AccessibilityInfo.isReduceMotionEnabled().then(setReduce).catch(() => {});
    const a11y = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduce);
    const t = setInterval(() => setMinute(Math.floor(Date.now() / 6e4)), 15e3);
    const app = AppState.addEventListener('change', st => { if (st === 'active') { setMinute(Math.floor(Date.now() / 6e4)); reload(); } });
    return () => { a11y.remove(); clearInterval(t); app.remove(); };
  }, [reload]);

  // Préchargement des fiches des favoris (réseau faible sur la côte) : à chaque nouvel index, une fois par favori.
  useEffect(() => {
    if (!index || offline) return;
    favs.forEach((slug, i) => setTimeout(() => { loadSheet(slug).catch(() => {}); }, 400 * i));
  }, [index, offline, favs]);

  const toggleFav = useCallback((slug: string) => setFavs(f => {
    const n = f.includes(slug) ? f.filter(x => x !== slug) : [...f, slug];
    saveFavs(n); return n;
  }), []);
  const setCompare = useCallback((s: string[]) => {
    const n = [...new Set(s)].slice(0, 4);
    setCmp(n); AsyncStorage.setItem(COMPARE_KEY, JSON.stringify(n)).catch(() => {});
  }, []);

  const value = useMemo<Data>(() => ({
    index, offline, err, receivedAt, reload, favs, toggleFav, isFav: s => favs.includes(s), compare, setCompare, reduceMotion,
  }), [index, offline, err, receivedAt, reload, favs, toggleFav, compare, setCompare, reduceMotion]);
  return <DataCtx.Provider value={value}><ClockCtx.Provider value={minute}>{children}</ClockCtx.Provider></DataCtx.Provider>;
}

export function useData() {
  const d = useContext(DataCtx);
  if (!d) throw new Error('useData hors de DataProvider');
  return d;
}
/** Minute courante : à utiliser dans les écrans qui affichent un âge ou un état « en direct ». */
export const useMinute = () => useContext(ClockCtx);
/** Âge de l'index (heure de génération par le robot), recalculé chaque minute : « à l'heure », « en retard », « ancienne ». */
export function useDataAge(): DataAge {
  const { index } = useData();
  const minute = useMinute();
  return useMemo(() => dataAge(index?.generated, tMs, minute * 6e4), [index?.generated, minute]);
}
