/** Onglet « Ma côte » : tableau de bord personnel (P1 du porteur, 28/11). Pour chaque favori :
 *  - la prévision de l'heure (houle = hauteur + période + direction ensemble, D5 ; vent rapporté à la plage) ;
 *  - une MINI-FRISE des 48 prochaines heures (toutes les 3 h : barre de houle à l'échelle 0-3 m, filet d'orientation du
 *    vent dessous, jours marqués), tirée de la fiche déjà préchargée pour le hors-connexion (aucune requête en plus) ;
 *  - la dernière mesure de sa bouée de référence (or = mesure).
 *  Ajout d'un spot depuis l'écran, comparateur accessible en haut. Aucun score, classement ni recommandation : l'ordre est
 *  celui où vous avez ajouté vos spots. */
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';
import Arrow from './Arrow';
import { ageTxt, freshOf, fr, loadSheetShared, perTxt, refBuoy, regionName, sector, Sheet, SpotLite, WIND_WORD, windCat } from './data';
import { Blink } from './Live';
import { valueAt } from './series';
import Stamp from './Stamp';
import { useData, useMinute } from './store';
import { useBarSpace } from './TabBar';
import { C, F, sizeCell, themed } from './theme';
import { partsIn, placeTz, tMs } from './time';

const J = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
const STEP = 3, N = 16;   // 16 colonnes de 3 h = 48 h

export default function MaCote() {
  const { index, favs, setCompare } = useData();
  useMinute();
  const ins = useSafeAreaInsets(), pad = useBarSpace();
  const spots = favs.map(f => index!.spots.find(s => s.slug === f)).filter((s): s is SpotLite => !!s);
  const t = spots[0]?.now.t ?? index!.spots[0]?.now.t;
  const compare = () => { Haptics.selectionAsync().catch(() => {}); setCompare(spots.slice(0, 4).map(s => s.slug)); router.push('/comparer'); };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ paddingTop: ins.top + 10, paddingBottom: pad }}>
      <View style={st.top}>
        <Text style={st.h1}>Ma côte</Text>
        {spots.length >= 2 && (
          <Pressable onPress={compare} style={({ pressed }) => [st.cmp, pressed && st.pressed]} accessibilityLabel="Comparer mes spots">
            <Svg width={16} height={16} viewBox="0 0 24 24"><Path d="M6 20V10M12 20V4M18 20v-7" stroke={C.onNight} strokeWidth={2.4} strokeLinecap="round" /></Svg>
            <Text style={st.cmpT}>Comparer</Text>
          </Pressable>
        )}
      </View>
      <View style={{ paddingHorizontal: 20, marginBottom: 4 }}><Stamp t={t} /></View>

      {spots.length ? spots.map(s => <FavCard key={s.slug} s={s} />) : (
        <View style={st.empty}>
          <Text style={st.emptyT}>Vos spots, d’un coup d’œil</Text>
          <Text style={st.emptyS}>Ajoutez vos spots : chacun aura ici sa prévision des 48 prochaines heures et la mesure de sa bouée. Leurs données restent lisibles sans réseau.</Text>
        </View>
      )}

      <Pressable onPress={() => router.push({ pathname: '/recherche', params: { pick: 'fav' } })} style={({ pressed }) => [st.add, pressed && st.pressed]} accessibilityLabel="Ajouter un spot à Ma côte">
        <Text style={st.addT}>+ Ajouter un spot</Text>
      </Pressable>
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
        <View style={st.now}>
          <Text style={st.v}>{fr(n.hs)}<Text style={st.u}> m</Text></Text>
          <View style={st.vRow}><Text style={st.s}>{n.tp != null ? `${Math.round(n.tp)} s` : '—'}</Text><Arrow dir={n.dir} size={10} color={C.ink2} /><Text style={st.s}>{sector(n.dir)}</Text></View>
        </View>
        <View style={st.now}>
          <Text style={st.v}>{n.wind ?? '—'}<Text style={st.u}> km/h</Text></Text>
          <Text style={[st.s, wc && wc !== 'lisse' && { color: col, fontFamily: F.tX }]} numberOfLines={1}>{wc ? WIND_WORD[wc] : sector(n.wdir)}</Text>
        </View>
      </View>
      <Strip s={s} />
      {ref && (
        <View style={st.buoy}>
          {freshOf(ref.b) === 'live' ? <Blink size={6} color={C.liveOnBuoy} /> : <View style={st.bdot} />}
          <Text style={st.bk} numberOfLines={1}>{ref.b.name}</Text>
          <Text style={st.bv}>{fr(ref.b.hs)} m{perTxt(ref.b) ? ` · ${perTxt(ref.b)}` : ''}</Text>
          <Text style={st.ba} numberOfLines={1}>{ageTxt(ref.b.time)}</Text>
        </View>
      )}
    </Pressable>
  );
}

