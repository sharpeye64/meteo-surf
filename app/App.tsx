import { Manrope_500Medium, Manrope_600SemiBold, Manrope_700Bold, Manrope_800ExtraBold } from '@expo-google-fonts/manrope';
import { Unbounded_500Medium, Unbounded_700Bold, Unbounded_800ExtraBold } from '@expo-google-fonts/unbounded';
import { useFonts } from 'expo-font';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, BackHandler, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { Index, loadFavs, loadIndex, saveFavs, SpotLite } from './src/data';
import SpotList from './src/SpotList';
import SpotSheet from './src/SpotSheet';
import { C, F } from './src/theme';

export default function App() {
  const [fonts] = useFonts({ Unbounded_500Medium, Unbounded_700Bold, Unbounded_800ExtraBold, Manrope_500Medium, Manrope_600SemiBold, Manrope_700Bold, Manrope_800ExtraBold });
  const [index, setIndex] = useState<Index | null>(null);
  const [offline, setOffline] = useState(false);
  const [err, setErr] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [favs, setFavs] = useState<string[] | null>(null);
  const [open, setOpen] = useState<SpotLite | null>(null);

  const load = useCallback(async () => {
    try { const r = await loadIndex(); setIndex(r.data); setOffline(r.offline); setErr(false); } catch { setErr(true); }
  }, []);
  useEffect(() => { load(); loadFavs().then(setFavs); }, [load]);
  useEffect(() => {   // bouton retour d'Android : revenir à la liste
    const sub = BackHandler.addEventListener('hardwareBackPress', () => { if (open) { setOpen(null); return true; } return false; });
    return () => sub.remove();
  }, [open]);

  const toggleFav = (slug: string) => setFavs(f => { const n = (f || []).includes(slug) ? (f || []).filter(x => x !== slug) : [...(f || []), slug]; saveFavs(n); return n; });

  return (
    <SafeAreaProvider>
      <SafeAreaView style={st.root} edges={['top', 'left', 'right']}>
        <StatusBar style="dark" />
        {!fonts || !index || favs == null ? (
          <View style={st.center}>
            {err ? (
              <>
                <Text style={st.msg}>Impossible de charger les prévisions.</Text>
                <Pressable onPress={load} style={st.retry}><Text style={st.retryT}>Réessayer</Text></Pressable>
              </>
            ) : <ActivityIndicator color={C.ink} />}
          </View>
        ) : open ? (
          <SpotSheet spot={open} buoys={index.buoys} fav={favs.includes(open.slug)} onFav={() => toggleFav(open.slug)} onBack={() => setOpen(null)} />
        ) : (
          <SpotList index={index} favs={favs} offline={offline} refreshing={refreshing}
            onRefresh={async () => { setRefreshing(true); await load(); setRefreshing(false); }} onOpen={setOpen} />
        )}
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
