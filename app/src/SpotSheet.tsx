import { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, G, Line, Path, Text as SvgText } from 'react-native-svg';
import Arrow from './Arrow';
import { ageTxt, Buoy, fr, isLive, loadSheet, perTxt, refBuoy, regionName, sector, Sheet, SpotLite, windCat, windText } from './data';
import { partsIn, placeTz, tMs } from './time';
import { useReloaded } from './useReloaded';
import { useBarSpace } from './TabBar';
import { C, F, isDark, periodCell, sizeCell, themed, windCell } from './theme';

type Props = { spot: SpotLite; buoys: Buoy[]; fav: boolean; onFav: () => void; onBack: () => void; onBuoy?: (b: Buoy) => void };
const J = ['DIM', 'LUN', 'MAR', 'MER', 'JEU', 'VEN', 'SAM'];
const COL = 50;   // largeur d'une colonne de la frise horaire


export default function SpotSheet({ spot, buoys, fav, onFav, onBack, onBuoy }: Props) {
  const pad = useBarSpace();
  const { data: sheet, offline, err } = useReloaded<Sheet>(loadSheet, spot.slug);   // redemandée au retour (reprise réseau)
  const [day, setDay] = useState(0);
  const [hour, setHour] = useState<number | null>(null);
  const strip = useRef<{ scrollTo: (o: { x: number; animated?: boolean }) => void } | null>(null);


  const days = useMemo(() => {
    if (!sheet) return [];
    const out: { date: string; idx: number[] }[] = [];
    const t0 = tMs(sheet.t0), tz = placeTz(sheet);   // jours à l'heure du spot (Lisbonne au Portugal), pas du téléphone
    sheet.hs.forEach((_, i) => {
      const key = partsIn(t0 + i * 36e5, tz).date;
      if (!out.length || out[out.length - 1].date !== key) out.push({ date: key, idx: [] });
      out[out.length - 1].idx.push(i);
    });
    return out.slice(0, 7);
  }, [sheet]);

  if (err) return <Center onBack={onBack} name={spot.name} text="Fiche indisponible. Vérifie la connexion." />;
  if (!sheet || !days.length) return <Center onBack={onBack} name={spot.name} loading />;

  const t0 = tMs(sheet.t0), tz = placeTz(sheet);
  const at = (i: number) => partsIn(t0 + i * 36e5, tz);   // heure du spot (issue #2)
  const nowI = Math.max(0, Math.min(sheet.hs.length - 1, Math.floor((Date.now() - t0) / 36e5)));
  const d = days[day];
  const hrs = d.idx.filter(i => { const h = at(i).h; return h >= 6 && h <= 21; });
  const def = day === 0 ? (hrs.find(i => i >= nowI) ?? hrs[hrs.length - 1]) : (hrs.find(i => at(i).h >= 10) ?? hrs[0]);
  const sel = hour != null && d.idx.includes(hour) ? hour : def;
  const isNow = day === 0 && sel === nowI;
  const rel = windText(windCat(sheet.wind[sel], sheet.wdir[sel], sheet.ori));   // mêmes catégories et seuils que le site
  const tides = (sheet.tide?.extremes || []).filter(e => partsIn(tMs(e.t), tz).date === d.date);
  const sunI = sheet.sun ? sheet.sun.time.findIndex(x => x === d.date) : -1;   // dates locales du spot
  // Bouée de comparaison : même règle que le site (src/rules.ts : Landes, Sainte-Barbe, en direct selon la cadence, 6 h, la plus fraîche)
  const near = refBuoy(buoys, spot);
  const sea = d.idx.map(i => sheet.sea[i]);

  return (
    <View style={{ flex: 1 }}>
      <View style={st.bar}>
        <Pressable onPress={onBack} hitSlop={10} style={st.round} accessibilityLabel="Retour à la liste"><Text style={st.roundT}>‹</Text></Pressable>
        <View style={st.spotPill}><Text style={st.spotPillT} numberOfLines={1}>{sheet.name}</Text></View>
        <Pressable onPress={onFav} hitSlop={10} style={[st.round, fav && { backgroundColor: isDark() ? C.sandCard : C.ink }]} accessibilityLabel={fav ? 'Retirer des favoris' : 'Ajouter aux favoris'}>
          <Text style={[st.roundT, { fontSize: 17 }, fav && { color: C.sand }]}>{fav ? '★' : '☆'}</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={{ paddingBottom: pad + 20 }}>
        {offline && <Text style={st.off}>hors connexion · dernière version reçue</Text>}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.days}>
          {days.map((x, i) => {
            const dd = at(x.idx[0]), mx = Math.max(...x.idx.map(j => sheet.hs[j] ?? 0)), on = i === day;
            return (
              <Pressable key={x.date} onPress={() => { setDay(i); setHour(null); strip.current?.scrollTo({ x: 0, animated: false }); }} style={[st.day, on && st.dayOn]}>
                <Text style={[st.dayJ, on && { color: C.onInk2 }]}>{i === 0 ? 'AUJ.' : J[dd.wd]}</Text>
                <Text style={[st.dayN, on && { color: C.onInk }]}>{dd.d}</Text>
                <Text style={[st.dayH, on && { color: C.onInk }]}>{fr(mx)}<Text style={st.dayU}> m</Text></Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <View style={st.card}>
          <View style={st.nowRow}>
            <View style={[st.dot, !isNow && { backgroundColor: C.ink3 }]} />
            <Text style={st.nowT}>{isNow ? 'MAINTENANT' : day === 0 ? "AUJOURD'HUI" : J[at(sel).wd]} · {at(sel).h} H</Text>
          </View>
          <View style={st.tiles}>
            <View style={st.tile}>
              <Text style={st.tileK}>HOULE</Text>
              <Text style={st.big}>{fr(sheet.hs[sel])}<Text style={st.bigU}> m</Text></Text>
              <View style={st.tileRow}><Text style={st.tileS}>{fr(sheet.tp[sel], 0)} s</Text><Arrow dir={sheet.dir[sel]} size={9} color={C.ink2} /><Text style={st.tileS}>{sector(sheet.dir[sel])}</Text></View>
            </View>
            <View style={st.tile}>
              <Text style={st.tileK}>VENT</Text>
              <Text style={st.big}>{fr(sheet.wind[sel], 0)}<Text style={st.bigU}> km/h</Text></Text>
              <View style={st.tileRow}><Arrow dir={sheet.wdir[sel]} size={9} color={C.ink2} /><Text style={st.tileS}>{sheet.gust[sel] != null ? `raf. ${fr(sheet.gust[sel], 0)}` : sector(sheet.wdir[sel])}</Text></View>
            </View>
            <View style={[st.tile, { backgroundColor: C.water }]}>
              <Text style={[st.tileK, { color: C.waterK }]}>EAU</Text>
              <Text style={[st.big, { color: C.waterT }]}>{fr(sheet.sst[sel], 0)}<Text style={st.bigU}> °C</Text></Text>
              <Text style={[st.tileS, { color: C.waterK }]}>{waterRange(sheet.sst)}</Text>
            </View>
            <SunTile sun={sunI >= 0 && sheet.sun ? { rise: sheet.sun.sunrise[sunI], set: sheet.sun.sunset[sunI] } : null} today={day === 0} />
          </View>
          {rel && <Text style={st.rel}>{rel}</Text>}

          <ScrollView ref={strip as never} horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.grid}
            onContentSizeChange={() => { const k = hrs.indexOf(sel); if (k > 2) strip.current?.scrollTo({ x: (k - 2) * (COL + 4), animated: false }); }}>
            <View style={st.labels}>
              <Text style={[st.lab, { height: 26 }]} />
              <Text style={[st.lab, { height: 46 }]}>m</Text>
              <Text style={[st.lab, { height: 36 }]}>s</Text>
              <Text style={[st.lab, { height: 40 }]}>km/h</Text>
              <Text style={[st.lab, { height: TIDE_H }]}>marée</Text>
            </View>
            <View>
            <View style={{ flexDirection: 'row', gap: 4 }}>
            {hrs.map(i => {
              const on = i === sel, h = at(i).h;
              return (
                <Pressable key={i} onPress={() => setHour(i)} style={st.col}>
                  <Text style={[st.hh, on && { color: C.ink }]}>{h}h</Text>
                  <View style={[st.cell, { height: 46, backgroundColor: sizeCell(sheet.hs[i]) }, on && st.cellOn]}><Text style={st.cellBig}>{fr(sheet.hs[i])}</Text></View>
                  <View style={[st.cell, { height: 36, backgroundColor: periodCell(sheet.tp[i]) }, on && st.cellOn]}>
                    <Text style={st.cellMid}>{fr(sheet.tp[i], 0)} s</Text>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 2 }}><Arrow dir={sheet.dir[i]} size={8} /><Text style={st.cellSm}>{sector(sheet.dir[i])}</Text></View>
                  </View>
                  <View style={[st.cell, { height: 40, backgroundColor: windCell(sheet.wind[i]) }, on && st.cellOn]}>
                    <Arrow dir={sheet.wdir[i]} size={12} />
                    <Text style={st.cellMid}>{fr(sheet.wind[i], 0)}</Text>
                  </View>
                </Pressable>
              );
            })}
            </View>
            <TideRow sheet={sheet} hrs={hrs} sel={sel} t0={t0} />
            </View>
          </ScrollView>
          {sheet.tide ? <Text style={st.port}>Marée : {sheet.tide.label}</Text> : <Text style={st.port}>Marée indicative (modèle)</Text>}
        </View>

        {near && (
          <Pressable onPress={() => onBuoy?.(near.b)} style={({ pressed }) => [st.card, { backgroundColor: C.sandCard }, pressed && { opacity: 0.85 }]}>
            <View style={st.nowRow}><View style={[st.dot, !isLive(near.b) && { backgroundColor: C.sandMuted }]} /><Text style={[st.nowT, { color: C.sandText }]}>MESURE RÉELLE · BOUÉE {near.b.name.toUpperCase()}</Text></View>
            <View style={{ flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 8 }}>
              <Text style={[st.big, { color: C.sandText }]}>{fr(near.b.hs)}<Text style={st.bigU}> m</Text></Text>
              <Text style={[st.tileS, { color: C.sandText, marginBottom: 8 }]}>{perTxt(near.b) ? `${perTxt(near.b)} · ` : ''}{near.b.dir != null ? sector(near.b.dir) + ' · ' : ''}{Math.round(near.k)} km</Text>
            </View>
            <Text style={[st.hint, { color: C.sandMuted2 }]}>Mesuré {ageTxt(near.b.time)}, en mer : à comparer à la prévision. Voir la bouée ›</Text>
          </Pressable>
        )}
      </ScrollView>
    </View>
  );
}

