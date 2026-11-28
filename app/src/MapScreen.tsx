/** Accueil : la carte seule (chantier #8). Pas de panneau permanent (D13) : un toucher sur un repère ouvre sa fiche en
 *  panneau natif, la carte reste montée derrière.
 *  DENSITÉ (retour du porteur après le test iPhone du 28/11, src/density.ts) : trois niveaux de lecture selon le zoom,
 *  sans chevauchement — loin : un regroupement par région ; milieu : pastilles choisies sans collision, les autres spots en
 *  points ; près : pastilles détaillées (nom + valeurs). Les bouées sont réservées d'abord (leur point ne disparaît jamais
 *  sous un spot) et leur étiquette dorée ne s'affiche que s'il y a la place.
 *  STABILITÉ (revue de René) : une clé par spot / bouée / région, jamais recréée au zoom ; seul l'aspect change. Les repères
 *  sont figés (tracksViewChanges=false) et ne se redessinent que pendant 0,7 s après un changement d'aspect.
 *  FOND : plan épuré par défaut (lisibilité des pastilles), satellite à un toucher. Unités partout (m, s, km/h). */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Haptics from 'expo-haptics';
import * as Location from 'expo-location';
import { router } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { MapType, Marker, Region } from 'react-native-maps';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Defs, LinearGradient, Path, Rect, Stop } from 'react-native-svg';
import Arrow from './Arrow';
import { Buoy, freshOf, fr, hav, perTxt, refBuoy, regionName, sector, SpotLite, spotPoint, WIND_WORD, windCat } from './data';
import { bucketOf, Cluster, clusters, Item, Level, levelOf, place } from './density';
import Stamp from './Stamp';
import { useData, useMinute } from './store';
import { barBottom, FLOAT_BAR_H } from './TabBar';
import { C, F, isDark, periodCell, sizeCell, themed, windCell } from './theme';

type Mode = 'houle' | 'periode' | 'vent';
const START: Region = { latitude: 44.6, longitude: -3.2, latitudeDelta: 9.5, longitudeDelta: 9.5 };
const PLAN: MapType = Platform.OS === 'ios' ? 'mutedStandard' : 'standard';
const SAT: MapType = 'hybrid';
// clé du fond renouvelée (v2) : tout le monde repart sur le plan épuré, plus lisible que le satellite sous les pastilles
const K = { region: 'houlalah.map.region', type: 'houlalah.mapType.v2', mode: 'houlalah.map.mode' };
let memRegion: Region | null = null;   // zone gardée pendant la vie de l'appli (retour d'une fiche, changement d'onglet)

// tailles des repères (px) : pastille simple selon la donnée, pastille détaillée, point de bouée, étiquette de bouée
const COMPACT: Record<Mode, { w: number; h: number }> = { houle: { w: 96, h: 32 }, periode: { w: 88, h: 32 }, vent: { w: 104, h: 32 } };
const DETAIL = { w: 124, h: 46 };
const BUOY_DOT = { w: 18, h: 18 };
const BUOY_LAB = { w: 88, h: 22, dy: 22 };

