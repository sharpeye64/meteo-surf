import { useEffect, useMemo, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import Svg, { Circle, G, Path, Text as SvgText } from 'react-native-svg';
import Arrow from './Arrow';
import Brand from './Brand';
import { ageH, ageTxt, Buoy, country, fr, Index, km, loadSheet, perTxt, regionName, sector, Sheet, SpotLite, windRel } from './data';
import { hhIn, partsIn, placeTz, tMs } from './time';
import { Blink } from './Live';
import { SpotRow } from './SpotList';
import { useBarSpace } from './TabBar';
import { C, F, sizeCell, themed, windCell } from './theme';

type Props = {
  index: Index; favs: string[]; offline: boolean; refreshing: boolean; onRefresh: () => void;
  onOpen: (s: SpotLite) => void; onBuoy: (b: Buoy) => void;
};

const CTY = ['France', 'Espagne', 'Portugal'];
const norm =(t: string) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

/** Onglet Spots « Mon tableau » : la recherche toujours en haut, votre spot en grand, ceux d'à côté, puis toute la côte par région. */
export default function Home({ index, favs, offline, refreshing, onRefresh, onOpen, onBuoy }: Props) {
  const pad = useBarSpace();
  const [q, setQ] = useState('');
  const [open, setOpen] = useState<string | null>(null);
  const bySlug = useMemo(() => Object.fromEntries(index.spots.map(s => [s.slug, s])), [index]);
  const mine = favs.map(f => bySlug[f]).filter(Boolean) as SpotLite[];
  const hero = mine[0];

  // Recherche dans tous les spots (nom, commune, région), sans accents, sans filtre.
  const results = useMemo(() => {
    const t = norm(q.trim());
    if (!t) return [];
    return index.spots
      .map(s => ({ s, n: norm(s.name), o: norm(`${s.commune || ''} ${s.region}`) }))
      .filter(x => x.n.includes(t) || x.o.includes(t))
      .sort((a, b) => Number(!a.n.startsWith(t)) - Number(!b.n.startsWith(t)) || Number(!a.n.includes(t)) - Number(!b.n.includes(t)) || b.s.lat - a.s.lat)
      .map(x => x.s);
  }, [index, q]);

  const near = useMemo(() => (hero ? index.spots.filter(s => s.slug !== hero.slug).map(s => ({ s, d: km(hero, s) })).sort((a, b) => a.d - b.d).slice(0, 8).map(x => x.s) : []), [index, hero]);
  const live = index.buoys.filter(b => ageH(b.time) < 2);

  // Régions du nord au sud, rangées par pays.
  const regions = useMemo(() => {
    const m = new Map<string, SpotLite[]>();
    index.spots.forEach(s => { if (!m.has(s.region)) m.set(s.region, []); m.get(s.region)!.push(s); });
    return [...m.entries()].map(([r, ss]) => ({ r, c: country(r), ss: ss.sort((a, b) => b.lat - a.lat), top: Math.max(...ss.map(s => s.lat)) })).sort((a, b) => CTY.indexOf(a.c) - CTY.indexOf(b.c) || b.top - a.top);
  }, [index]);

  const hour = partsIn(Date.now(), 'Europe/Paris').h;   // heure de Paris (liste de toute la côte), comme la carte du site
  return (
    <ScrollView stickyHeaderIndices={[1]} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag"
      contentContainerStyle={{ paddingBottom: pad }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.ink} />}>
      <View style={st.head}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}><Brand h={22} /></View>
        {offline && <Text style={st.off}>hors connexion</Text>}
      </View>

      {/* Toujours visible, même en faisant défiler : on cherche n'importe quel spot sans passer par des filtres. */}
      <View style={st.sticky}>
        <View style={st.search}>
          <Text style={st.lens}>⌕</Text>
          <TextInput value={q} onChangeText={setQ} placeholder={`Chercher parmi ${index.spots.length} spots…`} placeholderTextColor={C.ink3}
            style={st.input} autoCorrect={false} returnKeyType="search" clearButtonMode="while-editing" />
          {!!q && <Pressable onPress={() => setQ('')} hitSlop={10}><Text style={st.clear}>✕</Text></Pressable>}
        </View>
      </View>

      {q.trim() ? (
        <View style={{ paddingTop: 6 }}>
          <Text style={st.lbl}>{results.length ? `${results.length} spot${results.length > 1 ? 's' : ''}` : 'Aucun spot ne correspond'}</Text>
          {results.map(s => <SpotRow key={s.slug} s={s} fav={favs.includes(s.slug)} onOpen={onOpen} place />)}
        </View>
      ) : (
        <View>
          <Text style={st.h1}>{hour < 5 || hour >= 18 ? 'Bonsoir' : 'Bonjour'}</Text>

          {hero ? <Hero s={hero} onOpen={onOpen} /> : (
            <View style={[st.hero, { gap: 6 }]}>
              <Text style={st.heroK}>VOTRE SPOT</Text>
              <Text style={st.heroEmpty}>Touchez l’étoile ☆ sur la fiche d’un spot : il s’affichera ici en grand, avec les spots autour.</Text>
            </View>
          )}

          {mine.length > 1 && <Strip title="Mes autres spots" list={mine.slice(1)} onOpen={onOpen} />}
          {hero && <Strip title={`Autour de ${hero.name}`} list={near} onOpen={onOpen} />}

          {!!live.length && (
            <View style={st.liveCard}>
              <View style={st.liveHd}><Blink size={7} /><Text style={st.liveT}>BOUÉES EN DIRECT</Text><Text style={st.liveN}>{live.length}</Text></View>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingRight: 16 }}>
                {live.map((b, i) => (
                  <Pressable key={b.id} style={st.bu} onPress={() => onBuoy(b)}>
                    <Blink size={7} delay={(i % 3) * 450} />
                    <View><Text style={st.buN}>{b.name}</Text><Text style={st.buS}>{ageTxt(b.time)}{perTxt(b) ? ` · ${perTxt(b)}` : ''}</Text></View>
                    <View style={st.buV}><Text style={st.buVT}>{fr(b.hs)}</Text></View>
                  </Pressable>
                ))}
              </ScrollView>
            </View>
          )}

          <Text style={[st.lbl, { marginTop: 26 }]}>Parcourir la côte</Text>
          {CTY.map(c => {
            const rs = regions.filter(g => g.c === c);
            if (!rs.length) return null;
            return (
              <View key={c} style={st.group}>
                <Text style={st.cty}>{c}</Text>
                {rs.map((g, i) => (
                  <View key={g.r} style={i > 0 && st.sep}>
                    <Pressable onPress={() => setOpen(o => (o === g.r ? null : g.r))} style={({ pressed }) => [st.reg, pressed && { opacity: 0.6 }]}>
                      <Text style={st.regN}>{regionName(g.r)}</Text>
                      <Text style={st.regC}>{g.ss.length}</Text>
                      <Text style={[st.chev, open === g.r && { transform: [{ rotate: '90deg' }] }]}>›</Text>
                    </Pressable>
                    {open === g.r && g.ss.map(s => (
                      <Pressable key={s.slug} onPress={() => onOpen(s)} style={({ pressed }) => [st.sub, pressed && { opacity: 0.6 }]}>
                        <Text style={st.subN} numberOfLines={1}>{favs.includes(s.slug) ? '★ ' : ''}{s.name}</Text>
                        <Text style={st.subT}>{fr(s.now.tp, 0)} s</Text>
                        <View style={[st.subH, { backgroundColor: sizeCell(s.now.hs) }]}><Text style={st.subHT}>{fr(s.now.hs)}</Text></View>
                      </Pressable>
                    ))}
                  </View>
                ))}
              </View>
            );
          })}
          <Text style={st.foot}>Mis à jour {ageTxt(index.generated)} · prévisions indicatives, à confirmer sur place</Text>
        </View>
      )}
    </ScrollView>
  );
}

