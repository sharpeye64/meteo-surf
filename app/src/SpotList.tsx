import { useMemo, useState } from 'react';
import { FlatList, Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import Arrow from './Arrow';
import { ageTxt, country, fr, Index, regionName, sizeCol, SpotLite } from './data';
import { C, R } from './theme';

type Props = { index: Index; favs: string[]; offline: boolean; refreshing: boolean; onRefresh: () => void; onOpen: (s: SpotLite) => void };
const FILTERS = ['Tous', 'France', 'Espagne', 'Portugal', '★ Favoris'];

export default function SpotList({ index, favs, offline, refreshing, onRefresh, onOpen }: Props) {
  const [q, setQ] = useState('');
  const [f, setF] = useState(favs.length ? '★ Favoris' : 'Tous');
  const top = useMemo(() => { const t: Record<string, number> = {}; index.spots.forEach(s => { t[s.region] = Math.max(t[s.region] ?? -90, s.lat); }); return t; }, [index]);
  const list = useMemo(() => {
    const t = q.trim().toLowerCase();
    return [...index.spots]
      .filter(s => (f === 'Tous' ? true : f === '★ Favoris' ? favs.includes(s.slug) : country(s.region) === f))
      .filter(s => !t || s.name.toLowerCase().includes(t) || (s.commune || '').toLowerCase().includes(t) || s.region.toLowerCase().includes(t))
      .sort((a, b) => (top[b.region] - top[a.region]) || (b.lat - a.lat));   // régions du nord au sud, puis spots du nord au sud
  }, [index, q, f, favs, top]);
  const fresh = index.buoys.filter(b => (Date.now() - new Date(b.time + ':00').getTime()) / 36e5 < 2).length;

  return (
    <FlatList
      data={list}
      keyExtractor={s => s.slug}
      keyboardShouldPersistTaps="handled"
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.ink} />}
      contentContainerStyle={{ paddingBottom: 40 }}
      ListHeaderComponent={
        <View>
          <View style={st.head}>
            <Text style={st.logo}>houlalah</Text>
            <Text style={st.sub}>{index.spots.length} spots · {fresh} bouées en direct{offline ? ' · hors connexion' : ''}</Text>
          </View>
          <View style={st.search}>
            <TextInput value={q} onChangeText={setQ} placeholder="Chercher un spot ou une ville" placeholderTextColor={C.ink3} style={st.input} autoCorrect={false} />
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.chips}>
            {FILTERS.map(x => (
              <Pressable key={x} onPress={() => setF(x)} style={[st.chip, f === x && st.chipOn]}>
                <Text style={[st.chipT, f === x && st.chipTOn]}>{x}</Text>
              </Pressable>
            ))}
          </ScrollView>
          {!list.length && <Text style={st.empty}>{f === '★ Favoris' ? 'Aucun favori pour l’instant. Touche l’étoile sur la fiche d’un spot.' : 'Aucun spot ne correspond.'}</Text>}
        </View>
      }
      renderItem={({ item: s, index: i }) => {
        const head = i === 0 || list[i - 1].region !== s.region;
        return (
          <View>
            {head && <Text style={st.grp}>{regionName(s.region)}</Text>}
            <Pressable onPress={() => onOpen(s)} style={({ pressed }) => [st.row, pressed && { opacity: 0.6 }]}>
              <View style={{ flex: 1 }}>
                <Text style={st.name}>{favs.includes(s.slug) ? '★ ' : ''}{s.name}</Text>
                <Text style={st.meta}>{s.commune && s.commune !== s.name ? s.commune + ' · ' : ''}{fr(s.now.tp, 0)} s · vent {fr(s.now.wind, 0)} km/h</Text>
              </View>
              <Arrow dir={s.now.dir} size={15} color={C.ink2} />
              <View style={[st.pill, { backgroundColor: sizeCol(s.now.hs) }]}>
                <Text style={st.pillT}>{fr(s.now.hs)}</Text>
              </View>
            </Pressable>
          </View>
        );
      }}
      ListFooterComponent={<Text style={st.foot}>Mis à jour {ageTxt(index.generated)} · prévisions indicatives</Text>}
    />
  );
}

const st = StyleSheet.create({
  head: { paddingHorizontal: 20, paddingTop: 12 },
  logo: { fontSize: 30, fontWeight: '800', color: C.ink, letterSpacing: -1 },
  sub: { color: C.ink2, fontWeight: '600', marginTop: 2 },
  search: { marginHorizontal: 16, marginTop: 16, backgroundColor: C.card, borderRadius: R.pill, paddingHorizontal: 18, borderWidth: 1, borderColor: C.line },
  input: { height: 48, fontSize: 16, color: C.ink },
  chips: { paddingHorizontal: 16, paddingVertical: 14, gap: 8 },
  chip: { paddingHorizontal: 16, height: 38, borderRadius: R.pill, backgroundColor: C.card, justifyContent: 'center', borderWidth: 1, borderColor: C.line },
  chipOn: { backgroundColor: C.ink, borderColor: C.ink },
  chipT: { fontWeight: '700', color: C.ink },
  chipTOn: { color: '#fff' },
  grp: { marginHorizontal: 20, marginTop: 18, marginBottom: 6, fontSize: 12, fontWeight: '800', letterSpacing: 1.2, textTransform: 'uppercase', color: C.sandDeep },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, marginHorizontal: 16, paddingHorizontal: 16, paddingVertical: 12, backgroundColor: C.card, borderRadius: 18, marginBottom: 6 },
  name: { fontSize: 16, fontWeight: '700', color: C.ink },
  meta: { fontSize: 13, color: C.ink2, marginTop: 2 },
  pill: { minWidth: 54, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10 },
  pillT: { fontSize: 16, fontWeight: '800', color: '#0c1519' },
  empty: { marginHorizontal: 20, color: C.ink2, marginTop: 10 },
  foot: { textAlign: 'center', color: C.ink3, marginTop: 20, fontSize: 12 },
});