export default function MapScreen() {
  const { index: idx, offline, isFav, favs } = useData();
  const index = idx!;
  const minute = useMinute();
  const ins = useSafeAreaInsets();
  const map = useRef<MapView>(null);
  const [reg, setReg] = useState<Region>(memRegion || START);
  const [type, setType] = useState<MapType>(PLAN);
  const [mode, setModeState] = useState<Mode>('houle');
  const [me, setMe] = useState<{ lat: number; lon: number } | null>(null);
  const [width, setWidth] = useState(393);

  useEffect(() => {
    AsyncStorage.multiGet([K.region, K.type, K.mode]).then(([[, r], [, t], [, m]]) => {
      if (t === 'sat') setType(SAT);
      if (m === 'periode' || m === 'vent') setModeState(m);
      if (!memRegion && r) { try { const x = JSON.parse(r); if (x && x.latitude) { memRegion = x; setReg(x); map.current?.animateToRegion(x, 0); } } catch {} }
    }).catch(() => {});
  }, []);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onRegion = (r: Region) => {
    memRegion = r; setReg(r);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => AsyncStorage.setItem(K.region, JSON.stringify(r)).catch(() => {}), 800);
  };
  const setMode = (m: Mode) => { if (m === mode) return; Haptics.selectionAsync().catch(() => {}); setModeState(m); AsyncStorage.setItem(K.mode, m).catch(() => {}); };
  const toggleType = () => { const n = type === SAT ? PLAN : SAT; Haptics.selectionAsync().catch(() => {}); setType(n); AsyncStorage.setItem(K.type, n === SAT ? 'sat' : 'plan').catch(() => {}); };
  const sat = type === SAT, dark = isDark();

  // niveau et palier de zoom, avec hystérésis (src/density.ts) : un déplacement de la carte ne recalcule rien
  const lvl = useRef<Level>(levelOf(reg.longitudeDelta)), bkt = useRef<number>(bucketOf(reg.longitudeDelta));
  lvl.current = levelOf(reg.longitudeDelta, lvl.current);
  bkt.current = bucketOf(reg.longitudeDelta, bkt.current);
  const level = lvl.current, bucket = bkt.current;

  const val = useCallback((s: SpotLite) => (mode === 'vent' ? s.now.wind : mode === 'periode' ? s.now.tp : s.now.hs), [mode]);
  const fresh = useMemo(() => Object.fromEntries(index.buoys.map(b => [b.id, freshOf(b)])), [index, minute]);   // eslint-disable-line react-hooks/exhaustive-deps
  const freshKey = Object.values(fresh).join('');

  // placement : priorité aux favoris puis à la plus forte valeur ; les points des bouées sont des obstacles réservés
  const placed = useMemo(() => {
    const px = width / Math.pow(2, bucket / 2);
    if (level === 'far') {
      const cl = clusters(index.spots, val);
      const items: Item[] = cl.map(c => ({ id: c.region, lat: c.lat, lon: c.lon, prio: c.n, sizes: [{ w: 132, h: 46 }, { w: 70, h: 30 }] }));
      return { px, cl, at: place(items, px, 4) };
    }
    const shown = index.buoys.filter(b => fresh[b.id] !== 'off');
    const obstacles: Item[] = shown.map(b => ({ id: `o:${b.id}`, lat: b.lat, lon: b.lon, prio: 0, sizes: [BUOY_DOT] }));
    const items: Item[] = index.spots.map(s => ({
      id: `s:${s.slug}`, lat: s.lat, lon: s.lon, prio: (favs.includes(s.slug) ? 1000 : 0) + (val(s) ?? 0),
      sizes: level === 'near' ? [DETAIL, COMPACT[mode]] : [COMPACT[mode]],
    }));
    shown.forEach(b => items.push({ id: `b:${b.id}`, lat: b.lat, lon: b.lon, prio: -1, sizes: [BUOY_LAB] }));
    return { px, cl: [] as Cluster[], at: place(items, px, 3, obstacles) };
  }, [index, level, bucket, mode, width, favs, val, freshKey]);   // eslint-disable-line react-hooks/exhaustive-deps

  // aspect changé (niveau, palier, donnée, thème, fraîcheur) : les repères se redessinent 0,7 s puis se figent
  const [track, setTrack] = useState(true);
  useEffect(() => { setTrack(true); const t = setTimeout(() => setTrack(false), 700); return () => clearTimeout(t); }, [placed, dark, sat]);

  // toucher : un seul par repère (onPress du repère, onMarkerPress en secours), anti-doublon 600 ms
  const last = useRef(0);
  const open = useCallback((id: string) => {
    const now = Date.now(); if (now - last.current < 600) return; last.current = now;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    if (id.startsWith('b:')) { const b = index.buoys.find(x => x.id === id.slice(2)); if (b) router.push({ pathname: '/bouee/[slug]', params: { slug: b.slug } }); }
    else if (id.startsWith('s:')) router.push({ pathname: '/spot/[slug]', params: { slug: id.slice(2) } });
  }, [index]);
  const zoomTo = useCallback((c: Cluster) => {
    Haptics.selectionAsync().catch(() => {});
    const [la0, lo0, la1, lo1] = c.bounds, d = Math.max(0.6, (la1 - la0) * 1.4, (lo1 - lo0) * 1.4);
    map.current?.animateToRegion({ latitude: (la0 + la1) / 2, longitude: (lo0 + lo1) / 2, latitudeDelta: d, longitudeDelta: d }, 550);
  }, []);

  // Me localiser : permission demandée seulement à ce toucher ; refus = message clair, la carte reste utilisable
  const locate = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') { Alert.alert('Position non autorisée', 'Déplacez la carte ou cherchez un spot. Vous pouvez autoriser la position dans les Réglages de l’iPhone.'); return; }
      const p = (await Location.getLastKnownPositionAsync()) ?? (await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }));
      const pos = { lat: p.coords.latitude, lon: p.coords.longitude };
      setMe(pos);
      map.current?.animateToRegion({ latitude: pos.lat, longitude: pos.lon, latitudeDelta: 0.5, longitudeDelta: 0.5 }, 650);
    } catch { Alert.alert('Position indisponible', 'Réessayez dans un instant, ou cherchez un spot.'); }
  };
  const near = useMemo(() => {
    if (!me) return null;
    const sp = index.spots.map(s => ({ s, k: hav({ lat: me.lat, lon: me.lon }, spotPoint(s)) })).sort((a, b) => a.k - b.k).slice(0, 2);
    return { spots: sp, buoy: sp[0] ? refBuoy(index.buoys, sp[0].s) : null };
  }, [me, index]);

  const markers = useMemo(() => {
    const { at, cl } = placed;
    if (level === 'far') {
      return [
        ...cl.map(c => <ClusterMark key={`r:${c.region}`} c={c} mode={mode} big={at[c.region] === 0} track={track} onPress={() => zoomTo(c)} />),
        ...index.buoys.filter(b => fresh[b.id] !== 'off').map(b => <BuoyMark key={`b:${b.id}`} b={b} f={fresh[b.id]} label={false} track={track} onPress={() => open(`b:${b.id}`)} />),
      ];
    }
    return [
      ...index.spots.map(s => <SpotMark key={`s:${s.slug}`} s={s} mode={mode} size={at[`s:${s.slug}`]} detail={level === 'near'} fav={isFav(s.slug)} track={track} onPress={() => open(`s:${s.slug}`)} />),
      ...index.buoys.filter(b => fresh[b.id] !== 'off').map(b => <BuoyMark key={`b:${b.id}`} b={b} f={fresh[b.id]} label={at[`b:${b.id}`] === 0} track={track} onPress={() => open(`b:${b.id}`)} />),
    ];
  }, [placed, level, mode, track, index, fresh, isFav, open, zoomTo]);   // eslint-disable-line react-hooks/exhaustive-deps

  const bottom = barBottom(ins.bottom) + FLOAT_BAR_H + 8;
  return (
    <View style={StyleSheet.absoluteFill} onLayout={e => setWidth(e.nativeEvent.layout.width)}>
      <MapView ref={map} style={StyleSheet.absoluteFill} initialRegion={memRegion || START} onRegionChangeComplete={onRegion} mapType={type}
        userInterfaceStyle={dark ? 'dark' : 'light'} showsUserLocation={!!me} showsMyLocationButton={false}
        mapPadding={{ top: ins.top + 60, bottom: bottom + 50, left: 0, right: 0 }} onMarkerPress={e => { const id = e.nativeEvent.id; if (id && !id.startsWith('r:')) open(id); }}
        rotateEnabled={false} pitchEnabled={false} showsPointsOfInterests={false} showsBuildings={false} showsCompass={false} toolbarEnabled={false}>
        {markers}
      </MapView>

      <Svg style={[st.fade, { height: ins.top + 80 }]} pointerEvents="none">
        <Defs><LinearGradient id="g" x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor={C.bg} stopOpacity={sat ? 0.5 : 0.9} /><Stop offset="1" stopColor={C.bg} stopOpacity={0} /></LinearGradient></Defs>
        <Rect width="100%" height="100%" fill="url(#g)" />
      </Svg>

      <View style={[st.top, { top: ins.top + 6 }]}>
        <Pressable onPress={() => router.push('/recherche')} style={({ pressed }) => [st.search, pressed && st.pressed]} accessibilityRole="search" accessibilityLabel="Rechercher un spot, une bouée, une région">
          <Svg width={18} height={18} viewBox="0 0 24 24"><Circle cx={11} cy={11} r={6.5} stroke={C.ink2} strokeWidth={2} fill="none" /><Path d="M16 16l4.5 4.5" stroke={C.ink2} strokeWidth={2} strokeLinecap="round" /></Svg>
          <Text style={st.searchT}>Spot, bouée, région…</Text>
        </Pressable>
        <Pressable onPress={toggleType} style={({ pressed }) => [st.round, pressed && st.pressed]} accessibilityLabel={sat ? 'Passer au plan' : 'Passer en vue satellite'}>
          <Svg width={21} height={21} viewBox="0 0 24 24">
            <Path d="M12 3 2.5 8 12 13l9.5-5z" stroke={C.ink} strokeWidth={1.8} strokeLinejoin="round" fill={sat ? C.ink : 'none'} />
            <Path d="m2.5 12.5 9.5 5 9.5-5M2.5 16.5l9.5 5 9.5-5" stroke={C.ink} strokeWidth={1.8} strokeLinejoin="round" fill="none" />
          </Svg>
        </Pressable>
      </View>
      <View style={[st.when, { top: ins.top + 62 }]} pointerEvents="none"><Stamp t={index.spots[0]?.now.t} /></View>

      {near && (
        <View style={[st.near, { bottom: bottom + 54 }]}>
          {near.spots.map(({ s, k }) => {
            const wc = windCat(s.now.wind, s.now.wdir, s.ori);
            return (
              <Pressable key={s.slug} onPress={() => open(`s:${s.slug}`)} style={({ pressed }) => [st.nearCard, pressed && st.pressed]} accessibilityLabel={`${s.name}, à ${Math.round(k)} kilomètres`}>
                <View style={st.nearHd}><Text style={st.nearN} numberOfLines={1}>{s.name}</Text><Text style={st.nearK}>{k < 1 ? '< 1' : Math.round(k)} km</Text></View>
                <Text style={st.nearV}>{fr(s.now.hs)}<Text style={st.nearU}> m</Text><Text style={st.nearS}>  {s.now.tp != null ? Math.round(s.now.tp) + ' s' : ''} {sector(s.now.dir)}</Text></Text>
                <Text style={st.nearW} numberOfLines={1}>vent {s.now.wind ?? '—'} km/h{wc ? ` · ${WIND_WORD[wc]}` : ''}</Text>
              </Pressable>
            );
          })}
          {near.buoy && <NearBuoy b={near.buoy.b} onPress={() => open(`b:${near.buoy!.b.id}`)} />}
          <Pressable onPress={() => setMe(null)} style={st.nearX} hitSlop={8} accessibilityLabel="Fermer « Autour de vous »"><Text style={st.nearXT}>×</Text></Pressable>
        </View>
      )}

      {/* une seule rangée au-dessus de la pilule : donnée affichée + me localiser (au lieu de deux étages) */}
      <View style={[st.row, { bottom }]}>
        <View style={st.seg}>
          {(['houle', 'periode', 'vent'] as Mode[]).map(m => (
            <Pressable key={m} onPress={() => setMode(m)} style={[st.segB, mode === m && st.segOn]} accessibilityRole="button" accessibilityState={{ selected: mode === m }}>
              <Text style={[st.segT, mode === m && st.segTOn]}>{m === 'houle' ? 'Houle' : m === 'periode' ? 'Période' : 'Vent'}</Text>
            </Pressable>
          ))}
        </View>
        <Pressable onPress={locate} style={({ pressed }) => [st.round, st.loc, me && st.roundOn, pressed && st.pressed]} accessibilityLabel="Me localiser">
          <Svg width={19} height={19} viewBox="0 0 24 24"><Path d="M20.5 3.5 3.5 10.6l7 2.4 2.4 7z" stroke={me ? C.onNight : C.ink} strokeWidth={1.9} strokeLinejoin="round" fill={me ? C.onNight : 'none'} /></Svg>
        </Pressable>
      </View>
      {offline && <View pointerEvents="none" style={[st.offline, { bottom: bottom + 52 }]}><Text style={st.offlineT}>Hors connexion : fond de carte peut-être absent</Text></View>}
    </View>
  );
}

