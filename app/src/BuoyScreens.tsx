import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Line, Path, Text as SvgText } from 'react-native-svg';
import Arrow from './Arrow';
import { ageTxt, Buoy, buoyFits, dayTxt, BuoySheet, fr, freshOf, Index, isLive, km, loadBuoy, perTxt, refBuoy, sector } from './data';
import { tMs } from './time';
import { Blink } from './Live';
import { useBarSpace } from './TabBar';
import { C, F, themed } from './theme';

const ZONES = ['Bretagne', 'Golfe de Gascogne', 'Espagne', 'Portugal'];
/** Grande zone de côte d'une bouée, d'après sa position. */
const zone = (b: Buoy) => (b.lat < 42 ? 'Portugal' : b.lat < 44.5 && b.lon < -1.8 ? 'Espagne' : b.lat > 47 ? 'Bretagne' : 'Golfe de Gascogne');
/** En Espagne, on suit la côte : de la frontière vers l'ouest le long de la côte nord, puis la Galice vers le sud. */
const alongSpain = (a: Buoy, b: Buoy) => {
  const k = (x: Buoy) => (x.lat >= 43 ? -x.lon : 100 - x.lat);
  return k(a) - k(b);
};

/** Feu de fraîcheur, selon la cadence de la station (règle commune avec le site, src/rules.ts) : vert qui clignote (en direct),
 *  sable (récente), gris (ancienne ou muette). */
function Lamp({ b, i = 0 }: { b: Buoy; i?: number }) {
  const f = freshOf(b);
  return f === 'live' ? <Blink size={9} delay={(i % 3) * 450} /> : <View style={[st.lamp, { backgroundColor: f === 'recent' ? C.sandB : C.lampOld }]} />;
}

/** Une ligne de bouée dans une carte groupée. */
function BuoyLine({ b, i, note, first, onOpen }: { b: Buoy; i: number; note?: string; first?: boolean; onOpen: (b: Buoy) => void }) {
  return (
    <Pressable onPress={() => onOpen(b)} style={({ pressed }) => [st.line, !first && st.sep, pressed && { opacity: 0.6 }]}>
      <Lamp b={b} i={i} />
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={st.name} numberOfLines={1}>{b.name}</Text>
        <Text style={st.sub} numberOfLines={1}>{note ? `${note} · ` : ''}{b.silent ? `pas de mesure depuis ${dayTxt(b.time)}` : ageTxt(b.time)}</Text>
      </View>
      {perTxt(b) ? <Text style={[st.metaT, b.silent && { opacity: 0.5 }]}>{perTxt(b)}</Text> : null}
      <View style={[st.val, b.silent && { opacity: 0.45 }]}><Text style={st.valT}>{fr(b.hs)}</Text></View>
    </Pressable>
  );
}

/** Onglet Bouées « autour de mon spot » : la bouée de côte la plus utile pour votre spot en grand, les autres bouées
 *  proches avec leur distance, puis toutes les bouées rangées par zone, du nord au sud. */
