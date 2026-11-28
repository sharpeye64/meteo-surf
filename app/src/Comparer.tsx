/** Comparateur (maquette de l'itération 3), indépendant de la PR #21 : il lit les fiches des spots déjà publiées.
 *  - Moment LIBRE : un jour et une heure, gardés comme un INSTANT absolu (heure de Paris choisie, D21). Chaque spot affiche
 *    son heure locale (Lisbonne au Portugal) : on compare le même instant, pas la même heure écrite.
 *  - Sections Houle (barres depuis 0, échelle 3 m ou plus, écart au premier spot), Période (échelle 16 s), Vent + marée.
 *  - Aucun classement, aucune note : l'ordre est celui choisi par l'utilisateur. Quatre spots au plus.
 *  Les fiches arrivent une à une (réseau faible) ; une fiche absente est dite comme telle, jamais remplacée par une valeur. */
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Arrow from './Arrow';
import { fr, loadSheetShared, sector, Sheet, WIND_WORD, windCat } from './data';
import Info from './Info';
import { useData } from './store';
import { C, F, periodCell, sizeCell, themed } from './theme';
import { civilDays, valueAt as sample } from './series';
import { hhIn, partsIn, placeTz, tMs } from './time';

const J = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];
type Got = { sheet: Sheet | null; err: boolean };

/** Valeur d'une série à un instant : échantillon EXACT seulement (src/series.ts), sinon null, dit « heure indisponible ». */
const valueAt = (sheet: Sheet, key: 'hs' | 'tp' | 'dir' | 'wind' | 'wdir' | 'gust', ms: number) => sample(tMs(sheet.t0), sheet[key], ms);