/** Mini-frise 48 h : une colonne toutes les 3 h à partir de l'heure pleine en cours, barre de houle à l'échelle 0-3 m
 *  (couleur de la frise), filet d'orientation du vent. Valeurs lues par instant exact (src/series.ts). */
function Strip({ s }: { s: SpotLite }) {
  const [sheet, setSheet] = useState<Sheet | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let alive = true;
    loadSheetShared(s.slug).then(r => { if (alive) setSheet(r.data); }, () => { if (alive) setErr(true); });
    return () => { alive = false; };
  }, [s.slug]);
  if (!sheet) return <View style={st.strip}><Text style={st.stripMsg}>{err ? 'Prévision 48 h indisponible hors connexion' : ' '}</Text></View>;
  const t0 = tMs(sheet.t0), tz = placeTz(sheet), start = Math.floor(Date.now() / 36e5) * 36e5;
  const cols = Array.from({ length: N }, (_, k) => {
    const ms = start + k * STEP * 36e5, p = partsIn(ms, tz);
    const hs = valueAt(t0, sheet.hs, ms), w = valueAt(t0, sheet.wind, ms), wd = valueAt(t0, sheet.wdir, ms);
    return { ms, p, hs, tp: valueAt(t0, sheet.tp, ms), c: windCat(w, wd, sheet.ori) };
  });
  const top = Math.max(3, ...cols.map(c => c.hs ?? 0));
  const max = cols.reduce((a, c) => ((c.hs ?? -1) > (a.hs ?? -1) ? c : a), cols[0]);
  const cc = (c: (typeof cols)[number]['c']) => (c === 'offshore' || c === 'side-off' ? C.off : c === 'de côté' ? C.side : c === 'onshore' ? C.on : 'transparent');
  return (
    <View accessibilityLabel={`48 prochaines heures : houle la plus haute ${fr(max.hs)} mètre ${J[max.p.wd]} ${max.p.h} heures`}>
      <View style={st.strip}>
        {/* échelle discrète des barres (retour du porteur) : haut = 3 m (ou le maximum s'il est plus haut), trait à mi-hauteur */}
        <View style={st.scale} accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <Text style={st.scaleT}>{fr(top, top % 1 ? 1 : 0)} m</Text>
          <Text style={st.scaleT}>{fr(top / 2, (top / 2) % 1 ? 1 : 0)}</Text>
          <Text style={st.scaleT}>0</Text>
        </View>
        {cols.map((c, k) => (
          <View key={k} style={st.col}>
            <View style={st.barBox}>
              <View style={st.mid} />
              {c.hs != null && <View style={[st.bar, { height: `${Math.max(4, (c.hs / top) * 100)}%`, backgroundColor: sizeCell(c.hs) }]} />}
            </View>
            <View style={[st.wind, { backgroundColor: cc(c.c) }]} />
            <Text style={[st.hh, c.p.h < 3 && st.hhDay]} numberOfLines={1}>{c.p.h < 3 ? J[c.p.wd] : c.p.h % 6 === 0 ? `${c.p.h}h` : ''}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const st = themed(() => StyleSheet.create({
  top: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingBottom: 8 },
  h1: { fontFamily: F.num, fontSize: 28, color: C.ink, letterSpacing: -1 },
  cmp: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 38, paddingHorizontal: 14, borderRadius: 19, backgroundColor: C.night },
  cmpT: { fontFamily: F.tX, fontSize: 13, color: C.onNight },
  card: { marginHorizontal: 12, marginTop: 10, padding: 14, borderRadius: 26, backgroundColor: C.card, gap: 10 },
  pressed: { opacity: 0.82, transform: [{ scale: 0.985 }] },
  cardHd: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  name: { fontFamily: F.num, fontSize: 17, color: C.ink, letterSpacing: -0.5 },
  reg: { fontFamily: F.tB, fontSize: 12, color: C.ink3, marginTop: 2 },
  now: { alignItems: 'flex-end' },
  vRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  v: { fontFamily: F.num, fontSize: 17, color: C.ink, letterSpacing: -0.6 },
  u: { fontFamily: F.tB, fontSize: 10.5, letterSpacing: 0 },
  s: { fontFamily: F.tB, fontSize: 11.5, color: C.ink2 },
  strip: { flexDirection: 'row', gap: 2, height: 62, alignItems: 'flex-end' },
  stripMsg: { fontFamily: F.tB, fontSize: 12, color: C.ink3, alignSelf: 'center' },
  col: { flex: 1, alignItems: 'stretch', gap: 2 },
  barBox: { height: 38, justifyContent: 'flex-end', borderRadius: 4, backgroundColor: C.soft, overflow: 'hidden' },
  mid: { position: 'absolute', left: 0, right: 0, top: 19, height: StyleSheet.hairlineWidth, backgroundColor: C.line },
  scale: { width: 24, height: 38, marginBottom: 20, justifyContent: 'space-between' },   // 20 = filet du vent + heures sous les barres
  scaleT: { fontFamily: F.tB, fontSize: 8.5, lineHeight: 10, color: C.ink3 },
  bar: { borderRadius: 4 },
  wind: { height: 3, borderRadius: 2 },
  hh: { fontFamily: F.tB, fontSize: 9, color: C.ink3, textAlign: 'center', height: 13 },
  hhDay: { fontFamily: F.tX, color: C.ink },
  stripCap: { fontFamily: F.tB, fontSize: 11.5, color: C.ink2, marginTop: 4 },
  buoy: { flexDirection: 'row', alignItems: 'center', gap: 7, height: 34, paddingHorizontal: 12, borderRadius: 17, backgroundColor: C.buoySurface },
  bdot: { width: 6, height: 6, borderRadius: 3, backgroundColor: C.onBuoy2 },
  bk: { flexShrink: 1, fontFamily: F.tX, fontSize: 11.5, color: C.onBuoy },
  bv: { fontFamily: F.num, fontSize: 12, color: C.measureOnBuoy },
  ba: { flex: 1, textAlign: 'right', fontFamily: F.tB, fontSize: 11, color: C.onBuoy2 },
  empty: { marginHorizontal: 12, marginTop: 10, padding: 22, borderRadius: 26, backgroundColor: C.card, gap: 8 },
  emptyT: { fontFamily: F.num, fontSize: 18, color: C.ink, letterSpacing: -0.5 },
  emptyS: { fontFamily: F.t, fontSize: 14, lineHeight: 20, color: C.ink2 },
  add: { alignSelf: 'center', marginTop: 16, height: 46, paddingHorizontal: 22, borderRadius: 23, borderWidth: 1.5, borderColor: C.ink, borderStyle: 'dashed', justifyContent: 'center' },
  addT: { fontFamily: F.tX, fontSize: 14, color: C.ink },
}));