export function BuoyList({ index, favs, onOpen }: { index: Index; favs: string[]; onOpen: (b: Buoy) => void }) {
  const pad = useBarSpace();
  const spot = favs.map(f => index.spots.find(s => s.slug === f)).find(Boolean);
  const fresh = index.buoys.filter(isLive).length;

  const mine = useMemo(() => {
    if (!spot) return null;
    const all = index.buoys.filter(b => buoyFits(b, spot.name)).map(b => ({ b, k: km(spot, b) })).sort((x, y) => x.k - y.k);
    // bouée de référence : même règle que le site (src/rules.ts), Landes et Sainte-Barbe compris
    const r = refBuoy(index.buoys, spot);
    const main = r || all[0];
    const others = all.filter(x => x.b.id !== main.b.id && x.k < 200).slice(0, 4);
    const off = all.find(x => x.b.large);
    if (off && off.b.id !== main.b.id && !others.some(x => x.b.id === off.b.id)) others.push(off);
    return { main, others };
  }, [index, spot]);

  const zones = useMemo(() => ZONES.map(z => ({ z, list: index.buoys.filter(b => zone(b) === z).sort(z === 'Espagne' ? alongSpain : (a, b) => b.lat - a.lat) })).filter(x => x.list.length), [index]);
  const M = mine?.main;

  return (
    <ScrollView contentContainerStyle={{ paddingBottom: pad }}>
      <View style={{ paddingHorizontal: 20, paddingTop: 14, paddingBottom: 6 }}>
        <Text style={st.h1}>Bouées</Text>
        <Text style={st.lead}>Mesures réelles en mer · {fresh} en direct sur {index.buoys.length}</Text>
      </View>

      {spot && M ? (
        <View>
          <Text style={st.lbl}>Pour {spot.name}</Text>
          <Pressable onPress={() => onOpen(M.b)} style={({ pressed }) => [st.hero, pressed && { opacity: 0.9 }]}>
            <View style={st.heroTop}>
              <Lamp b={M.b} />
              <Text style={st.heroK} numberOfLines={1}>{M.b.large ? 'AU LARGE' : 'À LA CÔTE'} · {M.b.name.toUpperCase()} · {Math.round(M.k)} KM</Text>
            </View>
            <View style={st.heroRow}>
              <Text style={st.heroH}>{fr(M.b.hs)}<Text style={st.heroU}> m</Text></Text>
              <View style={{ gap: 4 }}>
                {perTxt(M.b) ? <Text style={st.heroP}>{perTxt(M.b)}</Text> : null}
                {M.b.dir != null && <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}><Arrow dir={M.b.dir} size={13} color={C.sandText} /><Text style={st.heroS}>{sector(M.b.dir)}</Text></View>}
              </View>
            </View>
            <Text style={st.heroFoot}>Mesuré {ageTxt(M.b.time)}{M.b.sst != null ? ` · eau ${fr(M.b.sst, 0)} °C` : ''}   Voir la bouée ›</Text>
          </Pressable>
          {!!mine!.others.length && (
            <View style={st.group}>
              {mine!.others.map((x, i) => <BuoyLine key={x.b.id} b={x.b} i={i + 1} first={i === 0} note={`${x.b.large ? 'au large' : 'à la côte'} · ${Math.round(x.k)} km`} onOpen={onOpen} />)}
            </View>
          )}
        </View>
      ) : (
        <View style={[st.hero, { gap: 6 }]}>
          <Text style={st.heroK}>VOTRE SPOT</Text>
          <Text style={st.heroEmpty}>Ajoutez un spot en favori (étoile ☆ sur sa fiche) : ses bouées les plus proches s’afficheront ici.</Text>
        </View>
      )}

      <Text style={[st.lbl, { marginTop: 24 }]}>Toutes les bouées</Text>
      {zones.map(({ z, list }) => (
        <View key={z} style={st.group}>
          <Text style={st.zone}>{z}</Text>
          {list.map((b, i) => <BuoyLine key={b.id} b={b} i={i} first={i === 0} note={b.large ? 'au large' : undefined} onOpen={onOpen} />)}
        </View>
      ))}
    </ScrollView>
  );
}