const cellOf = (mode: Mode, n: SpotLite['now']) => (mode === 'vent' ? windCell(n.wind) : mode === 'periode' ? periodCell(n.tp) : sizeCell(n.hs));
const catCol = (c: ReturnType<typeof windCat>) => (c === 'offshore' || c === 'side-off' ? C.off : c === 'de côté' ? C.side : c === 'onshore' ? C.on : C.ink3);

/** Valeurs d'un spot avec leurs unités : houle = hauteur + période + direction (D5) ; vent = force, direction, orientation. */
function Values({ mode, s }: { mode: Mode; s: SpotLite }) {
  const n = s.now, wc = windCat(n.wind, n.wdir, s.ori);
  if (mode === 'vent') return (
    <View style={st.vals}><Arrow dir={n.wdir} size={10} color={C.ink} /><Text style={st.v}>{n.wind ?? '—'}<Text style={st.u}> km/h</Text></Text>{!!wc && <View style={[st.wdot, { backgroundColor: catCol(wc) }]} />}</View>
  );
  if (mode === 'periode') return (
    <View style={st.vals}><Text style={st.v}>{n.tp != null ? Math.round(n.tp) : '—'}<Text style={st.u}> s</Text></Text><Text style={st.v2}>{fr(n.hs)} m</Text></View>
  );
  return (
    <View style={st.vals}><Arrow dir={n.dir} size={10} color={C.ink} /><Text style={st.v}>{fr(n.hs)}<Text style={st.u}> m</Text></Text><Text style={st.v2}>{n.tp != null ? `${Math.round(n.tp)} s` : ''}</Text></View>
  );
}

