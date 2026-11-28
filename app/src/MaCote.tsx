/** Onglet « Ma côte » : vos spots favoris, chacun avec la prévision de l'heure (houle, période, direction ensemble, D5),
 *  le vent rapporté à la plage, et la mesure de maintenant de sa bouée de référence (or = mesure). Un toucher ouvre la fiche.
 *  Pas de classement ni de note : l'ordre est celui où vous avez ajouté vos spots. */
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Arrow from './Arrow';
import { ageTxt, freshOf, fr, perTxt, refBuoy, regionName, sector, SpotLite, WIND_WORD, windCat } from './data';
import { Blink } from './Live';
import { useData, useMinute } from './store';
import { useBarSpace } from './TabBar';
import { C, F, sizeCell, themed } from './theme';
import Stamp from './Stamp';

export default function MaCote() {
  const { index, favs, setCompare } = useData();
  useMinute();
  const ins = useSafeAreaInsets(), pad = useBarSpace();
  const spots = favs.map(f => index!.spots.find(s => s.slug === f)).filter((s): s is SpotLite => !!s);
  const t = spots[0]?.now.t ?? index!.spots[0]?.now.t;

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ paddingTop: ins.top + 14, paddingBottom: pad }}>
      <View style={st.top}>
        <Text style={st.h1}>Ma côte</Text>
        <Stamp t={t} style={{ marginTop: 8 }} />
      </View>

      {spots.length ? spots.map(s => <FavCard key={s.slug} s={s} />) : (
        <View style={st.empty}>
          <Text style={st.emptyT}>Vos spots, d’un coup d’œil</Text>
          <Text style={st.emptyS}>Touchez l’étoile sur la fiche d’un spot : il apparaîtra ici avec sa prévision et la mesure de sa bouée. Ses données restent lisibles sans réseau.</Text>
          <Pressable onPress={() => router.push('/recherche')} style={({ pressed }) => [st.btn, pressed && st.pressed]}><Text style={st.btnT}>Chercher un spot</Text></Pressable>
        </View>
      )}

      {spots.length >= 2 && (
        <Pressable onPress={() => { Haptics.selectionAsync().catch(() => {}); setCompare(spots.slice(0, 4).map(s => s.slug)); router.push('/comparer'); }}
          style={({ pressed }) => [st.btn, st.btnWide, pressed && st.pressed]} accessibilityHint="Ouvre le comparateur avec vos favoris">
          <Text style={st.btnT}>Comparer mes spots</Text>
        </Pressable>
      )}
    </ScrollView>
  );
}

function FavCard({ s }: { s: SpotLite }) {
  const { index } = useData();
  const n = s.now, wc = windCat(n.wind, n.wdir, s.ori), ref = refBuoy(index!.buoys, s);
  const col = wc === 'offshore' || wc === 'side-off' ? C.off : wc === 'de côté' ? C.side : wc === 'onshore' ? C.on : C.ink2;
  return (
    <Pressable onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {}); router.push({ pathname: '/spot/[slug]', params: { slug: s.slug } }); }}
      style={({ pressed }) => [st.card, pressed && st.pressed]} accessibilityLabel={`${s.name}, houle ${fr(n.hs)} mètre, ${n.tp != null ? Math.round(n.tp) + ' secondes' : ''}, vent ${n.wind ?? '—'} kilomètres heure${wc ? ', ' + WIND_WORD[wc] : ''}`}>
      <View style={st.cardHd}>
        <View style={{ flex: 1, minWidth: 0 }}>
          <Text style={st.name} numberOfLines={1}>{s.name}</Text>
          <Text style={st.reg} numberOfLines={1}>{regionName(s.region)}</Text>
        </View>
        <View style={[st.chip, { backgroundColor: sizeCell(n.hs) }]}><Text style={st.chipT}>{fr(n.hs)} m</Text></View>
      </View>
      <View style={st.row}>
        <View style={st.cell}>
          <Text style={st.k}>Houle</Text>
          <View style={st.vRow}><Text style={st.v}>{n.tp != null ? Math.round(n.tp) : '—'}<Text style={st.u}> s</Text></Text><Arrow dir={n.dir} size={12} color={C.ink2} /><Text style={st.s}>{sector(n.dir)}</Text></View>
        </View>
        <View style={st.cell}>
          <Text style={st.k}>Vent</Text>
          <View style={st.vRow}><Text style={st.v}>{n.wind ?? '—'}<Text style={st.u}> km/h</Text></Text><Arrow dir={n.wdir} size={12} color={C.ink2} /></View>
          {!!wc && <Text style={[st.s, { color: col, fontFamily: F.tX }]}>{WIND_WORD[wc]}</Text>}
        </View>
        {ref ? (
          <View style={[st.cell, st.buoy]}>
            <View style={st.vRow}>{freshOf(ref.b) === 'live' ? <Blink size={6} color={C.liveOnBuoy} /> : null}<Text style={st.bk} numberOfLines={1}>{ref.b.name}</Text></View>
            <Text style={st.bv}>{fr(ref.b.hs)}<Text style={st.u}> m</Text></Text>
            <Text style={st.bs} numberOfLines={1}>{perTxt(ref.b) || ageTxt(ref.b.time)}</Text>
          </View>
        ) : <View style={st.cell} />}
      </View>
    </Pressable>
  );
}

