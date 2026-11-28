/** Fiche d'un spot (maquette « fiche spot » de l'itération 3), ouverte en panneau natif au-dessus de la carte.
 *  En haut : trois colonnes Houle / Vent / Marée pour l'heure choisie. Puis les jours, la GRANDE frise de 6 h à 21 h
 *  (colonnes de 46 px : hauteur avec la flèche, période, vent avec son orientation en filet de couleur, rafales, courbe de
 *  marée), heures de nuit grisées. Ensuite des phrases factuelles (jamais d'avis), puis la bouée de référence, qui est la
 *  mesure de MAINTENANT (pas de l'heure choisie). Aucune note, aucun score. */
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, G, Line, Path, Text as SvgText } from 'react-native-svg';
import Arrow from './Arrow';
import { ageTxt, Buoy, freshOf, fr, loadSheet, perTxt, refBuoy, regionName, sector, Sheet, SpotLite, WIND_WORD, windCat, WindCat } from './data';
import { Blink } from './Live';
import { Pick, resolveSel } from './selection';
import { useData, useDataAge, useMinute } from './store';
import { C, F, periodCell, sizeCell, themed, windCell } from './theme';
import { hhIn, partsIn, placeTz, tMs } from './time';
import { useReloaded } from './useReloaded';
import { agoWords, dayWord } from './series';

const J = ['DIM', 'LUN', 'MAR', 'MER', 'JEU', 'VEN', 'SAM'];
const JOUR = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];
const COL = 46, GAP = 3, TIDE_H = 58;
const catCol = (c: WindCat | null) => (c === 'offshore' || c === 'side-off' ? C.off : c === 'de côté' ? C.side : c === 'onshore' ? C.on : 'transparent');