function SpotMark({ s, mode, size, detail, fav, track, onPress }: { s: SpotLite; mode: Mode; size: number; detail: boolean; fav: boolean; track: boolean; onPress: () => void }) {
  const n = s.now, wc = windCat(n.wind, n.wdir, s.ori), bg = cellOf(mode, n);
  const label = mode === 'vent'
    ? `${s.name}, vent ${n.wind ?? '—'} kilomètres heure, ${sector(n.wdir)}${wc ? ', ' + WIND_WORD[wc] : ''}`
    : `${s.name}, houle ${fr(n.hs)} mètre, ${n.tp != null ? Math.round(n.tp) + ' secondes' : ''}, ${sector(n.dir)}`;
  const big = size === 0 && detail, pill = size === 0 || (detail && size === 1);
  return (
    <Marker identifier={`s:${s.slug}`} coordinate={{ latitude: s.lat, longitude: s.lon }} onPress={onPress} tracksViewChanges={track}
      anchor={{ x: 0.5, y: 0.5 }} zIndex={big ? 6 : pill ? 5 : 1} accessibilityLabel={label}>
      {big ? (
        <View style={[st.detail, { backgroundColor: bg }]}>
          <Text style={st.dName} numberOfLines={1}>{s.name}</Text>
          <Values mode={mode} s={s} />
          {fav && <View style={st.fav} />}
        </View>
      ) : pill ? (
        <View style={[st.pill, { backgroundColor: bg }]}><Values mode={mode} s={s} />{fav && <View style={st.fav} />}</View>
      ) : (
        <View style={st.hit}><View style={[st.dot, { backgroundColor: bg }, fav && st.dotFav]} /></View>
      )}
    </Marker>
  );
}