/** Page d'une bouée : relevé actuel, courbe 48 h mesuré / prévu, records, derniers relevés, spots autour. */
export function BuoyPage({ buoy, onBack, onSpot }: { buoy: Buoy; onBack: () => void; onSpot: (slug: string) => void }) {
  const pad = useBarSpace();
  const [d, setD] = useState<BuoySheet | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => { loadBuoy(buoy.slug).then(r => setD(r.data)).catch(() => setErr(true)); }, [buoy.slug]);
  const L = d?.latest, live = !!(d && L && freshOf({ id: d.id, lim: d.lim, time: L.time, silent: d.silent }) === 'live');

  return (
    <View style={{ flex: 1 }}>
      <View style={st.bar}>
        <Pressable onPress={onBack} hitSlop={10} style={st.round} accessibilityLabel="Retour"><Text style={st.roundT}>‹</Text></Pressable>
        <View style={st.pill}><Text style={st.pillT} numberOfLines={1}>Bouée {buoy.name}</Text></View>
      </View>
      {!d ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          {err ? <Text style={st.sub}>Relevés indisponibles. Vérifie la connexion.</Text> : <ActivityIndicator color={C.ink} />}
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ paddingBottom: pad + 10 }}>
          <View style={[st.card, { backgroundColor: C.sandCard }]}>
            <View style={st.nowRow}>
              <View style={[st.lamp, !live && { backgroundColor: C.sandMuted }]} />
              <Text style={st.nowT}>{live ? 'EN DIRECT' : 'DERNIÈRE MESURE'} · {ageTxt(L!.time).toUpperCase()}</Text>
            </View>
            <Text style={st.big}>{fr(L!.hs)}<Text style={st.bigU}> m</Text></Text>
            <Text style={st.bigS}>Hauteur significative mesurée{L!.hmax ? ` · vague max ${fr(L!.hmax)} m` : ''}</Text>
            <View style={st.tiles}>
              <Tile k={!L!.tp && L!.tm ? 'Période moy.' : 'Période'} v={L!.tp ? `${Math.round(L!.tp)} s` : L!.tm ? `${Math.round(L!.tm)} s` : '—'} />
              <Tile k="Direction" v={sector(L!.dir)} dir={L!.dir} />
              <Tile k="Eau" v={L!.sst != null ? `${fr(L!.sst, 1)} °C` : '—'} />
            </View>
            <Text style={st.note}>{d.sub}. Mesure en mer : ce n'est pas la taille des vagues au bord.</Text>
          </View>

          <View style={st.card}>
            <Text style={st.cardT}>48 heures : mesuré et prévu</Text>
            <Chart d={d} />
            <View style={st.legRow}>
              <View style={st.legI}><View style={[st.legL, { backgroundColor: C.ink }]} /><Text style={st.legS}>mesuré</Text></View>
              <View style={st.legI}><View style={[st.legL, { backgroundColor: C.gold }]} /><Text style={st.legS}>prévu ({d.model_src})</Text></View>
            </View>
          </View>

          {d.stats && (
            <View style={st.card}>
              <Text style={st.cardT}>Depuis le {d.stats.since.split('-').reverse().slice(0, 2).join('/')}</Text>
              <View style={st.tiles}>
                <Tile k="Record" v={`${fr(d.stats.hs_max)} m`} s={d.stats.hs_max_t.slice(8, 10) + '/' + d.stats.hs_max_t.slice(5, 7)} light />
                <Tile k="Moyenne" v={`${fr(d.stats.hs_mean)} m`} s={`${d.stats.days} jours`} light />
                {d.stats.sst_mean != null && <Tile k="Eau" v={`${fr(d.stats.sst_mean, 1)} °C`} s="moyenne" light />}
              </View>
            </View>
          )}

          <View style={st.card}>
            <Text style={st.cardT}>Derniers relevés</Text>
            {[...d.obs].reverse().slice(0, 8).map(o => (
              <View key={o.t} style={st.obs}>
                <Text style={st.obsT}>{o.t.slice(8, 10)}/{o.t.slice(5, 7)} · {o.t.slice(11, 16).replace(':', 'h')}</Text>
                <Text style={st.obsV}>{fr(o.hs)} m</Text>
                <Text style={st.obsS}>{o.tp ? `${Math.round(o.tp)} s` : ''}  {sector(o.dir)}</Text>
              </View>
            ))}
          </View>

          {!!d.spots.length && (
            <View style={st.card}>
              <Text style={st.cardT}>Spots autour</Text>
              <View style={st.spots}>
                {d.spots.map(s => (
                  <Pressable key={s.slug} onPress={() => onSpot(s.slug)} style={st.spot}><Text style={st.spotT}>{s.name}</Text><Text style={st.spotS}>{s.km} km</Text></Pressable>
                ))}
              </View>
            </View>
          )}
        </ScrollView>
      )}
    </View>
  );
}

function Tile({ k, v, s, dir, light }: { k: string; v: string; s?: string; dir?: number | null; light?: boolean }) {
  return (
    <View style={[st.tile, light && { backgroundColor: C.soft }]}>
      <Text style={st.tileK}>{k.toUpperCase()}</Text>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 3 }}>{dir != null && <Arrow dir={dir} size={12} />}<Text style={st.tileV}>{v}</Text></View>
      {s ? <Text style={st.tileS}>{s}</Text> : null}
    </View>
  );
}

