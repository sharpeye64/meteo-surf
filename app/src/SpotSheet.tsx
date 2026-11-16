import { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';
import Arrow from './Arrow';
import { ageTxt, Buoy, buoyFits, fr, loadSheet, regionName, sector, Sheet, SpotLite, windRel } from './data';
import { useBarSpace } from './TabBar';
import { C, F, periodCell, sizeCell, windCell } from './theme';

type Props = { spot: SpotLite; buoys: Buoy[]; fav: boolean; onFav: () => void; onBack: () => void; onBuoy?: (b: Buoy) => void };
const J = ['DIM', 'LUN', 'MAR', 'MER', 'JEU', 'VEN', 'SAM'];
const COL = 50;   // largeur d'une colonne de la frise horaire

const km = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => {
  const r = Math.PI / 180, x = (b.lon - a.lon) * r * Math.cos(((a.lat + b.lat) / 2) * r), y = (b.lat - a.lat) * r;
  return Math.sqrt(x * x + y * y) * 6371;
};

export default function SpotSheet({ spot, buoys, fav, onFav, onBack, onBuoy }: Props) {
  const pad = useBarSpace();
  const [sheet, setSheet] = useState<Sheet | null>(null);
  const [err, setErr] = useState(false);
  const [day, setDay] = useState(0);
  const [hour, setHour] = useState<number | null>(null);
  const strip = useRef<{ scrollTo: (o: { x: number; animated?: boolean }) => void } | null>(null);

  useEffect(() => { loadSheet(spot.slug).then(r => setSheet(r.data)).catch(() => setErr(true)); }, [spot.slug]);

  const days = useMemo(() => {
    if (!sheet) return [];
    const out: { date: string; idx: number[] }[] = [];
    const t0 = new Date(sheet.t0 + ':00').getTime();
    sheet.hs.forEach((_, i) => {
      const key = new Date(t0 + i * 36e5).toDateString();
      if (!out.length || out[out.length - 1].date !== key) out.push({ date: key, idx: [] });
      out[out.length - 1].idx.push(i);
    });
    return out.slice(0, 7);
  }, [sheet]);

  if (err) return <Center onBack={onBack} name={spot.name} text="Fiche indisponible. Vérifie la connexion." />;
  if (!sheet || !days.length) return <Center onBack={onBack} name={spot.name} loading />;

  const t0 = new Date(sheet.t0 + ':00').getTime();
  const at = (i: number) => new Date(t0 + i * 36e5);
  const nowI = Math.max(0, Math.min(sheet.hs.length - 1, Math.floor((Date.now() - t0) / 36e5)));
  const d = days[day];
  const hrs = d.idx.filter(i => { const h = at(i).getHours(); return h >= 6 && h <= 21; });
  const def = day === 0 ? (hrs.find(i => i >= nowI) ?? hrs[hrs.length - 1]) : (hrs.find(i => at(i).getHours() >= 10) ?? hrs[0]);
  const sel = hour != null && d.idx.includes(hour) ? hour : def;
  const isNow = day === 0 && sel === nowI;
  const rel = windRel(sheet.wdir[sel], sheet.ori);
  const tides = (sheet.tide?.extremes || []).filter(e => new Date(e.t + ':00').toDateString() === d.date);
  const sunI = sheet.sun ? sheet.sun.time.findIndex(x => new Date(x + 'T12:00').toDateString() === d.date) : -1;
  const near = buoys.filter(b => buoyFits(b, spot.name)).map(b => ({ b, k: km(spot, b) })).filter(x => x.k < 130).sort((a, b) => a.k - b.k)[0];
  const sea = d.idx.map(i => sheet.sea[i]);

  return (
    <View style={{ flex: 1 }}>
      <View style={st.bar}>
        <Pressable onPress={onBack} hitSlop={10} style={st.round} accessibilityLabel="Retour à la liste"><Text style={st.roundT}>‹</Text></Pressable>
        <View style={st.spotPill}><Text style={st.spotPillT} numberOfLines={1}>{sheet.name}</Text></View>
        <Pressable onPress={onFav} hitSlop={10} style={[st.round, fav && { backgroundColor: C.ink }]} accessibilityLabel={fav ? 'Retirer des favoris' : 'Ajouter aux favoris'}>
          <Text style={[st.roundT, { fontSize: 17 }, fav && { color: C.sand }]}>{fav ? '★' : '☆'}</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={{ paddingBottom: pad + 20 }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.days}>
          {days.map((x, i) => {
            const dd = at(x.idx[0]), mx = Math.max(...x.idx.map(j => sheet.hs[j] ?? 0)), on = i === day;
            return (
              <Pressable key={x.date} onPress={() => { setDay(i); setHour(null); strip.current?.scrollTo({ x: 0, animated: false }); }} style={[st.day, on && st.dayOn]}>
                <Text style={[st.dayJ, on && { color: 'rgba(255,255,255,0.7)' }]}>{i === 0 ? 'AUJ.' : J[dd.getDay()]}</Text>
                <Text style={[st.dayN, on && { color: '#fff' }]}>{dd.getDate()}</Text>
                <Text style={[st.dayH, on && { color: '#fff' }]}>{fr(mx)}<Text style={st.dayU}> m</Text></Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <View style={st.card}>
          <View style={st.nowRow}>
            <View style={[st.dot, !isNow && { backgroundColor: C.ink3 }]} />
            <Text style={st.nowT}>{isNow ? 'MAINTENANT' : day === 0 ? "AUJOURD'HUI" : J[at(sel).getDay()]} · {at(sel).getHours()} H</Text>
          </View>
          <View style={st.tiles}>
            <View style={st.tile}>
              <Text style={st.tileK}>≈  HOULE</Text>
              <Text style={st.big}>{fr(sheet.hs[sel])}<Text style={st.bigU}> m</Text></Text>
              <View style={st.tileRow}>
                <Text style={st.tileS}>{fr(sheet.tp[sel], 0)} s</Text>
                <View style={st.badge}><Arrow dir={sheet.dir[sel]} size={11} /><Text style={st.badgeT}>{sector(sheet.dir[sel])}</Text></View>
              </View>
            </View>
            <View style={st.tile}>
              <Text style={st.tileK}>〜  VENT</Text>
              <Text style={st.big}>{fr(sheet.wind[sel], 0)}<Text style={st.bigU}> km/h</Text></Text>
              <View style={st.tileRow}>
                <View style={[st.badge, { backgroundColor: windCell(sheet.wind[sel]) }]}><Arrow dir={sheet.wdir[sel]} size={11} /><Text style={st.badgeT}>{sector(sheet.wdir[sel])}</Text></View>
                {rel && <Text style={st.tileS}>{rel}</Text>}
              </View>
              {sheet.gust[sel] != null && <Text style={st.gustT}>rafales <Text style={{ fontFamily: F.tX, color: C.ink }}>{fr(sheet.gust[sel], 0)}</Text> km/h</Text>}
            </View>
          </View>

          <ScrollView ref={strip as never} horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.grid}
            onContentSizeChange={() => { const k = hrs.indexOf(sel); if (k > 2) strip.current?.scrollTo({ x: (k - 2) * (COL + 4), animated: false }); }}>
            <View style={st.labels}>
              <Text style={[st.lab, { height: 30 }]} />
              <Text style={[st.lab, { height: 66 }]}>m</Text>
              <Text style={[st.lab, { height: 46 }]}>s</Text>
              <Text style={[st.lab, { height: 52 }]}>km/h</Text>
            </View>
            {hrs.map(i => {
              const on = i === sel, h = at(i).getHours();
              return (
                <Pressable key={i} onPress={() => setHour(i)} style={st.col}>
                  <Text style={[st.hh, on && { color: C.ink }]}>{h}h</Text>
                  <View style={[st.cell, { height: 62, backgroundColor: sizeCell(sheet.hs[i]) }, on && st.cellOn]}><Text style={st.cellBig}>{fr(sheet.hs[i])}</Text></View>
                  <View style={[st.cell, { height: 42, backgroundColor: periodCell(sheet.tp[i]) }, on && st.cellOn]}>
                    <Text style={st.cellMid}>{fr(sheet.tp[i], 0)} s</Text>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 2 }}><Arrow dir={sheet.dir[i]} size={8} /><Text style={st.cellSm}>{sector(sheet.dir[i])}</Text></View>
                  </View>
                  <View style={[st.cell, { height: 48, backgroundColor: windCell(sheet.wind[i]) }, on && st.cellOn]}>
                    <Arrow dir={sheet.wdir[i]} size={14} />
                    <Text style={st.cellMid}>{fr(sheet.wind[i], 0)}</Text>
                  </View>
                </Pressable>
              );
            })}
          </ScrollView>
        </View>

        <View style={st.card}>
          <Text style={st.cardT}>Marée{sheet.tide ? <Text style={st.cardS}>  ·  {sheet.tide.label}</Text> : null}</Text>
          <TideCurve sea={sea} />
          {tides.length ? (
            <View style={st.tides}>{tides.map(e => (
              <View key={e.t} style={[st.tide, e.type === 'PM' && { backgroundColor: '#e6eef6' }]}>
                <Text style={st.tideK}>{e.type === 'PM' ? 'PM' : 'BM'}</Text>
                <Text style={st.tideV}>{e.t.slice(11, 13)}h{e.t.slice(14, 16)}</Text>
                <Text style={st.tideS}>{fr(e.h, 2)} m</Text>
              </View>
            ))}</View>
          ) : <Text style={st.hint}>Marée indicative (modèle) : pas d'horaires calculés pour ce spot.</Text>}
        </View>

        <WaterSun sst={sheet.sst[sel]} week={sheet.sst} sun={sunI >= 0 && sheet.sun ? { rise: sheet.sun.sunrise[sunI], set: sheet.sun.sunset[sunI] } : null} today={day === 0} />

        {near && (
          <Pressable onPress={() => onBuoy?.(near.b)} style={({ pressed }) => [st.card, { backgroundColor: C.sand }, pressed && { opacity: 0.85 }]}>
            <View style={st.nowRow}><View style={[st.dot, (Date.now() - new Date(near.b.time + ':00').getTime()) / 36e5 >= 2 && { backgroundColor: '#a08a5a' }]} /><Text style={[st.nowT, { color: C.sandText }]}>MESURE RÉELLE · BOUÉE {near.b.name.toUpperCase()}</Text></View>
            <View style={{ flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 8 }}>
              <Text style={[st.big, { color: C.sandText }]}>{fr(near.b.hs)}<Text style={st.bigU}> m</Text></Text>
              <Text style={[st.tileS, { color: C.sandText, marginBottom: 8 }]}>{near.b.tp ? `${Math.round(near.b.tp)} s · ` : ''}{near.b.dir != null ? sector(near.b.dir) + ' · ' : ''}{Math.round(near.k)} km</Text>
            </View>
            <Text style={[st.hint, { color: '#6b5a33' }]}>Mesuré {ageTxt(near.b.time)}, en mer : à comparer à la prévision. Voir la bouée ›</Text>
          </Pressable>
        )}
      </ScrollView>
    </View>
  );
}

/** Eau et soleil : température de l'eau sur fond d'eau, et course du soleil sur un arc (lever, coucher, durée du jour). */
function WaterSun({ sst, week, sun, today }: { sst: number | null; week: (number | null)[]; sun: { rise: string; set: string } | null; today: boolean }) {
  const w = week.filter((x): x is number => x != null);
  if (sst == null && !sun) return null;
  const rise = sun ? new Date(sun.rise + ':00') : null, set = sun ? new Date(sun.set + ':00') : null;
  const len = rise && set ? Math.round((set.getTime() - rise.getTime()) / 6e4) : 0;
  const f = rise && set && today ? (Date.now() - rise.getTime()) / (set.getTime() - rise.getTime()) : null;
  const up = f != null && f >= 0 && f <= 1;
  const R = 54, cx = 70, cy = 64, a = Math.PI * (1 - (up ? f! : 0));
  const sx = cx + R * Math.cos(a), sy = cy - R * Math.sin(a);
  return (
    <View style={st.ws}>
      {sst != null && (
        <View style={[st.wsTile, { backgroundColor: '#dcebf3' }]}>
          <Text style={st.tileK}>EAU</Text>
          <Text style={[st.big, { color: '#123c55' }]}>{fr(sst, 0)}<Text style={st.bigU}> °C</Text></Text>
          {w.length > 1 && <Text style={[st.tileS, { color: '#3d6a82' }]}>{fr(Math.min(...w), 0)} à {fr(Math.max(...w), 0)} °C sur 7 jours</Text>}
          <Svg width="100%" height={26} viewBox="0 0 160 26" preserveAspectRatio="none" style={st.wsWave}>
            <Path d="M0 12 C20 4 40 4 60 12 S100 20 120 12 S150 4 160 10 V26 H0Z" fill="#bcd8e8" />
            <Path d="M0 18 C25 11 45 11 70 18 S115 25 140 18 S155 14 160 16 V26 H0Z" fill="#9cc5dc" />
          </Svg>
        </View>
      )}
      {rise && set && (
        <View style={[st.wsTile, { backgroundColor: C.sandA }]}>
          <Text style={[st.tileK, { color: '#7a5f33' }]}>SOLEIL</Text>
          <Svg width="100%" height={70} viewBox="0 0 140 70">
            <Path d={`M${cx - R} ${cy} A${R} ${R} 0 0 1 ${cx + R} ${cy}`} stroke="#c9a463" strokeWidth={1.5} strokeDasharray="3 4" fill="none" />
            {up && <Path d={`M${cx - R} ${cy} A${R} ${R} 0 0 1 ${sx.toFixed(1)} ${sy.toFixed(1)}`} stroke="#b8892f" strokeWidth={2.5} fill="none" strokeLinecap="round" />}
            <Path d={`M8 ${cy} H132`} stroke="#d9b779" strokeWidth={1} />
            {up && <Circle cx={sx} cy={sy} r={7} fill="#f2b632" stroke="#fff" strokeWidth={2} />}
          </Svg>
          <View style={st.wsSun}>
            <Text style={st.wsT}>{rise.getHours()} h {String(rise.getMinutes()).padStart(2, '0')}</Text>
            <Text style={st.wsT}>{set.getHours()} h {String(set.getMinutes()).padStart(2, '0')}</Text>
          </View>
          <Text style={[st.tileS, { color: '#7a5f33', textAlign: 'center' }]}>{Math.floor(len / 60)} h {String(len % 60).padStart(2, '0')} de jour</Text>
        </View>
      )}
    </View>
  );
}

/** Courbe de la hauteur d'eau sur la journée (même source que le site : calcul harmonique ou modèle). */
function TideCurve({ sea }: { sea: (number | null)[] }) {
  const v = sea.map(x => x ?? NaN), ok = v.filter(x => !isNaN(x));
  if (ok.length < 4) return null;
  const W = 320, H = 64, mn = Math.min(...ok), mx = Math.max(...ok), n = v.length - 1;
  const pts = v.map((y, i) => [(i / n) * W, isNaN(y) ? NaN : H - 6 - ((y - mn) / Math.max(0.01, mx - mn)) * (H - 12)]).filter(p => !isNaN(p[1]));
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
  const nowX = ((new Date().getHours() + new Date().getMinutes() / 60) / 24) * W;
  return (
    <Svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ marginTop: 10 }}>
      <Path d={`${d} L${W},${H} L0,${H} Z`} fill="#dfe8ef" />
      <Path d={d} stroke={C.ink} strokeWidth={1.6} fill="none" />
      <Circle cx={nowX} cy={H / 2} r={0} />
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

const st = StyleSheet.create({
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
  tiles: { flexDirection: 'row', gap: 8, marginTop: 12 },
  tile: { flex: 1, backgroundColor: C.soft, borderRadius: 18, padding: 12 },
  tileK: { fontFamily: F.tX, fontSize: 10.5, letterSpacing: 1.1, color: C.ink2 },
  big: { fontFamily: F.numX, fontSize: 34, color: C.ink, letterSpacing: -1.5, marginTop: 4 },
  bigU: { fontFamily: F.tB, fontSize: 13, letterSpacing: 0 },
  tileRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 6 },
  tileS: { fontFamily: F.tB, fontSize: 12.5, color: C.ink2 },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 4, height: 24, borderRadius: 12, paddingHorizontal: 8, backgroundColor: '#e3e9ec' },
  badgeT: { fontFamily: F.tX, fontSize: 11.5, color: C.ink },
  gustT: { fontFamily: F.tB, fontSize: 12, color: C.ink2, marginTop: 6 },
  ws: { flexDirection: 'row', gap: 10, marginHorizontal: 12, marginTop: 10 },
  wsTile: { flex: 1, borderRadius: 24, padding: 14, overflow: 'hidden', minHeight: 150 },
  wsWave: { position: 'absolute', left: 0, right: 0, bottom: 0 },
  wsSun: { flexDirection: 'row', justifyContent: 'space-between', marginTop: -4 },
  wsT: { fontFamily: F.num, fontSize: 12.5, color: C.sandText },
  grid: { paddingTop: 14, gap: 4, paddingRight: 4 },
  labels: { width: 30, gap: 4 },
  lab: { fontFamily: F.tB, fontSize: 10, color: C.ink3, textAlignVertical: 'center', paddingTop: 22 },
  col: { width: COL, gap: 4, alignItems: 'stretch' },
  hh: { fontFamily: F.tX, fontSize: 12, color: C.ink2, textAlign: 'center', height: 26, lineHeight: 26 },
  cell: { borderRadius: 10, alignItems: 'center', justifyContent: 'center', gap: 2 },
  cellOn: { borderWidth: 2, borderColor: C.ink },
  cellBig: { fontFamily: F.num, fontSize: 16, color: C.ink, letterSpacing: -0.8 },
  cellMid: { fontFamily: F.tX, fontSize: 12.5, color: C.ink },
  cellSm: { fontFamily: F.tB, fontSize: 9, color: 'rgba(16,32,44,0.75)' },
  cardT: { fontFamily: F.num, fontSize: 16, color: C.ink, letterSpacing: -0.3 },
  cardS: { fontFamily: F.tB, fontSize: 13, color: C.ink2, letterSpacing: 0 },
  tides: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10 },
  tide: { flexGrow: 1, flexBasis: '45%', flexDirection: 'row', alignItems: 'baseline', gap: 8, backgroundColor: C.soft, borderRadius: 16, paddingVertical: 10, paddingHorizontal: 12 },
  tideK: { fontFamily: F.tX, fontSize: 9.5, letterSpacing: 0.8, color: C.ink2 },
  tideV: { fontFamily: F.num, fontSize: 15, color: C.ink, letterSpacing: -0.5 },
  tideS: { fontFamily: F.tB, fontSize: 11.5, color: C.ink2 },
  hint: { fontFamily: F.t, fontSize: 12.5, color: C.ink2, marginTop: 8 },
});
