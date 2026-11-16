import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Arrow from './Arrow';
import { ageTxt, Buoy, fr, JOURS, loadSheet, regionName, sector, Sheet, sizeCol, SpotLite, windRel } from './data';
import { C, R } from './theme';

type Props = { spot: SpotLite; buoys: Buoy[]; fav: boolean; onFav: () => void; onBack: () => void };

const km = (a: { lat: number; lon: number }, b: { lat: number; lon: number }) => {
  const r = Math.PI / 180, x = (b.lon - a.lon) * r * Math.cos(((a.lat + b.lat) / 2) * r), y = (b.lat - a.lat) * r;
  return Math.sqrt(x * x + y * y) * 6371;
};

export default function SpotSheet({ spot, buoys, fav, onFav, onBack }: Props) {
  const [sheet, setSheet] = useState<Sheet | null>(null);
  const [err, setErr] = useState(false);
  const [day, setDay] = useState(0);
  const [hour, setHour] = useState<number | null>(null);

  useEffect(() => { loadSheet(spot.slug).then(r => setSheet(r.data)).catch(() => setErr(true)); }, [spot.slug]);

  const days = useMemo(() => {
    if (!sheet) return [];
    const out: { date: string; idx: number[] }[] = [];
    const t0 = new Date(sheet.t0 + ':00').getTime();
    sheet.hs.forEach((_, i) => {
      const d = new Date(t0 + i * 36e5), key = d.toDateString();
      if (!out.length || out[out.length - 1].date !== key) out.push({ date: key, idx: [] });
      out[out.length - 1].idx.push(i);
    });
    return out.slice(0, 7);
  }, [sheet]);

  if (err) return <Center onBack={onBack} text="Fiche indisponible. Vérifie la connexion." />;
  if (!sheet || !days.length) return <Center onBack={onBack} loading />;

  const t0 = new Date(sheet.t0 + ':00').getTime();
  const nowI = Math.max(0, Math.min(sheet.hs.length - 1, Math.floor((Date.now() - t0) / 36e5)));
  const d = days[day];
  const hrs = d.idx.filter(i => { const h = new Date(t0 + i * 36e5).getHours(); return h >= 5 && h <= 22 && (day > 0 || i >= nowI); });   // aujourd'hui : à partir de maintenant
  const sel = hour != null && d.idx.includes(hour) ? hour : day === 0 ? (hrs[0] ?? nowI) : hrs.find(i => new Date(t0 + i * 36e5).getHours() >= 10) ?? hrs[0];
  const rel = windRel(sheet.wdir[sel], sheet.ori);
  const tides = (sheet.tide?.extremes || []).filter(e => new Date(e.t + ':00').toDateString() === d.date);
  const sun = sheet.sun ? sheet.sun.time.findIndex(x => new Date(x + 'T12:00').toDateString() === d.date) : -1;
  const near = [...buoys].map(b => ({ b, k: km(spot, b) })).filter(x => x.k < 130).sort((a, b) => a.k - b.k)[0];
  const maxH = Math.max(2.5, ...hrs.map(i => sheet.hs[i] ?? 0));   // échelle commune : une petite houle reste une petite barre
  const hh = (i: number) => `${new Date(t0 + i * 36e5).getHours()} h`;

  return (
    <ScrollView contentContainerStyle={{ paddingBottom: 48 }}>
      <View style={st.bar}>
        <Pressable onPress={onBack} hitSlop={12}><Text style={st.back}>‹ Spots</Text></Pressable>
        <Pressable onPress={onFav} hitSlop={12} accessibilityLabel={fav ? 'Retirer des favoris' : 'Ajouter aux favoris'}>
          <Text style={[st.star, fav && { color: C.sandDeep }]}>{fav ? '★' : '☆'}</Text>
        </Pressable>
      </View>
      <View style={{ paddingHorizontal: 20 }}>
        <Text style={st.title}>{sheet.name}</Text>
        <Text style={st.region}>{regionName(sheet.region)}{sheet.commune && sheet.commune !== sheet.name ? ' · ' + sheet.commune : ''}</Text>
      </View>

      <View style={st.hero}>
        <Text style={st.when}>{day === 0 && sel === nowI ? 'Maintenant' : `${JOURS[new Date(t0 + sel * 36e5).getDay()]} ${hh(sel)}`}</Text>
        <View style={{ flexDirection: 'row', alignItems: 'flex-end', gap: 8 }}>
          <Text style={st.big}>{fr(sheet.hs[sel])}</Text><Text style={st.unit}>m</Text>
        </View>
        <View style={st.heroRow}>
          <View style={st.kv}><Text style={st.k}>Période</Text><Text style={st.v}>{fr(sheet.tp[sel], 0)}<Text style={st.vu}> s</Text></Text></View>
          <View style={st.kv}><Text style={st.k}>Houle</Text><View style={st.vr}><Arrow dir={sheet.dir[sel]} size={14} /><Text style={st.v}>{sector(sheet.dir[sel])}</Text></View></View>
          <View style={st.kv}><Text style={st.k}>Vent</Text><View style={st.vr}><Arrow dir={sheet.wdir[sel]} size={14} color={C.sea} /><Text style={st.v} numberOfLines={1}>{fr(sheet.wind[sel], 0)}<Text style={st.vu}> km/h</Text></Text></View></View>
        </View>
        <Text style={st.note}>
          {rel ? `Vent ${rel}` : 'Vent'}{sheet.gust[sel] != null ? ` · rafales ${fr(sheet.gust[sel], 0)} km/h` : ''}{sheet.sst[sel] != null ? ` · eau ${fr(sheet.sst[sel], 0)} °C` : ''}
        </Text>
        <Text style={st.hint}>Hauteur prévue au large du spot, pas la taille au bord.</Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.days}>
        {days.map((x, i) => {
          const dd = new Date(t0 + x.idx[0] * 36e5), hv = x.idx.map(j => sheet.hs[j] ?? 0);
          return (
            <Pressable key={x.date} onPress={() => { setDay(i); setHour(null); }} style={[st.day, i === day && st.dayOn]}>
              <Text style={[st.dayT, i === day && { color: '#fff' }]}>{i === 0 ? "Auj." : JOURS[dd.getDay()]}</Text>
              <Text style={[st.dayN, i === day && { color: '#fff' }]}>{dd.getDate()}</Text>
              <View style={[st.dayDot, { backgroundColor: sizeCol(Math.max(...hv)) }]} />
            </Pressable>
          );
        })}
      </ScrollView>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.hours}>
        {hrs.map(i => (
          <Pressable key={i} onPress={() => setHour(i)} style={[st.h, i === sel && st.hOn]}>
            <Text style={st.hT}>{hh(i)}</Text>
            <View style={st.hBarBox}><View style={[st.hBar, { height: `${Math.max(8, ((sheet.hs[i] ?? 0) / maxH) * 100)}%`, backgroundColor: sizeCol(sheet.hs[i]) }]} /></View>
            <Text style={st.hV}>{fr(sheet.hs[i])}</Text>
            <Text style={st.hS}>{fr(sheet.tp[i], 0)} s</Text>
            <Arrow dir={sheet.wdir[i]} size={12} color={C.sea} />
            <Text style={st.hS}>{fr(sheet.wind[i], 0)}</Text>
          </Pressable>
        ))}
      </ScrollView>

      <View style={st.card}>
        <Text style={st.cardT}>Marée{sheet.tide ? ` · ${sheet.tide.label}` : ''}</Text>
        {tides.length ? (
          <View style={st.tides}>{tides.map(e => (
            <View key={e.t} style={st.tide}><Text style={st.k}>{e.type === 'PM' ? 'Pleine mer' : 'Basse mer'}</Text><Text style={st.v}>{e.t.slice(11, 16).replace(':', ' h ')}</Text><Text style={st.hS}>{fr(e.h, 2)} m</Text></View>
          ))}</View>
        ) : <Text style={st.hint}>Horaires calculés indisponibles pour ce spot : marée indicative seulement.</Text>}
        {sun >= 0 && sheet.sun && <Text style={[st.hint, { marginTop: 10 }]}>Soleil : lever {sheet.sun.sunrise[sun].slice(11, 16)} · coucher {sheet.sun.sunset[sun].slice(11, 16)}</Text>}
      </View>

      {near && (
        <View style={st.card}>
          <Text style={st.cardT}>Bouée la plus proche</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 8 }}>
            <View><Text style={st.v}>{near.b.name}</Text><Text style={st.hS}>{Math.round(near.k)} km · mesuré {ageTxt(near.b.time)}{near.b.tp ? ` · ${Math.round(near.b.tp)} s` : ''}</Text></View>
            <View style={[st.bPill]}><Text style={st.bPillT}>{fr(near.b.hs)} m</Text></View>
          </View>
          <Text style={[st.hint, { marginTop: 8 }]}>Mesure réelle en mer, à comparer à la prévision.</Text>
        </View>
      )}
    </ScrollView>
  );
}