/** Courbe : trait plein = mesure de la bouée, tirets dorés = prévision au même endroit, trait vertical = maintenant. */
function Chart({ d }: { d: BuoySheet }) {
  const W = 330, H = 150, P = { l: 26, r: 8, t: 10, b: 20 };
  const ts = (t: string) => tMs(t);   // instants exacts (issue #2)
  const obs = d.obs.filter(o => o.hs != null), mod = d.model.filter(m => m.hs != null);
  if (obs.length < 2) return <Text style={st.legS}>Pas assez de relevés récents.</Text>;
  const t0 = ts(obs[0].t), t1 = Math.max(ts(obs[obs.length - 1].t), mod.length ? ts(mod[mod.length - 1].t) : 0);
  const hmax = Math.max(1, ...obs.map(o => o.hs!), ...mod.map(m => m.hs!)) * 1.15;
  const X = (t: number) => P.l + ((t - t0) / Math.max(1, t1 - t0)) * (W - P.l - P.r), Y = (h: number) => H - P.b - (h / hmax) * (H - P.t - P.b);
  const line = (pts: { t: string; hs: number | null }[]) => pts.map((p, i) => `${i ? 'L' : 'M'}${X(ts(p.t)).toFixed(1)},${Y(p.hs!).toFixed(1)}`).join(' ');
  const now = X(Date.now()), ticks = [0, hmax / 2, hmax].map(v => Math.round(v * 2) / 2);
  return (
    <Svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ marginTop: 10 }}>
      {ticks.map(v => <Line key={v} x1={P.l} x2={W - P.r} y1={Y(v)} y2={Y(v)} stroke={C.line} strokeWidth={1} />)}
      {ticks.map(v => <SvgText key={'t' + v} x={2} y={Y(v) + 4} fontSize={10} fontFamily={F.tB} fill={C.ink3}>{fr(v)}</SvgText>)}
      {now > P.l && now < W - P.r && <Line x1={now} x2={now} y1={P.t} y2={H - P.b} stroke={C.ink3} strokeDasharray="2,4" />}
      {mod.length > 1 && <Path d={line(mod)} stroke={C.gold} strokeWidth={2} strokeDasharray="5,4" fill="none" />}
      <Path d={line(obs)} stroke={C.ink} strokeWidth={2.4} fill="none" strokeLinejoin="round" />
      <Circle cx={X(ts(obs[obs.length - 1].t))} cy={Y(obs[obs.length - 1].hs!)} r={4} fill={C.ink} />
      <SvgText x={P.l} y={H - 4} fontSize={10} fontFamily={F.tB} fill={C.ink3}>{obs[0].t.slice(8, 10)}/{obs[0].t.slice(5, 7)} {obs[0].t.slice(11, 13)}h</SvgText>
      <SvgText x={Math.min(now, W - 40)} y={H - 4} fontSize={10} fontFamily={F.tB} fill={C.ink3}>maintenant</SvgText>
    </Svg>
  );
}