export default function SpotSheet({ spot }: { spot: SpotLite }) {
  const { index, isFav, toggleFav, compare, setCompare } = useData();
  const minute = useMinute();
  const age = useDataAge();
  const ins = useSafeAreaInsets();
  const { data: sheet, offline, err } = useReloaded<Sheet>(loadSheet, spot.slug);
  const [pick, setPick] = useState<Pick>({ date: null, ms: null });
  const strip = useRef<{ scrollTo: (o: { x: number; animated?: boolean }) => void } | null>(null);
  const fav = isFav(spot.slug), cmp = compare ?? [], inCmp = cmp.includes(spot.slug);

  const days = useMemo(() => {
    if (!sheet) return [];
    const out: { date: string; idx: number[] }[] = [];
    const t0 = tMs(sheet.t0), tz = placeTz(sheet);
    sheet.hs.forEach((_, i) => {
      const key = partsIn(t0 + i * 36e5, tz).date;
      if (!out.length || out[out.length - 1].date !== key) out.push({ date: key, idx: [] });
      out[out.length - 1].idx.push(i);
    });
    // jours à partir d'AUJOURD'HUI à l'heure du spot (une fiche ancienne commence la veille : ces jours passés sont retirés)
    const today = partsIn(minute * 6e4, tz).date, fut = out.filter(d => d.date >= today);
    return (fut.length ? fut : out).slice(0, 7);
  }, [sheet, minute]);

  const head = (
    <View style={st.head}>
      <View style={{ flex: 1, minWidth: 0 }}>
        <Text style={st.name} numberOfLines={1} adjustsFontSizeToFit>{spot.name}</Text>
        <Text style={st.region} numberOfLines={1}>{spot.commune ? `${spot.commune} · ` : ''}{regionName(spot.region)}</Text>
        {(age.level !== 'ok' || offline) && <Text style={st.warnT}>{age.level === 'old' ? 'Données anciennes, calculées ' : 'Données calculées '}{agoWords(age.h)}{offline ? ' · hors connexion' : ''}</Text>}
      </View>
      <Pressable onPress={() => { Haptics.selectionAsync().catch(() => {}); setCompare(inCmp ? cmp.filter(s => s !== spot.slug) : [...cmp, spot.slug]); }}
        style={({ pressed }) => [st.round, inCmp && st.roundOn, pressed && st.pressed]} accessibilityLabel={inCmp ? 'Retirer de la comparaison' : 'Ajouter à la comparaison'}>
        <Svg width={19} height={19} viewBox="0 0 24 24"><Path d="M6 20V10M12 20V4M18 20v-7" stroke={inCmp ? C.onNight : C.ink} strokeWidth={2.2} strokeLinecap="round" /></Svg>
      </Pressable>
      <Pressable onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {}); toggleFav(spot.slug); }}
        style={({ pressed }) => [st.round, fav && st.roundOn, pressed && st.pressed]} accessibilityLabel={fav ? 'Retirer des favoris' : 'Ajouter aux favoris'} accessibilityState={{ selected: fav }}>
        <Text style={[st.star, fav && { color: C.measureOnNight }]}>{fav ? '★' : '☆'}</Text>
      </Pressable>
    </View>
  );

  if (err && !sheet) return <Panel head={head}><Text style={st.msg}>Fiche indisponible pour le moment. Vérifiez la connexion.</Text></Panel>;
  const t0 = sheet ? tMs(sheet.t0) : NaN, r = resolveSel(days, t0, pick);
  if (!sheet || !r) return <Panel head={head}><ActivityIndicator style={{ marginTop: 40 }} color={C.ink} /></Panel>;

  const tz = placeTz(sheet), day = r.dayI, d = days[day], today = partsIn(Date.now(), tz).date;
  const word = (date: string) => dayWord(date, today);
  const at = (i: number) => partsIn(t0 + i * 36e5, tz);
  const nowI = Math.max(0, Math.min(sheet.hs.length - 1, Math.floor((Date.now() - t0) / 36e5)));
  const hrs = d.idx.filter(i => { const h = at(i).h; return h >= 6 && h <= 21; });
  const cols = hrs.length ? hrs : d.idx;
  const def = (d.date === today ? (cols.find(i => i >= nowI) ?? cols[cols.length - 1]) : (cols.find(i => at(i).h >= 10) ?? cols[0])) ?? d.idx[0];
  const sel = r.hourI != null && d.idx.includes(r.hourI) ? r.hourI : def;
  const isNow = d.date === today && sel === nowI;
  const sunI = sheet.sun ? sheet.sun.time.findIndex(x => x === d.date) : -1;
  const rise = sunI >= 0 ? tMs(sheet.sun!.sunrise[sunI]) : NaN, set = sunI >= 0 ? tMs(sheet.sun!.sunset[sunI]) : NaN;
  const night = (i: number) => Number.isFinite(rise) && (t0 + (i + 1) * 36e5 <= rise || t0 + i * 36e5 >= set);
  const wc = windCat(sheet.wind[sel], sheet.wdir[sel], sheet.ori);
  const tides = (sheet.tide?.extremes || []).filter(e => partsIn(tMs(e.t), tz).date === d.date);
  const nextTide = (sheet.tide?.extremes || []).find(e => tMs(e.t) >= t0 + sel * 36e5);
  const ref = index ? refBuoy(index.buoys, spot) : null;
  const choose = (i: number) => { if (i === sel) return; Haptics.selectionAsync().catch(() => {}); setPick({ date: d.date, ms: t0 + i * 36e5 }); };

  return (
    <Panel head={head} bottom={ins.bottom + 30}>
        <View style={st.whenRow}>
          {isNow ? <Blink size={7} color={C.ink} /> : <View style={[st.dot, { backgroundColor: C.ink3 }]} />}
          <Text style={st.whenT}>{isNow ? 'Maintenant' : `${word(d.date) ?? JOUR[at(sel).wd]} ${at(sel).d}`} · {at(sel).h} h</Text>
        </View>
        <View style={st.hero}>
          <View style={st.heroCol}>
            <Text style={st.heroK}>Houle</Text>
            <Text style={st.heroV}>{fr(sheet.hs[sel])}<Text style={st.heroU}> m</Text></Text>
            <View style={st.heroRow}><Text style={st.heroS}>{sheet.tp[sel] != null ? `${Math.round(sheet.tp[sel]!)} s` : '—'}</Text><Arrow dir={sheet.dir[sel]} size={11} color={C.ink2} /><Text style={st.heroS}>{sector(sheet.dir[sel])}</Text></View>
          </View>
          <View style={st.heroSep} />
          <View style={st.heroCol}>
            <Text style={st.heroK}>Vent</Text>
            <Text style={st.heroV}>{fr(sheet.wind[sel], 0)}<Text style={st.heroU}> km/h</Text></Text>
            <View style={st.heroRow}><Arrow dir={sheet.wdir[sel]} size={11} color={C.ink2} /><Text style={[st.heroS, wc && wc !== 'lisse' && { color: catCol(wc), fontFamily: F.tX }]} numberOfLines={1}>{wc ? WIND_WORD[wc] : sector(sheet.wdir[sel])}</Text></View>
          </View>
          <View style={st.heroSep} />
          <View style={st.heroCol}>
            <Text style={st.heroK}>Marée</Text>
            {nextTide && partsIn(tMs(nextTide.t), tz).date !== d.date && <Text style={st.heroDay}>{word(partsIn(tMs(nextTide.t), tz).date)?.toLowerCase() ?? JOUR[partsIn(tMs(nextTide.t), tz).wd]}</Text>}
            <Text style={st.heroV}>{nextTide ? hhIn(tMs(nextTide.t), tz) : '—'}</Text>
            <Text style={st.heroS} numberOfLines={1}>{nextTide ? `${nextTide.type === 'PM' ? 'pleine mer' : 'basse mer'}${nextTide.h != null ? ` · ${fr(nextTide.h)} m` : ''}` : 'indicative'}</Text>
          </View>
        </View>

        <Text style={st.daysCap}>Houle la plus haute de 6 h à 21 h, en mètres</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={st.days}>
          {days.map((x, i) => {
            const dl = x.idx.filter(j => { const h = at(j).h; return h >= 6 && h <= 21; });
            const dd = at(x.idx[0]), mx = Math.max(...(dl.length ? dl : x.idx).map(j => sheet.hs[j] ?? 0)), on = i === day;
            return (
              <Pressable key={x.date} onPress={() => { if (on) return; Haptics.selectionAsync().catch(() => {}); setPick({ date: x.date, ms: null }); strip.current?.scrollTo({ x: 0, animated: false }); }}
                style={[st.day, on && st.dayOn]} accessibilityRole="button" accessibilityState={{ selected: on }} accessibilityLabel={`${word(x.date) ?? JOUR[dd.wd]} ${dd.d}, houle la plus haute de 6 h à 21 h : ${fr(mx)} mètre`}>
                <Text style={[st.dayJ, on && { color: C.onNight }]}>{x.date === today ? 'AUJ.' : J[dd.wd]}</Text>
                <Text style={[st.dayN, on && { color: C.onNight }]}>{dd.d}</Text>
                <Text style={[st.dayH, on && { color: C.onNight }]}>{fr(mx)}</Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <View style={st.gridWrap}>
          <View style={st.labels}>
            <Text style={[st.lab, { height: 22 }]} />
            <Text style={[st.lab, { height: 44 }]}>m</Text>
            <Text style={[st.lab, { height: 30 }]}>s</Text>
            <Text style={[st.lab, { height: 40 }]}>km/h</Text>
            <Text style={[st.lab, { height: 20 }]}>raf.</Text>
            <Text style={[st.lab, { height: TIDE_H }]}>mer</Text>
          </View>
          <ScrollView ref={strip as never} horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingRight: 14 }}
            onContentSizeChange={() => { const k = cols.indexOf(sel); if (k > 2) strip.current?.scrollTo({ x: (k - 2) * (COL + GAP), animated: false }); }}>
            <View>
              <View style={{ flexDirection: 'row', gap: GAP }}>
                {cols.map(i => {
                  const on = i === sel, h = at(i).h, c = windCat(sheet.wind[i], sheet.wdir[i], sheet.ori);
                  return (
                    <Pressable key={i} onPress={() => choose(i)} style={[st.col, night(i) && st.nightCol]}
                      accessibilityLabel={`${h} heures${night(i) ? ', de nuit' : ''} : houle ${fr(sheet.hs[i])} mètre, ${sheet.tp[i] != null ? Math.round(sheet.tp[i]!) + ' secondes' : ''}, vent ${fr(sheet.wind[i], 0)} kilomètres heure${c ? ', ' + WIND_WORD[c] : ''}`}
                      accessibilityState={{ selected: on }}>
                      <Text style={[st.hh, night(i) && st.hhNight, on && st.hhOn]}>{night(i) && !on ? '☾ ' : ''}{h}h</Text>
                      <View style={[st.cell, { height: 44, backgroundColor: sizeCell(sheet.hs[i]) }, on && st.cellOn]}>
                        <Text style={st.cBig}>{fr(sheet.hs[i])}</Text>
                        <Arrow dir={sheet.dir[i]} size={9} color={C.ink} />
                      </View>
                      <View style={[st.cell, { height: 30, backgroundColor: periodCell(sheet.tp[i]) }, on && st.cellOn]}><Text style={st.cMid}>{sheet.tp[i] != null ? Math.round(sheet.tp[i]!) : '—'}</Text></View>
                      <View style={[st.cell, { height: 40, backgroundColor: windCell(sheet.wind[i]), borderBottomWidth: 4, borderBottomColor: catCol(c) }, on && st.cellOn]}>
                        <Arrow dir={sheet.wdir[i]} size={11} color={C.ink} />
                        <Text style={st.cMid}>{fr(sheet.wind[i], 0)}</Text>
                      </View>
                      <Text style={st.gust}>{sheet.gust[i] != null ? fr(sheet.gust[i], 0) : '—'}</Text>
                    </Pressable>
                  );
                })}
              </View>
              <TideRow sheet={sheet} hrs={cols} sel={sel} t0={t0} tz={tz} />
            </View>
          </ScrollView>
        </View>
        <View style={st.legend}>
          <Leg c={C.off} t="offshore" /><Leg c={C.side} t="de côté" /><Leg c={C.on} t="onshore" />
          <Text style={st.legT}>· {sheet.tide ? `marée ${sheet.tide.label}` : 'marée indicative'}</Text>
        </View>

        <Summary sheet={sheet} cols={cols} tides={tides} at={at} tz={tz} />

        {ref ? <RefBuoy b={ref.b} km={ref.k} /> : (
          <View style={st.card}><Text style={st.cardK}>Bouée de référence</Text><Text style={st.cardS}>Aucune bouée n’a de mesure exploitable autour de ce spot pour le moment.</Text></View>
        )}
    </Panel>
  );
}

/** Structure d'un panneau natif (formSheet iOS), corrigée après le test iPhone du 28/11 :
 *  la liste qui défile est le PREMIER enfant de l'écran (règle d'Expo / react-native-screens : la ScrollView doit être
 *  atteignable par le premier enfant à chaque niveau, sinon iOS ne relie pas le défilement au glissement du panneau), et
 *  l'en-tête est DANS la liste, collant (stickyHeaderIndices) et opaque : rien ne peut défiler par-dessus ni dessous.
 *  Aucun décalage d'écran automatique d'iOS dans un panneau (contentInsetAdjustmentBehavior="never"). */
export function Panel({ head, bottom = 30, children }: { head: React.ReactNode; bottom?: number; children: React.ReactNode }) {
  return (
    <ScrollView style={st.page} stickyHeaderIndices={[0]} contentInsetAdjustmentBehavior="never" automaticallyAdjustContentInsets={false}
      contentContainerStyle={{ paddingBottom: bottom }} showsVerticalScrollIndicator={false} directionalLockEnabled>
      <View style={st.sticky}>{head}</View>
      {children}
    </ScrollView>
  );
}

function Leg({ c, t }: { c: string; t: string }) {
  return <View style={st.legI}><View style={[st.legD, { backgroundColor: c }]} /><Text style={st.legT}>{t}</Text></View>;
}

/** Quelques phrases FACTUELLES sur la journée (maximum de houle, vent le plus faible, marées) : pas d'avis, pas de note. */
function Summary({ sheet, cols, tides, at, tz }: { sheet: Sheet; cols: number[]; tides: { t: string; type: string; h: number }[]; at: (i: number) => { h: number }; tz: string }) {
  const ok = cols.filter(i => sheet.hs[i] != null);
  if (!ok.length) return null;
  const top = ok.reduce((a, b) => ((sheet.hs[b] ?? 0) > (sheet.hs[a] ?? 0) ? b : a));
  const wOk = cols.filter(i => sheet.wind[i] != null);
  const calm = wOk.length ? wOk.reduce((a, b) => ((sheet.wind[b] ?? 99) < (sheet.wind[a] ?? 99) ? b : a)) : null;
  const cc = calm != null ? windCat(sheet.wind[calm], sheet.wdir[calm], sheet.ori) : null;
  const lines = [
    `Houle la plus haute vers ${at(top).h} h : ${fr(sheet.hs[top])} m${sheet.tp[top] != null ? `, ${Math.round(sheet.tp[top]!)} s` : ''}, ${sector(sheet.dir[top])}.`,
    calm != null ? `Vent le plus faible vers ${at(calm).h} h : ${fr(sheet.wind[calm], 0)} km/h${cc ? ` (${WIND_WORD[cc].toLowerCase()})` : ''}.` : null,
    tides.length ? `Marées : ${tides.map(e => `${e.type === 'PM' ? 'pleine mer' : 'basse mer'} ${hhIn(tMs(e.t), tz)}`).join(', ')}.` : null,
  ].filter(Boolean) as string[];
  return (
    <View style={st.card}>
      <Text style={st.cardK}>La journée en bref</Text>
      {lines.map(l => <Text key={l} style={st.sum}>{l}</Text>)}
      <Text style={st.note}>Hauteur au large du spot, pas la taille des vagues au bord : à lire avec la période.</Text>
    </View>
  );
}

/** Bouée de référence (même règle que le site) : sa DERNIÈRE mesure, quelle que soit l'heure choisie ; « en direct »
 *  seulement si elle l'est selon la cadence de la station (jamais « maintenant » pour une mesure de 17 h). */
function RefBuoy({ b, km }: { b: Buoy; km: number }) {
  const f = freshOf(b);
  return (
    <Pressable onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {}); router.push({ pathname: '/bouee/[slug]', params: { slug: b.slug } }); }}
      style={({ pressed }) => [st.buoy, pressed && st.pressed]} accessibilityLabel={`Bouée ${b.name}, ${f === 'live' ? 'mesure en direct' : 'dernière mesure'} ${fr(b.hs)} mètre, ${ageTxt(b.time)}`}>
      <View style={st.buoyTop}>
        {f === 'live' ? <Blink size={8} color={C.liveOnBuoy} /> : <View style={[st.dot, { backgroundColor: C.onBuoy2 }]} />}
        <Text style={st.buoyK} numberOfLines={1}>{f === 'live' ? 'MESURE EN DIRECT' : 'DERNIÈRE MESURE'} · {b.name.toUpperCase()} · {Math.round(km)} KM</Text>
      </View>
      <View style={st.buoyRow}>
        <Text style={st.buoyV}>{fr(b.hs)}<Text style={st.buoyU}> m</Text></Text>
        <View style={{ alignItems: 'flex-end', gap: 3 }}>
          {!!perTxt(b) && <Text style={st.buoyS}>{perTxt(b)}</Text>}
          {b.dir != null && <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}><Arrow dir={b.dir} size={11} color={C.measureOnBuoy} /><Text style={st.buoyS}>{sector(b.dir)}</Text></View>}
        </View>
      </View>
      <Text style={st.buoyF}>Mesuré {ageTxt(b.time)}, en mer{b.sst != null ? ` · eau ${fr(b.sst, 0)} °C` : ''} · voir la bouée ›</Text>
    </Pressable>
  );
}