export default function Comparer() {
  const { index, compare, setCompare, favs } = useData();
  const ins = useSafeAreaInsets();
  const slugs = compare ?? favs.slice(0, 3);   // jamais réglée : les favoris ; vidée par l'utilisateur : reste vide
  const spots = slugs.map(s => index?.spots.find(x => x.slug === s)).filter(Boolean) as NonNullable<typeof index>['spots'];
  const [got, setGot] = useState<Record<string, Got>>({});
  const [ms, setMs] = useState(() => Math.ceil(Date.now() / 36e5) * 36e5);

  useEffect(() => {
    let alive = true;
    slugs.forEach(slug => {
      if (got[slug]?.sheet) return;
      loadSheetShared(slug).then(r => { if (alive) setGot(g => ({ ...g, [slug]: { sheet: r.data, err: false } })); })
        .catch(() => { if (alive) setGot(g => ({ ...g, [slug]: { sheet: g[slug]?.sheet ?? null, err: true } })); });
    });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slugs.join(',')]);

  const p = partsIn(ms, 'Europe/Paris');
  const start = Math.floor(Date.now() / 36e5) * 36e5, end = start + 7 * 24 * 36e5;
  // jours CIVILS de Paris (jamais par sauts de 24 h : changement d'heure), jour de semaine et numéro lus sur la date
  const days = useMemo(() => civilDays(partsIn(start, 'Europe/Paris').date, 8).map(date => ({ date, d: +date.slice(8, 10), wd: new Date(`${date}T12:00:00Z`).getUTCDay() })), [start]);
  const step = (h: number) => { const n = Math.min(end, Math.max(start, ms + h * 36e5)); if (n !== ms) { Haptics.selectionAsync().catch(() => {}); setMs(n); } };
  const pickDay = (date: string) => {
    const n = tMs(`${date}T${String(p.h).padStart(2, '0')}:00`);   // même heure de Paris ce jour-là (changement d'heure compris)
    Haptics.selectionAsync().catch(() => {}); setMs(Math.min(end, Math.max(start, n)));
  };

  const rows = spots.map(s => {
    const g = got[s.slug], sh = g?.sheet ?? null;
    const v = (k: Parameters<typeof valueAt>[1]) => (sh ? valueAt(sh, k, ms) : null);
    return { s, sh, err: !!g?.err && !sh, hs: v('hs'), tp: v('tp'), dir: v('dir'), wind: v('wind'), wdir: v('wdir'), gust: v('gust'), tz: placeTz(sh ?? s) };
  });
  const hsMax = Math.max(3, ...rows.map(r => r.hs ?? 0)), tpMax = Math.max(16, ...rows.map(r => r.tp ?? 0));
  const ref = rows[0]?.hs;

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <View style={[st.bar, { paddingTop: ins.top + 6 }]}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={st.round} accessibilityLabel="Retour"><Text style={st.roundT}>‹</Text></Pressable>
        <Text style={st.title}>Comparer</Text>
        <View style={{ width: 42 }} />
      </View>

      <ScrollView contentContainerStyle={{ paddingBottom: ins.bottom + 40 }}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.chips}>
          {spots.map(s => (
            <Pressable key={s.slug} onPress={() => { Haptics.selectionAsync().catch(() => {}); setCompare(slugs.filter(x => x !== s.slug)); }} style={st.chip} accessibilityLabel={`Retirer ${s.name}`}>
              <Text style={st.chipT} numberOfLines={1}>{s.name}</Text><Text style={st.chipX}>×</Text>
            </Pressable>
          ))}
          {spots.length < 4 && (
            <Pressable onPress={() => { if (compare == null && slugs.length) setCompare(slugs); router.push({ pathname: '/recherche', params: { pick: '1' } }); }} style={[st.chip, st.chipAdd]} accessibilityLabel="Ajouter un spot">
              <Text style={[st.chipT, { color: C.onNight }]}>+ Spot</Text>
            </Pressable>
          )}
        </ScrollView>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.days}>
          {days.map((d, k) => {
            const on = d.date === p.date;
            return (
              <Pressable key={d.date} onPress={() => !on && pickDay(d.date)} style={[st.day, on && st.dayOn]} accessibilityState={{ selected: on }}>
                <Text style={[st.dayJ, on && { color: C.onNight }]}>{k === 0 ? 'auj.' : J[d.wd]}</Text>
                <Text style={[st.dayN, on && { color: C.onNight }]}>{d.d}</Text>
              </Pressable>
            );
          })}
        </ScrollView>
        <View style={st.stepper}>
          <Pressable onPress={() => step(-1)} style={st.stepB} accessibilityLabel="Une heure plus tôt" disabled={ms <= start}><Text style={[st.stepT, ms <= start && { opacity: 0.3 }]}>‹</Text></Pressable>
          <View style={{ alignItems: 'center' }}>
            <Text style={st.hour}>{p.h} h</Text>
            <Text style={st.hourS}>heure de Paris</Text>
          </View>
          <Pressable onPress={() => step(1)} style={st.stepB} accessibilityLabel="Une heure plus tard" disabled={ms >= end}><Text style={[st.stepT, ms >= end && { opacity: 0.3 }]}>›</Text></Pressable>
        </View>

        {!spots.length ? (
          <View style={st.card}><Text style={st.empty}>Ajoutez des spots avec « + Spot », ou depuis le bouton Comparer d’une fiche.</Text></View>
        ) : (
          <>
            <Section title="Houle" info={['Hauteur au large de chaque spot. À droite : écart avec le premier spot.', 'Barres à la même échelle, depuis zéro.']}>
              {rows.map((r, k) => (
                <Line key={r.s.slug} name={r.s.name} local={localHour(ms, r.tz)} state={r}>
                  <Bar v={r.hs} max={hsMax} color={sizeCell(r.hs)} label={r.hs != null ? `${fr(r.hs)} m` : 'heure indisponible'} />
                  <Text style={st.diff}>{k && r.hs != null && ref != null ? `${r.hs - ref >= 0 ? '+' : '−'}${fr(Math.abs(r.hs - ref))}` : ''}</Text>
                </Line>
              ))}
            </Section>
            <Section title="Période">
              {rows.map(r => (
                <Line key={r.s.slug} name={r.s.name} local={localHour(ms, r.tz)} state={r}>
                  <Bar v={r.tp} max={tpMax} color={periodCell(r.tp)} label={r.tp != null ? `${Math.round(r.tp)} s` : 'heure indisponible'} />
                  <View style={st.dirW}><Arrow dir={r.dir} size={11} color={C.ink2} /><Text style={st.diff}>{sector(r.dir)}</Text></View>
                </Line>
              ))}
            </Section>
            <Section title="Vent et marée" info={['Orientation du vent par rapport à chaque plage.', 'Marée : prochaine pleine (PM) ou basse mer (BM) au port de référence du spot, à son heure locale.']}>
              {rows.map(r => {
                const c = windCat(r.wind, r.wdir, r.s.ori), col = c === 'offshore' || c === 'side-off' ? C.off : c === 'de côté' ? C.side : c === 'onshore' ? C.on : C.ink2;
                const tide = r.sh?.tide?.extremes.find(e => tMs(e.t) >= ms);
                return (
                  <Line key={r.s.slug} name={r.s.name} local={localHour(ms, r.tz)} state={r}>
                    <View style={st.wind}>
                      <Arrow dir={r.wdir} size={12} color={C.ink} />
                      <Text style={st.windV}>{r.wind != null ? Math.round(r.wind) : '—'}<Text style={st.windU}> km/h</Text></Text>
                      {!!c && <Text style={[st.windC, { color: col }]}>{WIND_WORD[c]}</Text>}
                    </View>
                    <Text style={st.tide} numberOfLines={1}>{tide ? `${tide.type} ${hhIn(tMs(tide.t), r.tz)}` : r.sh && !r.sh.tide ? 'marée —' : ''}</Text>
                  </Line>
                );
              })}
            </Section>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const localHour = (ms: number, tz: string) => (tz === 'Europe/Paris' ? null : `${hhIn(ms, tz)} sur place`);

function Section({ title, info, children }: { title: string; info?: string[]; children: React.ReactNode }) {
  return (
    <View style={st.card}>
      <View style={st.secHd}><Text style={st.secT}>{title}</Text>{info && <Info lines={info} />}</View>
      <View style={{ gap: 10, marginTop: 10 }}>{children}</View>
    </View>
  );
}

function Line({ name, local, state, children }: { name: string; local: string | null; state: { sh: Sheet | null; err: boolean }; children: React.ReactNode }) {
  return (
    <View>
      <Text style={st.lineN} numberOfLines={1}>{name}{local ? <Text style={st.lineL}>  · {local}</Text> : null}</Text>
      <View style={st.lineR}>
        {state.sh ? children : state.err ? <Text style={st.miss}>fiche indisponible</Text> : <ActivityIndicator size="small" color={C.ink3} />}
      </View>
    </View>
  );
}

function Bar({ v, max, color, label }: { v: number | null; max: number; color: string; label: string }) {
  // barres depuis 0 : rien pour 0 ; un trait minimal (3 %) seulement pour une petite valeur strictement positive
  const w = v != null && v > 0 ? Math.max(0.03, Math.min(1, v / max)) : 0;
  return (
    <View style={st.track}>
      <View style={[st.fill, { width: `${w * 100}%`, backgroundColor: color }]} />
      <Text style={st.barT}>{label}</Text>
    </View>
  );
}

const st = themed(() => StyleSheet.create({
  bar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 14, paddingBottom: 6 },
  round: { width: 42, height: 42, borderRadius: 21, backgroundColor: C.card, alignItems: 'center', justifyContent: 'center' },
  roundT: { fontFamily: F.tX, fontSize: 24, color: C.ink, marginTop: -2 },
  title: { fontFamily: F.num, fontSize: 18, color: C.ink, letterSpacing: -0.5 },
  chips: { paddingHorizontal: 12, paddingVertical: 8, gap: 6 },
  chip: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 38, paddingHorizontal: 14, borderRadius: 19, backgroundColor: C.card, maxWidth: 200 },
  chipAdd: { backgroundColor: C.night },
  chipT: { fontFamily: F.tX, fontSize: 13.5, color: C.ink, flexShrink: 1 },
  chipX: { fontFamily: F.tX, fontSize: 15, color: C.ink3 },
  days: { paddingHorizontal: 12, paddingTop: 6, gap: 6 },
  day: { width: 50, paddingVertical: 8, borderRadius: 16, alignItems: 'center', backgroundColor: C.card },
  dayOn: { backgroundColor: C.night },
  dayJ: { fontFamily: F.tX, fontSize: 10, color: C.ink3 },
  dayN: { fontFamily: F.numX, fontSize: 17, color: C.ink },
  stepper: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 26, marginTop: 10 },
  stepB: { width: 48, height: 48, borderRadius: 24, backgroundColor: C.card, alignItems: 'center', justifyContent: 'center' },
  stepT: { fontFamily: F.tX, fontSize: 24, color: C.ink, marginTop: -2 },
  hour: { fontFamily: F.numX, fontSize: 26, color: C.ink, letterSpacing: -1 },
  hourS: { fontFamily: F.tB, fontSize: 11, color: C.ink3 },
  card: { marginHorizontal: 12, marginTop: 14, padding: 16, borderRadius: 24, backgroundColor: C.card },
  empty: { fontFamily: F.t, fontSize: 14, color: C.ink2, lineHeight: 20 },
  secT: { fontFamily: F.num, fontSize: 16, color: C.ink, letterSpacing: -0.4 },
  secHd: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 8 },
  secS: { fontFamily: F.tB, fontSize: 11.5, color: C.ink3, marginTop: 2 },
  lineN: { fontFamily: F.tX, fontSize: 13, color: C.ink },
  lineL: { fontFamily: F.tB, fontSize: 11.5, color: C.ink3 },
  lineR: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 5, minHeight: 30 },
  track: { flex: 1, height: 30, borderRadius: 10, backgroundColor: C.soft, overflow: 'hidden', justifyContent: 'center' },
  fill: { position: 'absolute', left: 0, top: 0, bottom: 0, borderRadius: 10 },
  barT: { fontFamily: F.num, fontSize: 13, color: C.ink, marginLeft: 10, letterSpacing: -0.4 },
  diff: { minWidth: 44, textAlign: 'right', fontFamily: F.tX, fontSize: 12, color: C.ink2 },
  dirW: { flexDirection: 'row', alignItems: 'center', gap: 3, minWidth: 54, justifyContent: 'flex-end' },
  wind: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6 },
  windV: { fontFamily: F.num, fontSize: 15, color: C.ink, letterSpacing: -0.4 },
  windU: { fontFamily: F.tB, fontSize: 10.5, letterSpacing: 0 },
  windC: { fontFamily: F.tX, fontSize: 12 },
  tide: { fontFamily: F.tB, fontSize: 12, color: C.ink2 },
  miss: { fontFamily: F.tB, fontSize: 12, color: C.ink3 },
  foot: { fontFamily: F.tR, fontSize: 12, color: C.ink3, textAlign: 'center', marginTop: 16, paddingHorizontal: 30 },
}));