function ClusterMark({ c, mode, big, track, onPress }: { c: Cluster; mode: Mode; big: boolean; track: boolean; onPress: () => void }) {
  const u = mode === 'vent' ? ' km/h' : mode === 'periode' ? ' s' : ' m';
  const f = (v: number | null) => (v == null ? '—' : mode === 'houle' ? fr(v) : String(Math.round(v)));
  const range = c.min == null ? '—' : f(c.min) === f(c.max) ? `${f(c.max)}${u}` : `${f(c.min)}–${f(c.max)}${u}`;
  const bg = mode === 'vent' ? windCell(c.max) : mode === 'periode' ? periodCell(c.max) : sizeCell(c.max);
  return (
    <Marker identifier={`r:${c.region}`} coordinate={{ latitude: c.lat, longitude: c.lon }} onPress={onPress} tracksViewChanges={track}
      anchor={{ x: 0.5, y: 0.5 }} zIndex={5} accessibilityLabel={`${regionName(c.region)}, ${c.n} spots, ${range}. Toucher pour zoomer`}>
      <View style={[st.cluster, !big && st.clusterS]}>
        <View style={[st.cBand, { backgroundColor: bg }]} />
        <View>
          {big && <Text style={st.cName} numberOfLines={1}>{regionName(c.region)} <Text style={st.cN}>· {c.n}</Text></Text>}
          <Text style={st.cVal}>{range}</Text>
        </View>
      </View>
    </Marker>
  );
}