/** Courbe de marée alignée sur les colonnes, PM et BM posées à leur heure exacte (heure du lieu). */
function TideRow({ sheet, hrs, sel, t0, tz }: { sheet: Sheet; hrs: number[]; sel: number; t0: number; tz: string }) {
  const W = hrs.length * (COL + GAP) - GAP, a = hrs[0], b = hrs[hrs.length - 1];
  const x = (f: number) => (f - a) * (COL + GAP) + COL / 2;
  const val = (f: number) => { const i = Math.floor(f), u = f - i, p = sheet.sea[i], q = sheet.sea[i + 1]; return p == null ? null : q == null ? p : p + (q - p) * u; };
  const pts: [number, number][] = [];
  for (let f = a - 0.5; f <= b + 0.5001; f += 0.25) { const v = val(f); if (v != null) pts.push([f, v]); }
  if (pts.length < 4) return <View style={{ height: TIDE_H, marginTop: 4 }} />;
  const vs = pts.map(p => p[1]), mn = Math.min(...vs), mx = Math.max(...vs);
  const y = (v: number) => 10 + (1 - (v - mn) / Math.max(0.01, mx - mn)) * (TIDE_H - 22);
  const dd = pts.map(([f, v], k) => `${k ? 'L' : 'M'}${x(f).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const ext = (sheet.tide?.extremes || []).map(e => ({ ...e, f: (tMs(e.t) - t0) / 36e5 })).filter(e => e.f >= a - 0.5 && e.f <= b + 0.5);
  return (
    <Svg width={W} height={TIDE_H} style={{ marginTop: 4 }}>
      <Path d={`${dd} L${x(pts[pts.length - 1][0]).toFixed(1)},${TIDE_H} L${x(pts[0][0]).toFixed(1)},${TIDE_H} Z`} fill={C.tideFill} />
      <Path d={dd} stroke={C.ink} strokeWidth={1.4} fill="none" />
      <Line x1={x(sel)} y1={0} x2={x(sel)} y2={TIDE_H} stroke={C.ink} strokeWidth={1} strokeDasharray="2 3" />
      {ext.map(e => {
        const cy = y(val(e.f) ?? e.h), pm = e.type === 'PM', tx = Math.min(W - 28, Math.max(28, x(e.f)));
        return (
          <G key={e.t}>
            <Circle cx={x(e.f)} cy={cy} r={3.2} fill={C.ink} />
            <SvgText x={tx} y={pm ? cy + 15 : cy - 7} fontSize={10.5} fontFamily={F.tX} fill={C.ink} textAnchor="middle">{`${e.type} ${hhIn(tMs(e.t), tz).replace(' h ', 'h').replace(' h', 'h')}`}</SvgText>
          </G>
        );
      })}
    </Svg>
  );
}

const st = themed(() => StyleSheet.create({
  page: { flex: 1, backgroundColor: C.bg },
  sticky: { backgroundColor: C.bg },
  head: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 18, paddingTop: 22, paddingBottom: 8 },
  name: { fontFamily: F.num, fontSize: 24, color: C.ink, letterSpacing: -0.8 },
  region: { fontFamily: F.tB, fontSize: 12.5, color: C.ink2, marginTop: 2 },
  warnT: { fontFamily: F.tX, fontSize: 12, color: C.warn, marginTop: 3 },
  round: { width: 42, height: 42, borderRadius: 21, backgroundColor: C.card, alignItems: 'center', justifyContent: 'center' },
  roundOn: { backgroundColor: C.night },
  star: { fontSize: 19, color: C.ink, marginTop: -1 },
  pressed: { opacity: 0.75, transform: [{ scale: 0.97 }] },
  msg: { fontFamily: F.t, fontSize: 14, color: C.ink2, textAlign: 'center', marginTop: 40, paddingHorizontal: 30 },
  whenRow: { flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 18, marginTop: 6 },
  whenT: { fontFamily: F.tX, fontSize: 12, color: C.ink, letterSpacing: 0.3 },
  dot: { width: 7, height: 7, borderRadius: 4 },
  hero: { flexDirection: 'row', marginHorizontal: 12, marginTop: 8, paddingVertical: 14, paddingHorizontal: 6, borderRadius: 24, backgroundColor: C.card },
  heroCol: { flex: 1, minWidth: 0, paddingHorizontal: 8 },
  heroSep: { width: StyleSheet.hairlineWidth, backgroundColor: C.line },
  heroK: { fontFamily: F.tX, fontSize: 10, letterSpacing: 1, color: C.ink3, textTransform: 'uppercase' },
  heroDay: { fontFamily: F.tX, fontSize: 10.5, color: C.ink2, marginTop: 3, marginBottom: -4 },
  heroV: { fontFamily: F.numX, fontSize: 24, color: C.ink, letterSpacing: -1, marginTop: 4 },
  heroU: { fontFamily: F.tB, fontSize: 11.5, letterSpacing: 0 },
  heroRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 3 },
  heroS: { fontFamily: F.tB, fontSize: 12, color: C.ink2, flexShrink: 1 },
  daysCap: { fontFamily: F.tB, fontSize: 11, color: C.ink3, marginHorizontal: 18, marginTop: 14 },
  days: { paddingHorizontal: 12, paddingTop: 6, paddingBottom: 4, gap: 5 },
  day: { width: 47, paddingVertical: 6, borderRadius: 16, alignItems: 'center', backgroundColor: C.card },
  dayOn: { backgroundColor: C.night },
  dayJ: { fontFamily: F.tX, fontSize: 9.5, letterSpacing: 0.8, color: C.ink3 },
  dayN: { fontFamily: F.numX, fontSize: 16, color: C.ink },
  dayH: { fontFamily: F.tX, fontSize: 10.5, color: C.ink2 },
  gridWrap: { flexDirection: 'row', marginTop: 8, paddingLeft: 10 },
  labels: { width: 30, gap: 4 },
  lab: { fontFamily: F.tB, fontSize: 9.5, color: C.ink3, paddingTop: 2, lineHeight: 14 },
  col: { width: COL, gap: 4, borderRadius: 12 },
  nightCol: { backgroundColor: C.soft },
  hhNight: { color: C.ink3, fontFamily: F.tB },
  hh: { fontFamily: F.tX, fontSize: 11.5, color: C.ink2, textAlign: 'center', height: 22, lineHeight: 22, borderRadius: 11, overflow: 'hidden' },
  hhOn: { backgroundColor: C.night, color: C.onNight },
  cell: { borderRadius: 10, alignItems: 'center', justifyContent: 'center', gap: 1, overflow: 'hidden' },
  cellOn: { borderWidth: 2, borderColor: C.ink },
  cBig: { fontFamily: F.num, fontSize: 14.5, color: C.ink, letterSpacing: -0.7 },
  cMid: { fontFamily: F.tX, fontSize: 12.5, color: C.ink },
  gust: { fontFamily: F.tB, fontSize: 11, color: C.ink2, textAlign: 'center', height: 20, lineHeight: 20 },
  legend: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 10, paddingHorizontal: 18, marginTop: 8 },
  legI: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  legD: { width: 14, height: 4, borderRadius: 2 },
  legT: { fontFamily: F.tB, fontSize: 11, color: C.ink3 },
  card: { marginHorizontal: 12, marginTop: 14, padding: 16, borderRadius: 24, backgroundColor: C.card, gap: 6 },
  cardK: { fontFamily: F.tX, fontSize: 10.5, letterSpacing: 1, color: C.ink3, textTransform: 'uppercase' },
  cardS: { fontFamily: F.t, fontSize: 13.5, color: C.ink2 },
  sum: { fontFamily: F.t, fontSize: 14, lineHeight: 20, color: C.ink },
  note: { fontFamily: F.tR, fontSize: 12, color: C.ink3, marginTop: 2 },
  buoy: { marginHorizontal: 12, marginTop: 12, padding: 16, borderRadius: 24, backgroundColor: C.buoySurface },
  buoyTop: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  buoyK: { flex: 1, fontFamily: F.tX, fontSize: 10.5, letterSpacing: 0.9, color: C.onBuoy },
  buoyRow: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 8 },
  buoyV: { fontFamily: F.numX, fontSize: 32, color: C.measureOnBuoy, letterSpacing: -1.2 },
  buoyU: { fontFamily: F.tB, fontSize: 14, letterSpacing: 0 },
  buoyS: { fontFamily: F.tX, fontSize: 13, color: C.measureOnBuoy },
  buoyF: { fontFamily: F.t, fontSize: 12, color: C.onBuoy, marginTop: 8 },
}));
