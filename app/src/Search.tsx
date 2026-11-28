/** Recherche (panneau natif) : spots et bouées par nom, commune ou région, sans accents ni majuscules. Champ vide : la côte
 *  par pays et par région. Ouverte depuis le comparateur (`?pick=1`) : un toucher AJOUTE le spot à la comparaison et ferme ;
 *  depuis Ma côte (`?pick=fav`) : un toucher l'ajoute aux favoris et ferme. */
import * as Haptics from 'expo-haptics';
import { router, useLocalSearchParams } from 'expo-router';
import { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Path } from 'react-native-svg';
import { country, fr, regionName, SpotLite } from './data';
import { useData } from './store';
import { C, F, sizeCell, themed } from './theme';

const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
const PAYS = ['France', 'Espagne', 'Portugal'];

export default function Search() {
  const { index, compare, setCompare, isFav, toggleFav } = useData();
  const { pick } = useLocalSearchParams<{ pick?: string }>();
  const picking = pick === '1', addFav = pick === 'fav';
  const ins = useSafeAreaInsets();
  const [q, setQ] = useState('');

  const res = useMemo(() => {
    const k = norm(q.trim());
    if (!index || !k) return null;
    const m = (s: string | undefined) => !!s && norm(s).includes(k);
    return {
      spots: index.spots.filter(s => m(s.name) || m(s.commune) || m(regionName(s.region))).slice(0, 30),
      buoys: picking || addFav ? [] : index.buoys.filter(b => m(b.name) || m(b.sub)).slice(0, 8),
    };
  }, [q, index, picking, addFav]);

  const regions = useMemo(() => {
    if (!index) return [];
    return PAYS.map(p => {
      const by: Record<string, SpotLite[]> = {};
      index.spots.filter(s => country(s.region) === p).forEach(s => { (by[s.region] ||= []).push(s); });
      return { p, regs: Object.entries(by) };
    }).filter(x => x.regs.length);
  }, [index]);

  const openSpot = (s: SpotLite) => {
    Haptics.selectionAsync().catch(() => {});
    if (addFav) { if (!isFav(s.slug)) toggleFav(s.slug); router.back(); return; }
    if (picking) { setCompare([...(compare ?? []).filter(x => x !== s.slug), s.slug]); router.back(); return; }
    router.replace({ pathname: '/spot/[slug]', params: { slug: s.slug } });
  };
  const row = (s: SpotLite) => {
    const added = (picking && !!compare?.includes(s.slug)) || (addFav && isFav(s.slug));
    return (
      <Pressable key={s.slug} onPress={() => openSpot(s)} style={({ pressed }) => [st.row, pressed && { opacity: 0.6 }]} accessibilityLabel={`${s.name}, ${regionName(s.region)}`}>
        <View style={[st.dot, { backgroundColor: sizeCell(s.now.hs) }]} />
        <View style={{ flex: 1, minWidth: 0 }}>
          <Text style={st.name} numberOfLines={1}>{s.name}</Text>
          <Text style={st.sub} numberOfLines={1}>{s.commune ? `${s.commune} · ` : ''}{regionName(s.region)}</Text>
        </View>
        <Text style={st.val}>{added ? 'ajouté' : `${fr(s.now.hs)} m`}</Text>
      </Pressable>
    );
  };

  return (
    // Même structure que la fiche (src/SpotSheet.tsx, Panel) : la liste est le premier enfant du panneau et le champ de
    // recherche est son en-tête collant et opaque. Clavier : iOS ajoute lui-même l'inset sous la liste
    // (automaticallyAdjustKeyboardInsets) pour que les derniers résultats restent atteignables au-dessus du clavier.
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} stickyHeaderIndices={[0]} contentInsetAdjustmentBehavior="never" automaticallyAdjustContentInsets={false}
      automaticallyAdjustKeyboardInsets keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" contentContainerStyle={{ paddingBottom: ins.bottom + 30 }}>
      <View style={st.sticky}><View style={st.field}>
        <Svg width={18} height={18} viewBox="0 0 24 24"><Circle cx={11} cy={11} r={6.5} stroke={C.ink2} strokeWidth={2} fill="none" /><Path d="M16 16l4.5 4.5" stroke={C.ink2} strokeWidth={2} strokeLinecap="round" /></Svg>
        <TextInput value={q} onChangeText={setQ} autoFocus placeholder={picking ? 'Ajouter un spot à comparer' : addFav ? 'Ajouter un spot à Ma côte' : 'Spot, bouée, commune, région'} placeholderTextColor={C.ink3}
          style={st.input} autoCorrect={false} autoCapitalize="none" returnKeyType="search" clearButtonMode="while-editing" accessibilityLabel="Rechercher" />
      </View></View>
        {res ? (
          <>
            {!res.spots.length && !res.buoys.length && <Text style={st.none}>Aucun résultat pour « {q.trim()} ».</Text>}
            {!!res.spots.length && <View style={st.group}>{res.spots.map(row)}</View>}
            {!!res.buoys.length && (
              <>
                <Text style={st.lbl}>Bouées</Text>
                <View style={st.group}>
                  {res.buoys.map(b => (
                    <Pressable key={b.id} onPress={() => { Haptics.selectionAsync().catch(() => {}); router.replace({ pathname: '/bouee/[slug]', params: { slug: b.slug } }); }} style={({ pressed }) => [st.row, pressed && { opacity: 0.6 }]}>
                      <View style={[st.dot, st.buoyDot]} />
                      <View style={{ flex: 1, minWidth: 0 }}><Text style={st.name} numberOfLines={1}>{b.name}</Text><Text style={st.sub} numberOfLines={1}>{b.sub}</Text></View>
                      <Text style={[st.val, { color: C.measure }]}>{fr(b.hs)} m</Text>
                    </Pressable>
                  ))}
                </View>
              </>
            )}
          </>
        ) : regions.map(({ p, regs }) => (
          <View key={p}>
            <Text style={st.country}>{p}</Text>
            {regs.map(([r, list]) => (
              <View key={r}>
                <Text style={st.lbl}>{regionName(r)}</Text>
                <View style={st.group}>{list.map(row)}</View>
              </View>
            ))}
          </View>
        ))}
    </ScrollView>
  );
}