function BuoyMark({ b, f, label, track, onPress }: { b: Buoy; f: string; label: boolean; track: boolean; onPress: () => void }) {
  const ring = f === 'live' ? C.liveOnBuoy : f === 'recent' ? C.measureOnBuoy : C.onBuoy2;
  return (
    <Marker identifier={`b:${b.id}`} coordinate={{ latitude: b.lat, longitude: b.lon }} onPress={onPress} tracksViewChanges={track}
      anchor={{ x: 0.5, y: label ? 9 / 43 : 0.5 }} zIndex={7}
      accessibilityLabel={`Bouée ${b.name}, mesure ${fr(b.hs)} mètre${perTxt(b) ? ', ' + perTxt(b) : ''}, ${f === 'live' ? 'en direct' : f === 'recent' ? 'récente' : 'ancienne'}`}>
      <View style={[st.buWrap, f === 'old' && { opacity: 0.55 }]}>
        <View style={[st.buRing, { borderColor: ring }]}><View style={st.buCore} /></View>
        {label && <View style={st.buLab}><Text style={st.buLabT} numberOfLines={1}>{fr(b.hs)} m{perTxt(b) ? ` · ${perTxt(b)}` : ''}</Text></View>}
      </View>
    </Marker>
  );
}

function NearBuoy({ b, onPress }: { b: Buoy; onPress: () => void }) {
  const f = freshOf(b);
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [st.nearCard, st.nearBuoy, pressed && st.pressed]} accessibilityLabel={`Bouée ${b.name}`}>
      <View style={st.nearHd}><View style={[st.ndot, { backgroundColor: f === 'live' ? C.liveOnBuoy : C.onBuoy2 }]} /><Text style={[st.nearN, { color: C.measureOnBuoy }]} numberOfLines={1}>{b.name}</Text></View>
      <Text style={[st.nearV, { color: C.measureOnBuoy }]}>{fr(b.hs)}<Text style={st.nearU}> m</Text></Text>
      <Text style={[st.nearW, { color: C.onBuoy }]} numberOfLines={1}>{perTxt(b)}{perTxt(b) ? ' · ' : ''}mesure</Text>
    </Pressable>
  );
}

const glass = () => ({ backgroundColor: C.glass, shadowColor: '#0b1b26', shadowOpacity: 0.16, shadowRadius: 14, shadowOffset: { width: 0, height: 6 }, elevation: 6 }) as const;
const shadow = () => ({ shadowColor: '#0b1b26', shadowOpacity: 0.25, shadowRadius: 4, shadowOffset: { width: 0, height: 2 }, elevation: 3 }) as const;

