import { Manrope_500Medium, Manrope_600SemiBold, Manrope_700Bold, Manrope_800ExtraBold } from '@expo-google-fonts/manrope';
import { Unbounded_500Medium, Unbounded_700Bold, Unbounded_800ExtraBold } from '@expo-google-fonts/unbounded';
import { useFonts } from 'expo-font';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, BackHandler, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { BuoyList, BuoyPage } from './src/BuoyScreens';
import { Buoy, Index, loadFavs, loadIndex, saveFavs, SpotLite } from './src/data';
import MapScreen from './src/MapScreen';
import SpotList from './src/SpotList';
import SpotSheet from './src/SpotSheet';
import TabBar, { Tab } from './src/TabBar';
import { C, F } from './src/theme';

/** Une pile d'écrans par-dessus l'onglet courant : fiche de spot ou page de bouée (on peut passer de l'une à l'autre). */
type Screen = { kind: 'spot'; spot: SpotLite } | { kind: 'buoy'; buoy: Buoy };

export default function App() {
  const [fonts] = useFonts({ Unbounded_500Medium, Unbounded_700Bold, Unbounded_800ExtraBold, Manrope_500Medium, Manrope_600SemiBold, Manrope_700Bold, Manrope_800ExtraBold });
  const [index, setIndex] = useState<Index | null>(null);
  const [offline, setOffline] = useState(false);
  const [err, setErr] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [favs, setFavs] = useState<string[] | null>(null);
  const [tab, setTab] = useState<Tab>('spots');
  const [stack, setStack] = useState<Screen[]>([]);

  const load = useCallback(async () => {
    try { const r = await loadIndex(); setIndex(r.data); setOffline(r.offline); setErr(false); } catch { setErr(true); }
  }, []);
  useEffect(() => { load(); loadFavs().then(setFavs); }, [load]);
  useEffect(() => {   // bouton retour d'Android : revenir à l'écran précédent
    const sub = BackHandler.addEventListener('hardwareBackPress', () => { if (stack.length) { setStack(s => s.slice(0, -1)); return true; } return false; });
    return () => sub.remove();
  }, [stack.length]);

  const toggleFav = (slug: string) => setFavs(f => { const n = (f || []).includes(slug) ? (f || []).filter(x => x !== slug) : [...(f || []), slug]; saveFavs(n); return n; });
  const openSpot = (spot: SpotLite) => setStack(s => [...s, { kind: 'spot', spot }]);
  const openBuoy = (buoy: Buoy) => setStack(s => [...s, { kind: 'buoy', buoy }]);
  const back = () => setStack(s => s.slice(0, -1));
  const top = stack[stack.length - 1];

  let body = null;
  if (!fonts || !index || favs == null) {
    body = (
      <View style={st.center}>
        {err ? (
          <>
            <Text style={st.msg}>Impossible de charger les prévisions.</Text>
            <Pressable onPress={load} style={st.retry}><Text style={st.retryT}>Réessayer</Text></Pressable>
          </>
        ) : <ActivityIndicator color={C.ink} />}
      </View>
    );
  } else if (top?.kind === 'spot') {
    body = <SpotSheet key={top.spot.slug} spot={top.spot} buoys={index.buoys} fav={favs.includes(top.spot.slug)} onFav={() => toggleFav(top.spot.slug)} onBack={back} onBuoy={openBuoy} />;
  } else if (top?.kind === 'buoy') {
    body = <BuoyPage key={top.buoy.id} buoy={top.buoy} onBack={back} onSpot={slug => { const s = index.spots.find(x => x.slug === slug); if (s) openSpot(s); }} />;
  } else if (tab === 'carte') {
    body = <MapScreen index={index} onSpot={openSpot} onBuoy={openBuoy} />;
  } else if (tab === 'bouees') {
    body = <BuoyList index={index} onOpen={openBuoy} />;
  } else {
    body = <SpotList key={tab} favOnly={tab === 'favoris'} index={index} favs={favs} offline={offline} refreshing={refreshing}
      onRefresh={async () => { setRefreshing(true); await load(); setRefreshing(false); }} onOpen={openSpot} onBuoy={openBuoy} />;
  }

  const ready = !!(fonts && index && favs != null);
  const fullMap = ready && tab === 'carte' && !top;   // carte plein écran : sous la barre d'état, barre d'onglets flottante
  const onTab = (t: Tab) => { setTab(t); setStack([]); };

  return (
    <SafeAreaProvider>
      <SafeAreaView style={st.root} edges={fullMap ? [] : ['top', 'left', 'right']}>
        <StatusBar style="dark" />
        <View style={{ flex: 1 }}>{body}</View>
        {ready && <TabBar tab={tab} onTab={onTab} floating={fullMap} />}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const st = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30 },
  msg: { color: C.ink2, fontSize: 16, textAlign: 'center', fontFamily: F.t },
  retry: { marginTop: 16, backgroundColor: C.ink, paddingHorizontal: 22, height: 44, borderRadius: 22, justifyContent: 'center' },
  retryT: { color: '#fff', fontWeight: '700' },
});