function Center({ onBack, loading, text }: { onBack: () => void; loading?: boolean; text?: string }) {
  return (
    <View style={{ flex: 1 }}>
      <View style={st.bar}><Pressable onPress={onBack} hitSlop={12}><Text style={st.back}>‹ Spots</Text></Pressable></View>
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30 }}>
        {loading ? <ActivityIndicator color={C.ink} /> : <Text style={{ color: C.ink2, textAlign: 'center' }}>{text}</Text>}
      </View>
    </View>
  );
}

const st = StyleSheet.create({
  bar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 10 },
  back: { fontSize: 17, fontWeight: '700', color: C.ink },
  star: { fontSize: 28, color: C.ink3 },
  title: { fontSize: 32, fontWeight: '800', color: C.ink, letterSpacing: -1 },
  region: { color: C.ink2, fontWeight: '600', marginTop: 2 },
  hero: { margin: 16, padding: 20, borderRadius: R.card, backgroundColor: C.sandSoft },
  when: { fontSize: 12, fontWeight: '800', letterSpacing: 1.2, textTransform: 'uppercase', color: C.sandDeep },
  big: { fontSize: 64, fontWeight: '800', color: C.ink, letterSpacing: -2, lineHeight: 70 },
  unit: { fontSize: 22, fontWeight: '700', color: C.ink, marginBottom: 12 },
  heroRow: { flexDirection: 'row', gap: 10, marginTop: 10 },
  kv: { flex: 1, backgroundColor: '#fff', borderRadius: 14, padding: 10 },
  k: { fontSize: 11, fontWeight: '700', color: C.ink3, textTransform: 'uppercase', letterSpacing: 0.8 },
  v: { fontSize: 16, fontWeight: '800', color: C.ink, marginTop: 2 },
  vu: { fontSize: 12, fontWeight: '700', color: C.ink2 },
  vr: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 2 },
  note: { marginTop: 12, color: C.ink, fontWeight: '600' },
  hint: { marginTop: 4, color: C.ink2, fontSize: 12.5 },
  days: { paddingHorizontal: 16, gap: 8 },
  day: { width: 58, paddingVertical: 10, borderRadius: 18, alignItems: 'center', backgroundColor: C.card, borderWidth: 1, borderColor: C.line },
  dayOn: { backgroundColor: C.ink, borderColor: C.ink },
  dayT: { fontSize: 12, fontWeight: '700', color: C.ink2 },
  dayN: { fontSize: 18, fontWeight: '800', color: C.ink },
  dayDot: { width: 18, height: 5, borderRadius: 3, marginTop: 5 },
  hours: { paddingHorizontal: 16, paddingVertical: 14, gap: 6 },
  h: { width: 52, alignItems: 'center', paddingVertical: 10, borderRadius: 16, backgroundColor: C.card, gap: 3 },
  hOn: { borderWidth: 2, borderColor: C.ink },
  hT: { fontSize: 12, fontWeight: '700', color: C.ink2 },
  hBarBox: { height: 56, width: 14, justifyContent: 'flex-end', marginVertical: 4 },
  hBar: { width: 14, borderRadius: 7 },
  hV: { fontSize: 14, fontWeight: '800', color: C.ink },
  hS: { fontSize: 12, color: C.ink2 },
  card: { marginHorizontal: 16, marginTop: 10, padding: 18, borderRadius: R.card, backgroundColor: C.card },
  cardT: { fontSize: 16, fontWeight: '800', color: C.ink },
  tides: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 10 },
  tide: { minWidth: 92, backgroundColor: C.sandSoft, borderRadius: 14, padding: 10 },
  bPill: { backgroundColor: C.sand, borderRadius: 18, paddingHorizontal: 14, height: 38, justifyContent: 'center' },
  bPillT: { fontSize: 16, fontWeight: '800', color: '#2a2112' },
});