const NCOL = 7, STEP = 2;   // mini-frise : 7 colonnes, toutes les 2 h, à partir de l'heure actuelle

/** Votre spot en grand, avec la journée en mini-frise (comme la frise du site) : houle, vent, puis la courbe de marée
 *  avec la pleine mer et la basse mer posées à leur heure. */
function Hero({ s, onOpen }: { s: SpotLite; onOpen: (s: SpotLite) => void }) {
  const [sh, setSh] = useState<Sheet | null>(null);
  const [w, setW] = useState(0);
  useEffect(() => { let on = true; loadSheet(s.slug).then(r => on && setSh(r.data)).catch(() => {}); return () => { on = false; }; }, [s.slug]);

  const day = useMemo(() => {
    if (!sh) return null;
    // Le soir (après 19 h) ou la nuit, on montre la journée suivante (ou celle qui vient) à partir de 7 h.
    // heure DU SPOT (issue #2 : Lisbonne au Portugal), pas celle du téléphone
    const t0 = tMs(sh.t0), tz = placeTz(sh), nowP = partsIn(Date.now(), tz), hr = nowP.h, nowI = Math.max(1, Math.floor((Date.now() - t0) / 36e5));
    const tgt = hr >= 19 ? partsIn(Date.now() + 864e5, tz).date : nowP.date;
    const mI = sh.hs.findIndex((_, i) => { const p = partsIn(t0 + i * 36e5, tz); return p.date === tgt && p.h === 7; });
    const later = hr >= 19 || hr < 6, i0 = later ? Math.max(1, mI >= 0 ? mI : nowI) : nowI;
    const cols = Array.from({ length: NCOL }, (_, k) => i0 + k * STEP).filter(i => i < sh.hs.length);
    // marée : hauteur d'eau heure par heure sur toute la largeur, et les PM / BM qui tombent dedans
    const from = i0 - STEP / 2, to = i0 + NCOL * STEP - STEP / 2;
    const sea: [number, number][] = [];
    for (let i = from; i <= to; i++) { const v = sh.sea[i]; if (v != null) sea.push([i, v]); }
    const ext = (sh.tide?.extremes || []).map(e => ({ ...e, f: (tMs(e.t) - t0) / 36e5 })).filter(e => e.f >= from && e.f <= to);
    return { t0, tz, cols, from, to, sea, ext, later, tomorrow: hr >= 19 };
  }, [sh]);

  const H = 44;
  let tide: React.ReactNode = null;
  if (day && w && day.sea.length > 3) {
    const xs = (f: number) => ((f - day.from) / (day.to - day.from)) * w;
    const vs = day.sea.map(x => x[1]), mn = Math.min(...vs), mx = Math.max(...vs);
    const ys = (v: number) => 6 + (1 - (v - mn) / Math.max(0.01, mx - mn)) * (H - 12);
    const d = day.sea.map(([i, v], k) => `${k ? 'L' : 'M'}${xs(i).toFixed(1)},${ys(v).toFixed(1)}`).join(' ');
    tide = (
      <Svg width={w} height={H} style={{ marginTop: 6 }}>
        <Path d={`${d} L${xs(day.sea[day.sea.length - 1][0]).toFixed(1)},${H} L${xs(day.sea[0][0]).toFixed(1)},${H} Z`} fill={C.sandMuted} fillOpacity={0.16} />
        <Path d={d} stroke={C.sandMuted} strokeWidth={1.6} fill="none" />
        {day.ext.map(e => {
          const x = xs(e.f), y = e.type === 'PM' ? 6 : H - 6, tx = Math.min(w - 26, Math.max(26, x));
          return (
            <G key={e.t}>
              <Circle cx={x} cy={y} r={3} fill={C.sandText} />
              <SvgText x={tx} y={e.type === 'PM' ? y + 15 : y - 7} fontSize={10.5} fontFamily={F.tX} fill={C.sandText} textAnchor="middle">{`${e.type} ${+e.t.slice(11, 13)} h${+e.t.slice(14, 16) ? ' ' + e.t.slice(14, 16) : ''}`}</SvgText>
            </G>
          );
        })}
      </Svg>
    );
  }

  return (
    <Pressable onPress={() => onOpen(s)} style={({ pressed }) => [st.hero, pressed && { opacity: 0.9 }]}>
      <View style={st.heroTop}>
        <View style={{ flex: 1, minWidth: 0 }}>
          <Text style={st.heroK} numberOfLines={1}>VOTRE SPOT · {day?.tomorrow ? 'DEMAIN' : regionName(s.region).toUpperCase()}</Text>
          <Text style={st.heroName} numberOfLines={1}>{s.name}</Text>
        </View>
        <View style={{ alignItems: 'flex-end' }}>
          <Text style={st.heroH}>{fr(s.now.hs)}<Text style={st.heroU}> m</Text></Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
            <Text style={st.heroS}>{fr(s.now.tp, 0)} s</Text><Arrow dir={s.now.dir} size={11} color={C.sandText} /><Text style={st.heroS}>{sector(s.now.dir)}</Text>
          </View>
        </View>
      </View>

      <View onLayout={e => setW(e.nativeEvent.layout.width)} style={{ marginTop: 12 }}>
        {day ? (
          <>
            <View style={st.mrow}>{day.cols.map((i, k) => <Text key={i} style={[st.mh, k === 0 && { color: C.sandText }]}>{k === 0 && !day.later ? 'maint.' : hhIn(day.t0 + i * 36e5, day.tz)}</Text>)}</View>
            <View style={st.mrow}>{day.cols.map((i, k) => (
              <View key={i} style={[st.mc, { backgroundColor: sizeCell(sh!.hs[i]) }, k === 0 && !day.later && st.mcOn]}>
                <Text style={st.mcV}>{fr(sh!.hs[i])}</Text><Text style={st.mcU}>{fr(sh!.tp[i], 0)} s</Text>
              </View>
            ))}</View>
            <View style={st.mrow}>{day.cols.map(i => (
              <View key={i} style={[st.mw, { backgroundColor: windCell(sh!.wind[i]) }]}>
                <Arrow dir={sh!.wdir[i]} size={9} color={C.ink} /><Text style={st.mwT}>{fr(sh!.wind[i], 0)}</Text>
              </View>
            ))}</View>
            {tide}
          </>
        ) : <View style={{ height: 120 }} />}
      </View>
    </Pressable>
  );
}

