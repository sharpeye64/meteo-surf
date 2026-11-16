import { useEffect, useMemo, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import Arrow from './Arrow';
import Brand from './Brand';
import { ageTxt, Buoy, country, fr, Index, loadSheet, regionName, sector, Sheet, SpotLite, windRel } from './data';
import { SpotRow } from './SpotList';
import { useBarSpace } from './TabBar';
import { C, F, sizeCell, windCell } from './theme';

type Props = {
  index: Index; favs: string[]; offline: boolean; refreshing: boolean; onRefresh: () => void;
  onOpen: (s: SpotLite) => void; onBuoy: (b: Buoy) => void;
};

const CTY = ['France', 'Espagne', 'Portugal'];
const norm =(t: string) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
const km = (a: SpotLite, b: SpotLite) => {
  const x = (b.lon - a.lon) * Math.cos(((a.lat + b.lat) / 2) * Math.PI / 180), y = b.lat - a.lat;
  return Math.sqrt(x * x + y * y) * 111.2;
};
const hh = (d: Date) => `${d.getHours()} h${d.getMinutes() ? ' ' + String(d.getMinutes()).padStart(2, '0') : ''}`;

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
  const biggest = useMemo(() => [...index.spots].sort((a, b) => (b.now.hs ?? 0) - (a.now.hs ?? 0)).slice(0, 8), [index]);
  const live = index.buoys.filter(b => (Date.now() - new Date(b.time + ':00').getTime()) / 36e5 < 2);

  // Régions du nord au sud, rangées par pays.
  const regions = useMemo(() => {
    const m = new Map<string, SpotLite[]>();
    index.spots.forEach(s => { if (!m.has(s.region)) m.set(s.region, []); m.get(s.region)!.push(s); });
    return [...m.entries()].map(([r, ss]) => {
      const hs = ss.map(s => s.now.hs).filter((v): v is number => v != null);
      return { r, c: country(r), ss: ss.sort((a, b) => b.lat - a.lat), top: Math.max(...ss.map(s => s.lat)), lo: Math.min(...hs), hi: Math.max(...hs) };
    }).sort((a, b) => CTY.indexOf(a.c) - CTY.indexOf(b.c) || b.top - a.top);
  }, [index]);

  const hour = new Date().getHours();
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
          {!hero && <Strip title="Houle la plus grosse maintenant" list={biggest} onOpen={onOpen} />}

          {!!live.length && (
            <View style={st.liveCard}>
              <View style={st.liveHd}><View style={st.dot} /><Text style={st.liveT}>BOUÉES EN DIRECT</Text><Text style={st.liveN}>{live.length}</Text></View>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, paddingRight: 16 }}>
                {live.map(b => (
                  <Pressable key={b.id} style={st.bu} onPress={() => onBuoy(b)}>
                    <View><Text style={st.buN}>{b.name}</Text><Text style={st.buS}>{ageTxt(b.time)}{b.tp ? ` · ${Math.round(b.tp)} s` : ''}</Text></View>
                    <View style={st.buV}><Text style={st.buVT}>{fr(b.hs)}</Text></View>
                  </Pressable>
                ))}
              </ScrollView>
            </View>
          )}

          <Text style={[st.lbl, { marginTop: 26 }]}>Toute la côte</Text>
          {regions.map((g, i) => (
            <View key={g.r}>
              {(i === 0 || regions[i - 1].c !== g.c) && <Text style={st.cty}>{g.c}</Text>}
              <Pressable onPress={() => setOpen(o => (o === g.r ? null : g.r))} style={({ pressed }) => [st.reg, open === g.r && st.regOn, pressed && { opacity: 0.8 }]}>
                <View style={{ flex: 1 }}>
                  <Text style={st.regN}>{regionName(g.r)}</Text>
                  <View style={st.strip}>{g.ss.map(s => <View key={s.slug} style={{ flex: 1, backgroundColor: sizeCell(s.now.hs) }} />)}</View>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={st.regV}>{fr(g.lo)}–{fr(g.hi)} m</Text>
                  <Text style={st.regC}>{g.ss.length} spots {open === g.r ? '▴' : '▾'}</Text>
                </View>
              </Pressable>
              {open === g.r && <View style={{ marginTop: 8 }}>{g.ss.map(s => <SpotRow key={s.slug} s={s} fav={favs.includes(s.slug)} onOpen={onOpen} />)}</View>}
            </View>
          ))}
          <Text style={st.foot}>Mis à jour {ageTxt(index.generated)} · prévisions indicatives, à confirmer sur place</Text>
        </View>
      )}
    </ScrollView>
  );
}

