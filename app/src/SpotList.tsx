import { useMemo, useState } from 'react';
import { FlatList, Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import Arrow from './Arrow';
import Brand from './Brand';
import { ageTxt, country, fr, Index, isLive, regionName, sector, SpotLite } from './data';

import { useBarSpace } from './TabBar';
import { C, F, sizeCell, themed, windCell } from './theme';

type Props = { index: Index; favs: string[]; offline: boolean; refreshing: boolean; onRefresh: () => void; onOpen: (s: SpotLite) => void; onBuoy?: (b: Index['buoys'][number]) => void; favOnly?: boolean };
const FILTERS = ['Tous', 'France', 'Espagne', 'Portugal', '★ Favoris'];

export default function SpotList({ index, favs, offline, refreshing, onRefresh, onOpen, onBuoy, favOnly }: Props) {
  const pad = useBarSpace();
  const [q, setQ] = useState('');
  const [f, setF] = useState(favOnly ? '★ Favoris' : 'Tous');
  const top = useMemo(() => { const t: Record<string, number> = {}; index.spots.forEach(s => { t[s.region] = Math.max(t[s.region] ?? -90, s.lat); }); return t; }, [index]);
  const list = useMemo(() => {
    const t = q.trim().toLowerCase();
    return [...index.spots]
      .filter(s => (f === 'Tous' ? true : f === '★ Favoris' ? favs.includes(s.slug) : country(s.region) === f))
      .filter(s => !t || s.name.toLowerCase().includes(t) || (s.commune || '').toLowerCase().includes(t) || s.region.toLowerCase().includes(t))
      .sort((a, b) => (top[b.region] - top[a.region]) || (b.lat - a.lat));   // régions du nord au sud, puis spots du nord au sud
  }, [index, q, f, favs, top]);
  const live = index.buoys.filter(isLive);   // en direct selon la cadence de chaque station (src/rules.ts)

  return (
    <FlatList
      data={list}
      keyExtractor={s => s.slug}
      keyboardShouldPersistTaps="handled"
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.ink} />}
      contentContainerStyle={{ paddingBottom: pad }}
      ListHeaderComponent={
        <View>
          <View style={st.head}>
            <View style={st.brand}><Brand h={24} /></View>
            {offline && <Text style={st.off}>hors connexion</Text>}
          </View>
          <Text style={st.h1}>{favOnly ? 'Mes spots' : 'La houle\ndu moment'}</Text>
          <Text style={st.lead}>{favOnly ? `${favs.length} favori${favs.length > 1 ? 's' : ''}` : `${index.spots.length} spots de la Bretagne au Portugal`}</Text>

          {!favOnly && !!live.length && (
            <View style={st.liveCard}>
              <View style={st.liveHd}><View style={st.dot} /><Text style={st.liveT}>BOUÉES EN DIRECT</Text><Text style={st.liveN}>{live.length}</Text></View>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingRight: 16 }}>
                {live.map(b => (
                  <Pressable key={b.id} style={st.bu} onPress={() => onBuoy?.(b)}>
                    <View><Text style={st.buN}>{b.name}</Text><Text style={st.buS}>{ageTxt(b.time)}{b.tp ? ` · ${Math.round(b.tp)} s` : ''}</Text></View>
                    <View style={st.buV}><Text style={st.buVT}>{fr(b.hs)}</Text></View>
                  </Pressable>
                ))}
              </ScrollView>
            </View>
          )}

          {!favOnly && <View style={st.search}>
            <Text style={st.lens}>⌕</Text>
            <TextInput value={q} onChangeText={setQ} placeholder="Chercher un spot…" placeholderTextColor={C.ink3} style={st.input} autoCorrect={false} />
          </View>}
          {!favOnly && <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.chips}>
            {FILTERS.map(x => (
              <Pressable key={x} onPress={() => setF(x)} style={[st.chip, f === x && st.chipOn]}>
                <Text style={[st.chipT, f === x && st.chipTOn]}>{x}</Text>
              </Pressable>
            ))}
          </ScrollView>}
          {!list.length && <Text style={st.empty}>{f === '★ Favoris' ? 'Aucun favori pour l’instant. Touche l’étoile sur la fiche d’un spot.' : 'Aucun spot ne correspond.'}</Text>}
        </View>
      }
      renderItem={({ item: s, index: i }) => {
        const head = i === 0 || list[i - 1].region !== s.region;
        const n = head ? list.filter(x => x.region === s.region).length : 0;
        return (
          <View>
            {head && <View style={st.grp}><Text style={st.grpT}>{regionName(s.region)}</Text><Text style={st.grpN}>{n}</Text></View>}
            <SpotRow s={s} fav={favs.includes(s.slug)} onOpen={onOpen} />
          </View>
        );
      }}
      ListFooterComponent={<Text style={st.foot}>Mis à jour {ageTxt(index.generated)} · prévisions indicatives, à confirmer sur place</Text>}
    />
  );
}