/** Une rangée de petites cartes qui défile de côté. */
function Strip({ title, list, onOpen }: { title: string; list: SpotLite[]; onOpen: (s: SpotLite) => void }) {
  if (!list.length) return null;
  return (
    <View>
      <Text style={[st.lbl, { marginTop: 22 }]}>{title}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingHorizontal: 16 }}>
        {list.map(s => (
          <Pressable key={s.slug} onPress={() => onOpen(s)} style={({ pressed }) => [st.mini, pressed && { opacity: 0.85 }]}>
            <View style={[st.miniC, { backgroundColor: sizeCell(s.now.hs) }]}>
              <Text style={st.miniV}>{fr(s.now.hs)}</Text>
              <Text style={st.miniU}>{fr(s.now.tp, 0)} s</Text>
            </View>
            <Text style={st.miniN} numberOfLines={1}>{s.name}</Text>
          </Pressable>
        ))}
      </ScrollView>
    </View>
  );
}

const st = themed(() => StyleSheet.create({
  head: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingTop: 8, paddingBottom: 4 },
  off: { fontFamily: F.tB, fontSize: 12, color: C.coral },
  sticky: { backgroundColor: C.bg, paddingTop: 8, paddingBottom: 6 },
  search: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, backgroundColor: C.card, borderRadius: 999, paddingHorizontal: 18, height: 50,
    shadowColor: '#10202c', shadowOpacity: 0.08, shadowRadius: 14, shadowOffset: { width: 0, height: 6 }, elevation: 2 },
  lens: { fontSize: 20, color: C.ink2, marginRight: 8 },
  input: { flex: 1, height: 50, fontSize: 16, color: C.ink, fontFamily: F.t },
  clear: { fontSize: 14, color: C.ink3, paddingLeft: 8 },
  h1: { fontFamily: F.numX, fontSize: 28, color: C.ink, letterSpacing: -1, marginTop: 14, marginHorizontal: 20, marginBottom: 12 },
  lbl: { fontFamily: F.tX, fontSize: 11.5, letterSpacing: 1.3, textTransform: 'uppercase', color: C.gold, marginHorizontal: 20, marginBottom: 10 },
  hero: { marginHorizontal: 16, borderRadius: 26, padding: 18, backgroundColor: C.sandCard },
  heroK: { fontFamily: F.tX, fontSize: 10.5, letterSpacing: 1.3, color: C.sandMuted },
  heroEmpty: { fontFamily: F.t, fontSize: 14.5, lineHeight: 20, color: C.sandText },
  heroTop: { flexDirection: 'row', alignItems: 'flex-end', gap: 10 },
  heroName: { fontFamily: F.num, fontSize: 22, color: C.sandText, letterSpacing: -0.6, marginTop: 4 },
  heroH: { fontFamily: F.numX, fontSize: 34, color: C.sandText, letterSpacing: -1.5, lineHeight: 38 },
  heroU: { fontFamily: F.num, fontSize: 15, letterSpacing: 0 },
  heroS: { fontFamily: F.tX, fontSize: 12, color: C.sandText },
  mrow: { flexDirection: 'row', gap: 3, marginTop: 3 },
  mh: { flex: 1, textAlign: 'center', fontFamily: F.tX, fontSize: 10.5, color: C.sandMuted },
  mc: { flex: 1, height: 40, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  mcOn: { borderWidth: 2, borderColor: C.sandText },
  mcV: { fontFamily: F.num, fontSize: 13, color: C.ink, letterSpacing: -0.5 },
  mcU: { fontFamily: F.tB, fontSize: 9.5, color: C.cellU },
  mw: { flex: 1, height: 22, borderRadius: 7, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 2 },
  mwT: { fontFamily: F.tX, fontSize: 10.5, color: C.ink },
  mini: { width: 108, backgroundColor: C.card, borderRadius: 18, padding: 6, paddingBottom: 10, gap: 8 },
  miniC: { height: 56, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  miniV: { fontFamily: F.num, fontSize: 19, color: C.ink, letterSpacing: -0.8 },
  miniU: { fontFamily: F.tB, fontSize: 11, color: C.cellU },
  miniN: { fontFamily: F.tX, fontSize: 13, color: C.ink, paddingHorizontal: 4 },
  liveCard: { marginTop: 24, marginLeft: 16, paddingVertical: 14, paddingLeft: 16, borderTopLeftRadius: 24, borderBottomLeftRadius: 24, backgroundColor: C.card },
  liveHd: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10, paddingRight: 16 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: C.live },
  liveT: { fontFamily: F.tX, fontSize: 11, letterSpacing: 1.3, color: C.creamText, flex: 1 },
  liveN: { fontFamily: F.tX, fontSize: 11, color: C.creamText2 },
  bu: { flexDirection: 'row', alignItems: 'center', gap: 10, height: 46, borderRadius: 23, paddingLeft: 16, paddingRight: 5, backgroundColor: C.cream },
  buN: { fontFamily: F.tB, fontSize: 13.5, color: C.ink },
  buS: { fontFamily: F.t, fontSize: 11.5, color: C.creamText },
  buV: { height: 36, minWidth: 50, borderRadius: 18, paddingHorizontal: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: C.pill },
  buVT: { fontFamily: F.num, fontSize: 15, color: C.sandText, letterSpacing: -0.5 },
  group: { marginHorizontal: 16, marginBottom: 12, paddingHorizontal: 16, paddingBottom: 4, borderRadius: 22, backgroundColor: C.card },
  cty: { fontFamily: F.num, fontSize: 14, color: C.ink, paddingTop: 14, paddingBottom: 4 },
  sep: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: C.line },
  reg: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 14 },
  regN: { flex: 1, fontFamily: F.tB, fontSize: 15, color: C.ink },
  regC: { fontFamily: F.tB, fontSize: 13, color: C.ink3 },
  chev: { fontFamily: F.tX, fontSize: 20, color: C.ink3, width: 14, textAlign: 'center', marginTop: -2 },
  sub: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 8, paddingLeft: 12 },
  subN: { flex: 1, fontFamily: F.t, fontSize: 14, color: C.ink },
  subT: { fontFamily: F.tB, fontSize: 12, color: C.ink3 },
  subH: { minWidth: 44, height: 26, borderRadius: 13, paddingHorizontal: 8, alignItems: 'center', justifyContent: 'center' },
  subHT: { fontFamily: F.num, fontSize: 12, color: C.ink },
  foot: { textAlign: 'center', color: C.ink3, marginTop: 20, fontSize: 12, fontFamily: F.t, paddingHorizontal: 24 },
}));