const st = themed(() => StyleSheet.create({
  top: { paddingHorizontal: 20, paddingBottom: 8 },
  h1: { fontFamily: F.num, fontSize: 28, color: C.ink, letterSpacing: -1 },
  lead: { fontFamily: F.tB, fontSize: 13, color: C.ink2, marginTop: 4 },
  card: { marginHorizontal: 12, marginTop: 10, padding: 14, borderRadius: 26, backgroundColor: C.card, gap: 12 },
  pressed: { opacity: 0.82, transform: [{ scale: 0.985 }] },
  cardHd: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  name: { fontFamily: F.num, fontSize: 17, color: C.ink, letterSpacing: -0.5 },
  reg: { fontFamily: F.tB, fontSize: 12, color: C.ink3, marginTop: 2 },
  chip: { height: 34, paddingHorizontal: 12, borderRadius: 17, justifyContent: 'center' },
  chipT: { fontFamily: F.num, fontSize: 15, color: C.ink, letterSpacing: -0.5 },
  row: { flexDirection: 'row', gap: 6 },
  cell: { flex: 1, minWidth: 0, borderRadius: 16, backgroundColor: C.soft, padding: 10, gap: 3 },
  k: { fontFamily: F.tX, fontSize: 9.5, letterSpacing: 0.9, color: C.ink3, textTransform: 'uppercase' },
  vRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  v: { fontFamily: F.num, fontSize: 16, color: C.ink, letterSpacing: -0.5 },
  u: { fontFamily: F.tB, fontSize: 10.5, letterSpacing: 0 },
  s: { fontFamily: F.tB, fontSize: 11.5, color: C.ink2 },
  buoy: { backgroundColor: C.buoySurface },
  bk: { flexShrink: 1, fontFamily: F.tX, fontSize: 10, color: C.onBuoy },
  bv: { fontFamily: F.num, fontSize: 16, color: C.measureOnBuoy, letterSpacing: -0.5 },
  bs: { fontFamily: F.tB, fontSize: 11, color: C.measureOnBuoy },
  empty: { marginHorizontal: 12, marginTop: 10, padding: 22, borderRadius: 26, backgroundColor: C.card, gap: 8 },
  emptyT: { fontFamily: F.num, fontSize: 18, color: C.ink, letterSpacing: -0.5 },
  emptyS: { fontFamily: F.t, fontSize: 14, lineHeight: 20, color: C.ink2 },
  btn: { alignSelf: 'flex-start', marginTop: 8, height: 46, paddingHorizontal: 20, borderRadius: 23, backgroundColor: C.night, justifyContent: 'center' },
  btnWide: { alignSelf: 'center', marginTop: 18 },
  btnT: { fontFamily: F.tX, fontSize: 14, color: C.onNight },
}));