/** Une ligne de spot : case colorée (hauteur, période), nom, direction de la houle, vent. */
export function SpotRow({ s, fav, onOpen, place }: { s: SpotLite; fav: boolean; onOpen: (s: SpotLite) => void; place?: boolean }) {
  return (
      <Pressable onPress={() => onOpen(s)} style={({ pressed }) => [st.row, pressed && { transform: [{ scale: 0.985 }], opacity: 0.85 }]}>
        <View style={[st.cell, { backgroundColor: sizeCell(s.now.hs) }]}>
          <Text style={st.cellV}>{fr(s.now.hs)}</Text>
          <Text style={st.cellU}>{fr(s.now.tp, 0)} s</Text>
        </View>
        <View style={{ flex: 1, minWidth: 0 }}>
          <Text style={st.name} numberOfLines={1}>{s.name}{place && <Text style={st.place}>  {s.commune || regionName(s.region)}</Text>}</Text>
          <View style={st.metaRow}>
            <Arrow dir={s.now.dir} size={12} color={C.ink2} />
            <Text style={st.meta}>{sector(s.now.dir)}</Text>
            <View style={[st.wind, { backgroundColor: windCell(s.now.wind) }]}>
              <Arrow dir={s.now.wdir} size={10} color={C.ink} />
              <Text style={st.windT}>{fr(s.now.wind, 0)}</Text>
            </View>
          </View>
        </View>
        {fav && <Text style={st.fav}>★</Text>}
      </Pressable>
  );
}

const st = themed(() => StyleSheet.create({
  head: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingTop: 8 },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  off: { fontFamily: F.tB, fontSize: 12, color: C.coral },
  h1: { fontFamily: F.numX, fontSize: 30, lineHeight: 34, color: C.ink, letterSpacing: -1, marginTop: 22, marginHorizontal: 20 },
  lead: { fontFamily: F.t, fontSize: 14, color: C.ink2, marginTop: 6, marginHorizontal: 20 },
  liveCard: { marginTop: 18, marginLeft: 16, paddingVertical: 14, paddingLeft: 16, borderTopLeftRadius: 24, borderBottomLeftRadius: 24, backgroundColor: C.card },
  liveHd: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10, paddingRight: 16 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: C.live },
  liveT: { fontFamily: F.tX, fontSize: 11, letterSpacing: 1.3, color: C.creamText, flex: 1 },
  liveN: { fontFamily: F.tX, fontSize: 11, color: C.creamText2 },
  bu: { flexDirection: 'row', alignItems: 'center', gap: 10, height: 46, borderRadius: 23, paddingLeft: 16, paddingRight: 5, backgroundColor: C.cream },
  buN: { fontFamily: F.tB, fontSize: 13.5, color: C.ink },
  buS: { fontFamily: F.t, fontSize: 11.5, color: C.creamText },
  buV: { height: 36, minWidth: 50, borderRadius: 18, paddingHorizontal: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: C.pill },
  buVT: { fontFamily: F.num, fontSize: 15, color: C.sandText, letterSpacing: -0.5 },
  search: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 18, backgroundColor: C.card, borderRadius: 999, paddingHorizontal: 18, height: 52, shadowColor: '#10202c', shadowOpacity: 0.08, shadowRadius: 14, shadowOffset: { width: 0, height: 6 }, elevation: 2 },
  lens: { fontSize: 20, color: C.ink2, marginRight: 8 },
  input: { flex: 1, height: 52, fontSize: 16, color: C.ink, fontFamily: F.t },
  chips: { paddingHorizontal: 16, paddingVertical: 14, gap: 8 },
  chip: { paddingHorizontal: 16, height: 38, borderRadius: 19, backgroundColor: C.card, justifyContent: 'center' },
  chipOn: { backgroundColor: C.ink },
  chipT: { fontFamily: F.tB, fontSize: 13.5, color: C.ink },
  chipTOn: { color: C.onInk },
  grp: { flexDirection: 'row', alignItems: 'center', gap: 8, marginHorizontal: 20, marginTop: 18, marginBottom: 8 },
  grpT: { fontFamily: F.tX, fontSize: 11.5, letterSpacing: 1.4, textTransform: 'uppercase', color: C.gold },
  grpN: { fontFamily: F.tB, fontSize: 11.5, color: C.ink3 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 14, marginHorizontal: 16, padding: 8, paddingRight: 16, backgroundColor: C.card, borderRadius: 20, marginBottom: 8 },
  cell: { width: 62, height: 58, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  cellV: { fontFamily: F.num, fontSize: 19, color: C.ink, letterSpacing: -0.8 },
  cellU: { fontFamily: F.tB, fontSize: 11, color: C.cellU, marginTop: -1 },
  name: { fontFamily: F.tX, fontSize: 16, color: C.ink },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 5 },
  meta: { fontFamily: F.tB, fontSize: 12.5, color: C.ink2, marginRight: 6 },
  wind: { flexDirection: 'row', alignItems: 'center', gap: 4, height: 22, paddingHorizontal: 8, borderRadius: 11 },
  windT: { fontFamily: F.tX, fontSize: 12, color: C.ink },
  fav: { fontSize: 16, color: C.gold },
  place: { fontFamily: F.t, fontSize: 13, color: C.ink3 },
  empty: { marginHorizontal: 20, color: C.ink2, marginTop: 10, fontFamily: F.t },
  foot: { textAlign: 'center', color: C.ink3, marginTop: 20, fontSize: 12, fontFamily: F.t, paddingHorizontal: 24 },
}));