const st = themed(() => StyleSheet.create({
  pill: { flexDirection: 'row', alignItems: 'center', height: 30, paddingHorizontal: 9, borderRadius: 15, justifyContent: 'center', borderWidth: 2, borderColor: C.card, ...shadow() },
  detail: { minWidth: 96, maxWidth: 140, paddingHorizontal: 10, paddingTop: 4, paddingBottom: 5, borderRadius: 14, borderWidth: 2, borderColor: C.card, ...shadow() },
  dName: { fontFamily: F.tX, fontSize: 11, color: C.ink, marginBottom: 1 },
  vals: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  v: { fontFamily: F.num, fontSize: 12.5, color: C.ink, letterSpacing: -0.4 },
  u: { fontFamily: F.tX, fontSize: 9.5, letterSpacing: 0 },
  v2: { fontFamily: F.tX, fontSize: 10.5, color: C.cellU },
  wdot: { width: 8, height: 8, borderRadius: 4, borderWidth: 1, borderColor: C.card },
  fav: { position: 'absolute', top: -4, right: -4, width: 10, height: 10, borderRadius: 5, backgroundColor: C.night, borderWidth: 1.5, borderColor: C.card },
  hit: { width: 30, height: 30, alignItems: 'center', justifyContent: 'center' },
  dot: { width: 11, height: 11, borderRadius: 6, borderWidth: 2, borderColor: C.card, ...shadow() },
  dotFav: { borderColor: C.night },
  cluster: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingLeft: 6, paddingRight: 12, height: 44, borderRadius: 22, backgroundColor: C.card, ...shadow() },
  clusterS: { height: 30, paddingRight: 10 },
  cBand: { width: 8, alignSelf: 'stretch', marginVertical: 6, borderRadius: 4 },
  cName: { fontFamily: F.tX, fontSize: 11.5, color: C.ink },
  cN: { fontFamily: F.tB, color: C.ink3 },
  cVal: { fontFamily: F.num, fontSize: 12.5, color: C.ink, letterSpacing: -0.4 },
  buWrap: { alignItems: 'center', gap: 3 },
  buRing: { width: 18, height: 18, borderRadius: 9, backgroundColor: C.buoySurface, borderWidth: 3, alignItems: 'center', justifyContent: 'center', ...shadow() },
  buCore: { width: 6, height: 6, borderRadius: 3, backgroundColor: C.measureOnBuoy },
  buLab: { paddingHorizontal: 7, height: 22, borderRadius: 8, backgroundColor: C.buoySurface, justifyContent: 'center' },
  buLabT: { fontFamily: F.num, fontSize: 10.5, color: C.measureOnBuoy },
  fade: { position: 'absolute', top: 0, left: 0, right: 0 },
  top: { position: 'absolute', left: 16, right: 16, flexDirection: 'row', gap: 10 },
  search: { flex: 1, height: 48, borderRadius: 24, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 16, ...glass() },
  searchT: { fontFamily: F.t, fontSize: 15, color: C.ink2 },
  round: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', ...glass() },
  roundOn: { backgroundColor: C.night },
  pressed: { opacity: 0.7, transform: [{ scale: 0.97 }] },
  when: { position: 'absolute', left: 16 },
  row: { position: 'absolute', left: 22, right: 22, height: 44, flexDirection: 'row', gap: 10 },
  seg: { flex: 1, height: 44, borderRadius: 22, padding: 3, flexDirection: 'row', gap: 2, ...glass() },
  segB: { flex: 1, borderRadius: 19, alignItems: 'center', justifyContent: 'center' },
  segOn: { backgroundColor: C.night },
  segT: { fontFamily: F.tB, fontSize: 13, color: C.ink2 },
  segTOn: { fontFamily: F.tX, color: C.onNight },
  loc: { width: 44, height: 44, borderRadius: 22 },
  offline: { position: 'absolute', alignSelf: 'center', paddingHorizontal: 12, height: 26, borderRadius: 13, backgroundColor: C.warnBg, justifyContent: 'center' },
  offlineT: { fontFamily: F.tX, fontSize: 11.5, color: C.warn },
  near: { position: 'absolute', left: 12, right: 12, height: 100, flexDirection: 'row', gap: 8 },
  nearCard: { flex: 1, minWidth: 0, borderRadius: 22, padding: 11, justifyContent: 'space-between', ...glass(), backgroundColor: C.card },
  nearBuoy: { backgroundColor: C.buoySurface },
  nearHd: { flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'space-between' },
  nearN: { flexShrink: 1, fontFamily: F.tX, fontSize: 13.5, color: C.ink },
  nearK: { fontFamily: F.tB, fontSize: 11, color: C.ink2 },
  nearV: { fontFamily: F.numX, fontSize: 20, color: C.ink, letterSpacing: -0.8 },
  nearU: { fontFamily: F.tB, fontSize: 11, letterSpacing: 0 },
  nearS: { fontFamily: F.tX, fontSize: 11.5, color: C.ink2, letterSpacing: 0 },
  nearW: { fontFamily: F.tB, fontSize: 11, color: C.ink2 },
  nearX: { position: 'absolute', top: -12, right: -4, width: 26, height: 26, borderRadius: 13, backgroundColor: C.night, alignItems: 'center', justifyContent: 'center' },
  nearXT: { color: C.onNight, fontFamily: F.tX, fontSize: 15, marginTop: -2 },
  ndot: { width: 8, height: 8, borderRadius: 4 },
}));