const TIDE_H = 56;

/** Fourchette de température de l'eau sur les 7 jours. */
function waterRange(w: (number | null)[]) {
  const v = w.filter((x): x is number => x != null);
  return v.length > 1 ? `${fr(Math.min(...v), 0)} à ${fr(Math.max(...v), 0)}` : '';
}

/** Petit carré Soleil : arc avec la position du soleil (aujourd'hui), lever et coucher. */
function SunTile({ sun, today }: { sun: { rise: string; set: string } | null; today: boolean }) {
  if (!sun) return <View style={[st.tile, { backgroundColor: C.sunTile }]} />;
  const rise = tMs(sun.rise), set = tMs(sun.set);
  const f = today ? (Date.now() - rise) / (set - rise) : null;
  const up = f != null && f >= 0 && f <= 1;
  const R = 24, cx = 30, cy = 27, a = Math.PI * (1 - (up ? f! : 0));
  const sx = cx + R * Math.cos(a), sy = cy - R * Math.sin(a);
  const t = (s: string) => `${+s.slice(11, 13)}h${s.slice(14, 16)}`;   // heure locale du spot, écrite dans la chaîne
  return (
    <View style={[st.tile, { backgroundColor: C.sunTile }]}>
      <Text style={[st.tileK, { color: C.sandMuted }]}>SOLEIL</Text>
      <Svg width="100%" height={30} viewBox="0 0 60 30" style={{ marginTop: 2 }}>
        <Path d={`M${cx - R} ${cy} A${R} ${R} 0 0 1 ${cx + R} ${cy}`} stroke="#c9a463" strokeWidth={1.3} strokeDasharray="2 3" fill="none" />
        {up && <Path d={`M${cx - R} ${cy} A${R} ${R} 0 0 1 ${sx.toFixed(1)} ${sy.toFixed(1)}`} stroke="#b8892f" strokeWidth={2} fill="none" strokeLinecap="round" />}
        {up && <Circle cx={sx} cy={sy} r={4} fill="#f2b632" stroke="#fff" strokeWidth={1.5} />}
      </Svg>
      <Text style={[st.tileS, { color: C.sandMuted }]} numberOfLines={1} adjustsFontSizeToFit>{t(sun.rise)} · {t(sun.set)}</Text>
    </View>
  );
}