/** Votre spot en grand : houle maintenant, les 12 prochaines heures, le vent et la prochaine marée. */
function Hero({ s, onOpen }: { s: SpotLite; onOpen: (s: SpotLite) => void }) {
  const [sh, setSh] = useState<Sheet | null>(null);
  useEffect(() => { let on = true; loadSheet(s.slug).then(r => on && setSh(r.data)).catch(() => {}); return () => { on = false; }; }, [s.slug]);
  const next = useMemo(() => {
    if (!sh) return null;
    const t0 = new Date(sh.t0 + ':00').getTime(), i0 = Math.max(0, Math.floor((Date.now() - t0) / 36e5));
    const hours = Array.from({ length: 12 }, (_, k) => ({ h: sh.hs[i0 + k] ?? null, d: new Date(t0 + (i0 + k) * 36e5) }));
    const tide = (sh.tide?.extremes || []).find(e => new Date(e.t + ':00').getTime() > Date.now());
    return { hours, tide };
  }, [sh]);
  const max = Math.max(1, ...(next?.hours.map(x => x.h ?? 0) || [1]));
  const rel = windRel(s.now.wdir, s.ori);

  return (
    <Pressable onPress={() => onOpen(s)} style={({ pressed }) => [st.hero, pressed && { opacity: 0.9 }]}>
      <Text style={st.heroK}>VOTRE SPOT · {regionName(s.region).toUpperCase()}</Text>
      <Text style={st.heroName} numberOfLines={1}>{s.name}</Text>
      <View style={st.heroRow}>
        <Text style={st.heroH}>{fr(s.now.hs)}<Text style={st.heroU}> m</Text></Text>
        <View style={{ gap: 4 }}>
          <Text style={st.heroP}>{fr(s.now.tp, 0)} s</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}><Arrow dir={s.now.dir} size={13} color={C.sandText} /><Text style={st.heroS}>{sector(s.now.dir)}</Text></View>
        </View>
      </View>
      <View style={st.bars}>
        {(next?.hours || Array.from({ length: 12 }, () => ({ h: null, d: new Date() }))).map((x, k) => (
          <View key={k} style={{ flex: 1, justifyContent: 'flex-end' }}>
            <View style={{ height: x.h == null ? 4 : 6 + (x.h / max) * 34, borderRadius: 3, backgroundColor: x.h == null ? 'rgba(42,33,18,0.15)' : sizeCell(x.h) }} />
          </View>
        ))}
      </View>
      {next && <View style={st.barsL}><Text style={st.heroSm}>maintenant</Text><Text style={st.heroSm}>{hh(next.hours[6].d)}</Text><Text style={st.heroSm}>{hh(next.hours[11].d)}</Text></View>}
      <View style={st.heroFoot}>
        <View style={[st.windPill, { backgroundColor: windCell(s.now.wind) }]}>
          <Arrow dir={s.now.wdir} size={11} color={C.ink} />
          <Text style={st.windT}>{fr(s.now.wind, 0)} km/h{rel ? ` · ${rel}` : ''}</Text>
        </View>
        {next?.tide && <Text style={st.heroS}>{next.tide.type} {hh(new Date(next.tide.t + ':00'))}</Text>}
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

const st = StyleSheet.create({
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
  hero: { marginHorizontal: 16, borderRadius: 26, padding: 18, backgroundColor: C.sand },
  heroK: { fontFamily: F.tX, fontSize: 10.5, letterSpacing: 1.3, color: '#7a5f33' },
  heroEmpty: { fontFamily: F.t, fontSize: 14.5, lineHeight: 20, color: C.sandText },
  heroName: { fontFamily: F.num, fontSize: 22, color: C.sandText, letterSpacing: -0.6, marginTop: 4 },
  heroRow: { flexDirection: 'row', alignItems: 'center', gap: 14, marginTop: 6 },
  heroH: { fontFamily: F.numX, fontSize: 52, color: C.sandText, letterSpacing: -2.5 },
  heroU: { fontFamily: F.num, fontSize: 20, letterSpacing: 0 },
  heroP: { fontFamily: F.num, fontSize: 17, color: C.sandText },
  heroS: { fontFamily: F.tX, fontSize: 13, color: C.sandText },
  heroSm: { fontFamily: F.tB, fontSize: 11, color: '#7a5f33' },
  bars: { flexDirection: 'row', gap: 4, height: 42, alignItems: 'flex-end', marginTop: 12 },
  barsL: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 5 },
  heroFoot: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 14 },
  windPill: { flexDirection: 'row', alignItems: 'center', gap: 5, height: 28, paddingHorizontal: 11, borderRadius: 14 },
  windT: { fontFamily: F.tX, fontSize: 12.5, color: C.ink },
  mini: { width: 108, backgroundColor: C.card, borderRadius: 18, padding: 6, paddingBottom: 10, gap: 8 },
  miniC: { height: 56, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  miniV: { fontFamily: F.num, fontSize: 19, color: C.ink, letterSpacing: -0.8 },
  miniU: { fontFamily: F.tB, fontSize: 11, color: 'rgba(16,32,44,0.7)' },
  miniN: { fontFamily: F.tX, fontSize: 13, color: C.ink, paddingHorizontal: 4 },
  liveCard: { marginTop: 24, marginLeft: 16, paddingVertical: 14, paddingLeft: 16, borderTopLeftRadius: 24, borderBottomLeftRadius: 24, backgroundColor: C.card },
  liveHd: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10, paddingRight: 16 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: C.live },
  liveT: { fontFamily: F.tX, fontSize: 11, letterSpacing: 1.3, color: '#7a6f55', flex: 1 },
  liveN: { fontFamily: F.tX, fontSize: 11, color: '#a89c7e' },
  bu: { flexDirection: 'row', alignItems: 'center', gap: 10, height: 46, borderRadius: 23, paddingLeft: 16, paddingRight: 5, backgroundColor: '#f4efe3' },
  buN: { fontFamily: F.tB, fontSize: 13.5, color: C.ink },
  buS: { fontFamily: F.t, fontSize: 11.5, color: '#7a6f55' },
  buV: { height: 36, minWidth: 50, borderRadius: 18, paddingHorizontal: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: C.sandB },
  buVT: { fontFamily: F.num, fontSize: 15, color: C.sandText, letterSpacing: -0.5 },
  cty: { fontFamily: F.num, fontSize: 15, color: C.ink, marginHorizontal: 20, marginTop: 12, marginBottom: 8 },
  reg: { flexDirection: 'row', alignItems: 'center', gap: 14, marginHorizontal: 16, marginBottom: 8, paddingVertical: 13, paddingHorizontal: 16, borderRadius: 20, backgroundColor: C.card },
  regOn: { borderWidth: 1.5, borderColor: C.sandB },
  regN: { fontFamily: F.tX, fontSize: 15, color: C.ink },
  strip: { flexDirection: 'row', height: 5, borderRadius: 3, overflow: 'hidden', marginTop: 8, gap: 1 },
  regV: { fontFamily: F.num, fontSize: 14, color: C.ink },
  regC: { fontFamily: F.tB, fontSize: 11.5, color: C.ink3, marginTop: 3 },
  foot: { textAlign: 'center', color: C.ink3, marginTop: 20, fontSize: 12, fontFamily: F.t, paddingHorizontal: 24 },
});