const st = themed(() => StyleSheet.create({
  sticky: { backgroundColor: C.bg, paddingBottom: 6 },
  field: { flexDirection: 'row', alignItems: 'center', gap: 10, marginHorizontal: 14, marginTop: 22, height: 50, borderRadius: 25, paddingHorizontal: 16, backgroundColor: C.card },
  input: { flex: 1, height: 50, fontFamily: F.t, fontSize: 16, color: C.ink },
  none: { fontFamily: F.t, fontSize: 14, color: C.ink2, textAlign: 'center', marginTop: 30 },
  country: { fontFamily: F.num, fontSize: 20, color: C.ink, letterSpacing: -0.6, marginHorizontal: 20, marginTop: 22 },
  lbl: { fontFamily: F.tX, fontSize: 10.5, letterSpacing: 1, color: C.ink3, textTransform: 'uppercase', marginHorizontal: 22, marginTop: 14, marginBottom: 6 },
  group: { marginHorizontal: 12, borderRadius: 22, backgroundColor: C.card, overflow: 'hidden' },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 56, paddingHorizontal: 14, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.line },
  dot: { width: 12, height: 12, borderRadius: 6 },
  buoyDot: { backgroundColor: C.night, borderWidth: 3, borderColor: C.measure },
  name: { fontFamily: F.tX, fontSize: 15, color: C.ink },
  sub: { fontFamily: F.tB, fontSize: 12, color: C.ink3, marginTop: 1 },
  val: { fontFamily: F.num, fontSize: 13.5, color: C.ink, letterSpacing: -0.4 },
}));