/** Dernière ligne de la frise : la courbe de marée, alignée sur les colonnes, avec PM et BM posées à leur heure exacte. */
function TideRow({ sheet, hrs, sel, t0 }: { sheet: Sheet; hrs: number[]; sel: number; t0: number }) {
  const W = hrs.length * (COL + 4) - 4, a = hrs[0], b = hrs[hrs.length - 1];
  const x = (f: number) => (f - a) * (COL + 4) + COL / 2;
  const at = (f: number) => {   // hauteur d'eau à une heure fractionnaire (interpolation entre deux heures)
    const i = Math.floor(f), u = f - i, p = sheet.sea[i], q = sheet.sea[i + 1];
    return p == null ? null : q == null ? p : p + (q - p) * u;
  };
  const pts: [number, number][] = [];
  for (let f = a - 0.5; f <= b + 0.5001; f += 0.25) { const v = at(f); if (v != null) pts.push([f, v]); }
  if (pts.length < 4) return <View style={{ height: TIDE_H, marginTop: 4 }} />;
  const vs = pts.map(p => p[1]), mn = Math.min(...vs), mx = Math.max(...vs);
  const y = (v: number) => 8 + (1 - (v - mn) / Math.max(0.01, mx - mn)) * (TIDE_H - 16);
  const d = pts.map(([f, v], k) => `${k ? 'L' : 'M'}${x(f).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const ext = (sheet.tide?.extremes || []).map(e => ({ ...e, f: (tMs(e.t) - t0) / 36e5 })).filter(e => e.f >= a - 0.5 && e.f <= b + 0.5);
  return (
    <Svg width={W} height={TIDE_H} style={{ marginTop: 4 }}>
      <Path d={`${d} L${x(pts[pts.length - 1][0]).toFixed(1)},${TIDE_H} L${x(pts[0][0]).toFixed(1)},${TIDE_H} Z`} fill={C.tideFill} />
      <Path d={d} stroke={C.ink} strokeWidth={1.4} fill="none" />
      <Line x1={x(sel)} y1={0} x2={x(sel)} y2={TIDE_H} stroke={C.ink} strokeWidth={1} strokeDasharray="2 3" />
      {ext.map(e => {
        const v = at(e.f) ?? e.h, cy = y(v), pm = e.type === 'PM';
        const lab = `${e.type} ${+e.t.slice(11, 13)}h${e.t.slice(14, 16)}`;
        const tx = Math.min(W - 30, Math.max(30, x(e.f)));
        return (
          <G key={e.t}>
            <Circle cx={x(e.f)} cy={cy} r={3.2} fill={C.ink} />
            <SvgText x={tx} y={pm ? cy + 16 : cy - 8} fontSize={11} fontFamily={F.tX} fill={C.ink} textAnchor="middle">{lab}</SvgText>
          </G>
        );
      })}
    </Svg>
  );
}

function Center({ onBack, name, loading, text }: { onBack: () => void; name: string; loading?: boolean; text?: string }) {
  return (
    <View style={{ flex: 1 }}>
      <View style={st.bar}>
        <Pressable onPress={onBack} hitSlop={10} style={st.round}><Text style={st.roundT}>‹</Text></Pressable>
        <View style={st.spotPill}><Text style={st.spotPillT} numberOfLines={1}>{name}</Text></View>
        <View style={{ width: 40 }} />
      </View>
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30 }}>
        {loading ? <ActivityIndicator color={C.ink} /> : <Text style={{ color: C.ink2, textAlign: 'center', fontFamily: F.t }}>{text}</Text>}
      </View>
    </View>
  );
}

const st = themed(() => StyleSheet.create({
  off: { fontFamily: F.tB, fontSize: 12, color: C.coral, marginHorizontal: 16, marginTop: 8 },   // même style que « hors connexion » de l'accueil
  bar: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 16, paddingVertical: 8 },
  round: { width: 40, height: 40, borderRadius: 20, backgroundColor: C.card, alignItems: 'center', justifyContent: 'center' },
  roundT: { fontFamily: F.tX, fontSize: 24, color: C.ink, marginTop: -2 },
  spotPill: { flex: 1, height: 40, borderRadius: 20, backgroundColor: C.card, justifyContent: 'center', paddingHorizontal: 16 },
  spotPillT: { fontFamily: F.num, fontSize: 15, color: C.ink, letterSpacing: -0.4 },
  days: { paddingHorizontal: 16, paddingVertical: 8, gap: 8 },
  day: { width: 64, paddingVertical: 10, borderRadius: 18, alignItems: 'center', backgroundColor: C.card },
  dayOn: { backgroundColor: C.ink },
  dayJ: { fontFamily: F.tX, fontSize: 10.5, letterSpacing: 0.8, color: C.ink3 },
  dayN: { fontFamily: F.numX, fontSize: 22, color: C.ink, marginTop: 1 },
  dayH: { fontFamily: F.tX, fontSize: 12, color: C.ink2, marginTop: 2 },
  dayU: { fontFamily: F.tB, fontSize: 10 },
  card: { marginHorizontal: 12, marginTop: 10, padding: 14, borderRadius: 24, backgroundColor: C.card },
  nowRow: { flexDirection: 'row', alignItems: 'center', gap: 7, flexWrap: 'wrap' },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: C.live },
  nowT: { fontFamily: F.tX, fontSize: 11.5, letterSpacing: 1, color: C.ink, marginRight: 4 },
  nowS: { fontFamily: F.tB, fontSize: 12, color: C.ink2 },
  tiles: { flexDirection: 'row', gap: 6, marginTop: 12 },
  tile: { flex: 1, minWidth: 0, backgroundColor: C.soft, borderRadius: 14, paddingVertical: 8, paddingHorizontal: 8 },
  tileK: { fontFamily: F.tX, fontSize: 9.5, letterSpacing: 0.9, color: C.ink2 },
  big: { fontFamily: F.numX, fontSize: 19, color: C.ink, letterSpacing: -0.8, marginTop: 3 },
  bigU: { fontFamily: F.tB, fontSize: 10.5, letterSpacing: 0 },
  tileRow: { flexDirection: 'row', alignItems: 'center', gap: 3, marginTop: 3 },
  tileS: { fontFamily: F.tB, fontSize: 10.5, color: C.ink2 },
  rel: { fontFamily: F.tB, fontSize: 12, color: C.ink2, marginTop: 8 },
  port: { fontFamily: F.t, fontSize: 11.5, color: C.ink3, marginTop: 6 },
  grid: { paddingTop: 14, gap: 4, paddingRight: 4 },
  labels: { width: 30, gap: 4 },
  lab: { fontFamily: F.tB, fontSize: 10, color: C.ink3, textAlignVertical: 'center', paddingTop: 22 },
  col: { width: COL, gap: 4, alignItems: 'stretch' },
  hh: { fontFamily: F.tX, fontSize: 12, color: C.ink2, textAlign: 'center', height: 26, lineHeight: 26 },
  cell: { borderRadius: 10, alignItems: 'center', justifyContent: 'center', gap: 2 },
  cellOn: { borderWidth: 2, borderColor: C.ink },
  cellBig: { fontFamily: F.num, fontSize: 16, color: C.ink, letterSpacing: -0.8 },
  cellMid: { fontFamily: F.tX, fontSize: 12.5, color: C.ink },
  cellSm: { fontFamily: F.tB, fontSize: 9, color: C.cellU },
  cardT: { fontFamily: F.num, fontSize: 16, color: C.ink, letterSpacing: -0.3 },
  cardS: { fontFamily: F.tB, fontSize: 13, color: C.ink2, letterSpacing: 0 },
  tides: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
  tide: { flexGrow: 1, flexBasis: '45%', flexDirection: 'row', alignItems: 'baseline', gap: 8, backgroundColor: C.soft, borderRadius: 16, paddingVertical: 10, paddingHorizontal: 12 },
  tideK: { fontFamily: F.tX, fontSize: 9.5, letterSpacing: 0.8, color: C.ink2 },
  tideV: { fontFamily: F.num, fontSize: 15, color: C.ink, letterSpacing: -0.5 },
  tideS: { fontFamily: F.tB, fontSize: 11.5, color: C.ink2 },
  hint: { fontFamily: F.t, fontSize: 12.5, color: C.ink2, marginTop: 8 },
}));