const st = themed(() => StyleSheet.create({
  lbl: { fontFamily: F.tX, fontSize: 11.5, letterSpacing: 1.3, textTransform: 'uppercase', color: C.gold, marginHorizontal: 20, marginTop: 14, marginBottom: 10 },
  hero: { marginHorizontal: 16, borderRadius: 26, padding: 18, backgroundColor: C.sandCard },
  heroTop: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  heroK: { flex: 1, fontFamily: F.tX, fontSize: 10.5, letterSpacing: 1.2, color: C.sandMuted },
  heroEmpty: { fontFamily: F.t, fontSize: 14.5, lineHeight: 20, color: C.sandText },
  heroRow: { flexDirection: 'row', alignItems: 'center', gap: 14, marginTop: 8 },
  heroH: { fontFamily: F.numX, fontSize: 52, color: C.sandText, letterSpacing: -2.5 },
  heroU: { fontFamily: F.num, fontSize: 20, letterSpacing: 0 },
  heroP: { fontFamily: F.num, fontSize: 17, color: C.sandText },
  heroS: { fontFamily: F.tX, fontSize: 13, color: C.sandText },
  heroFoot: { fontFamily: F.tB, fontSize: 12, color: C.sandMuted2, marginTop: 8 },
  group: { marginHorizontal: 16, marginTop: 10, paddingHorizontal: 16, borderRadius: 22, backgroundColor: C.card },
  zone: { fontFamily: F.num, fontSize: 14, color: C.ink, paddingTop: 14, paddingBottom: 2 },
  line: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12 },
  sep: { borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: C.line },
  h1: { fontFamily: F.numX, fontSize: 28, color: C.ink, letterSpacing: -1 },
  lead: { fontFamily: F.t, fontSize: 14, color: C.ink2, marginTop: 4 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, marginHorizontal: 16, marginBottom: 8, padding: 14, borderRadius: 20, backgroundColor: C.card },
  lamp: { width: 9, height: 9, borderRadius: 5, backgroundColor: C.live },
  name: { fontFamily: F.tX, fontSize: 16, color: C.ink },
  sub: { fontFamily: F.t, fontSize: 12.5, color: C.ink2, marginTop: 2 },
  val: { height: 36, minWidth: 54, paddingHorizontal: 12, borderRadius: 18, backgroundColor: C.pill, alignItems: 'center', justifyContent: 'center' },
  valT: { fontFamily: F.num, fontSize: 16, color: C.sandText, letterSpacing: -0.5 },
  meta: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  metaT: { fontFamily: F.tB, fontSize: 11.5, color: C.ink2 },
  bar: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 16, paddingVertical: 8 },
  round: { width: 40, height: 40, borderRadius: 20, backgroundColor: C.card, alignItems: 'center', justifyContent: 'center' },
  roundT: { fontFamily: F.tX, fontSize: 24, color: C.ink, marginTop: -2 },
  pill: { flex: 1, height: 40, borderRadius: 20, backgroundColor: C.card, justifyContent: 'center', paddingHorizontal: 16 },
  pillT: { fontFamily: F.num, fontSize: 15, color: C.ink, letterSpacing: -0.4 },
  card: { marginHorizontal: 12, marginTop: 10, padding: 16, borderRadius: 24, backgroundColor: C.card },
  nowRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  nowT: { fontFamily: F.tX, fontSize: 11.5, letterSpacing: 1, color: C.sandText },
  big: { fontFamily: F.numX, fontSize: 56, color: C.sandText, letterSpacing: -2, marginTop: 6 },
  bigU: { fontFamily: F.tB, fontSize: 18, letterSpacing: 0 },
  bigS: { fontFamily: F.tB, fontSize: 12.5, color: C.sandMuted2 },
  tiles: { flexDirection: 'row', gap: 8, marginTop: 12 },
  tile: { flex: 1, backgroundColor: C.glass, borderRadius: 16, padding: 10 },
  tileK: { fontFamily: F.tX, fontSize: 9.5, letterSpacing: 0.9, color: C.ink2 },
  tileV: { fontFamily: F.num, fontSize: 15, color: C.ink, letterSpacing: -0.4 },
  tileS: { fontFamily: F.tB, fontSize: 11, color: C.ink2, marginTop: 2 },
  note: { fontFamily: F.t, fontSize: 12, color: C.sandMuted2, marginTop: 10 },
  cardT: { fontFamily: F.num, fontSize: 16, color: C.ink, letterSpacing: -0.3 },
  legRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 14, marginTop: 6 },
  legI: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  legL: { width: 16, height: 3, borderRadius: 2 },
  legS: { fontFamily: F.tB, fontSize: 11.5, color: C.ink2 },
  obs: { flexDirection: 'row', alignItems: 'center', paddingVertical: 9, borderTopWidth: 1, borderTopColor: C.line, gap: 10 },
  obsT: { flex: 1, fontFamily: F.tB, fontSize: 13, color: C.ink2 },
  obsV: { fontFamily: F.num, fontSize: 14, color: C.ink, width: 64, textAlign: 'right' },
  obsS: { fontFamily: F.tB, fontSize: 12, color: C.ink2, width: 74, textAlign: 'right' },
  spots: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
  spot: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 36, paddingHorizontal: 14, borderRadius: 18, backgroundColor: C.soft },
  spotT: { fontFamily: F.tB, fontSize: 13, color: C.ink },
  spotS: { fontFamily: F.tB, fontSize: 11.5, color: C.ink3 },
}));
