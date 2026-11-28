/** Accueil : la carte seule (chantier #8, maquette A validée). Pas de panneau permanent (D13) : un toucher sur un repère ouvre
 *  sa fiche en panneau natif, la carte reste montée derrière. Commandes en bas, dans la zone du pouce : donnée affichée
 *  (Houle / Période / Vent), me localiser ; recherche et fond de carte en haut.
 *  Repères : houle = hauteur + période + direction ensemble (D5) ; vent = force, direction et orientation par rapport à la plage.
 *  Performance : repères figés (tracksViewChanges=false), regroupement recalculé seulement quand le niveau de zoom change,
 *  aucune animation sur la carte. La zone, le fond et la donnée affichée sont mémorisés.
 *  L'index est garanti par la mise en page des onglets (chargement avant d'afficher la carte). */
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
import { Buoy, freshOf, fr, hav, JOURS, perTxt, refBuoy, sector, SpotLite, spotPoint, windCat } from './data';
import { useData, useMinute } from './store';
import { barBottom, FLOAT_BAR_H } from './TabBar';
import { C, F, isDark, periodCell, sizeCell, themed, windCell } from './theme';
import { partsIn, tMs } from './time';

type Mode = 'houle' | 'periode' | 'vent';
const START: Region = { latitude: 44.6, longitude: -3.2, latitudeDelta: 9.5, longitudeDelta: 9.5 };
const PLAN: MapType = Platform.OS === 'ios' ? 'mutedStandard' : 'standard';
const SAT: MapType = 'hybrid';
const K = { region: 'houlalah.map.region', type: 'houlalah.mapType', mode: 'houlalah.map.mode' };
let memRegion: Region | null = null;   // garde la zone pendant la vie de l'appli (retour d'une fiche, changement d'onglet)

const windCol = () => ({ offshore: C.off, 'side-off': C.off, 'de côté': C.side, onshore: C.on, lisse: C.ink3 }) as Record<string, string>;

export default function MapScreen() {
  const data = useData();
  const index = data.index!;
  const { offline, isFav } = data;
  useMinute();   // fraîcheur des bouées recalculée chaque minute
  const ins = useSafeAreaInsets();
  const map = useRef<MapView>(null);
  const [reg, setReg] = useState<Region>(memRegion || START);
  const [type, setType] = useState<MapType>(PLAN);
  const [mode, setModeState] = useState<Mode>('houle');
  const [me, setMe] = useState<{ lat: number; lon: number } | null>(null);
  const [size, setSize] = useState({ w: 1, h: 1 });

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

  // Une pastille chiffrée par case de grille (bouées d'abord, puis la plus forte valeur de la donnée affichée) ; les autres
  // spots sont de petits points, qui deviennent des pastilles en zoomant. Recalcul seulement au changement de niveau de zoom.
  const bucket = Math.round(Math.log2(reg.latitudeDelta) * 2);
  const { labeled, buoyLab } = useMemo(() => {
    const cell = Math.pow(2, bucket / 2) / 14, taken = new Set<string>(), labeled = new Set<string>(), buoyLab = new Set<string>();
    const free = (lat: number, lon: number) => { const k = `${Math.round(lat / cell)}:${Math.round(lon / (cell * 1.6))}`; if (taken.has(k)) return false; taken.add(k); return true; };
    [...index.buoys].filter(b => freshOf(b) !== 'off').sort((a, b) => tMs(b.time) - tMs(a.time)).forEach(b => { if (free(b.lat, b.lon)) buoyLab.add(b.id); });
    const v = (s: SpotLite) => (mode === 'vent' ? s.now.wind : mode === 'periode' ? s.now.tp : s.now.hs) ?? 0;
    [...index.spots].sort((a, b) => v(b) - v(a)).forEach(s => { if (free(s.lat, s.lon)) labeled.add(s.slug); });
    return { labeled, buoyLab };
  }, [index, bucket, mode]);

  // Toucher : par le repère (onMarkerPress, le plus fiable sur iPhone) ou, en secours, le repère le plus proche du toucher.
  const last = useRef(0);
  const open = useCallback((id: string) => {
    const now = Date.now(); if (now - last.current < 600) return; last.current = now;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    if (id.startsWith('b:')) { const b = index.buoys.find(x => x.id === id.slice(2)); if (b) router.push({ pathname: '/bouee/[slug]', params: { slug: b.slug } }); }
    else router.push({ pathname: '/spot/[slug]', params: { slug: id.slice(2) } });
  }, [index]);
  const tapMap = (c: { latitude: number; longitude: number }) => {
    const merc = (la: number) => Math.log(Math.tan(Math.PI / 4 + (la * Math.PI) / 360));
    const top = merc(reg.latitude + reg.latitudeDelta / 2), bot = merc(reg.latitude - reg.latitudeDelta / 2), west = reg.longitude - reg.longitudeDelta / 2;
    const px = (la: number, lo: number) => [((lo - west) / reg.longitudeDelta) * size.w, ((top - merc(la)) / (top - bot)) * size.h];
    const [tx, ty] = px(c.latitude, c.longitude);
    let best: { id: string; d: number } | null = null;
    const look = (id: string, la: number, lo: number, r: number, bonus = 0) => { const [x, y] = px(la, lo), d = Math.hypot(x - tx, y - ty) - bonus; if (d < r && (!best || d < best.d)) best = { id, d }; };
    index.buoys.forEach(b => look(`b:${b.id}`, b.lat, b.lon, 32, 8));
    index.spots.forEach(s => look(`s:${s.slug}`, s.lat, s.lon, labeled.has(s.slug) ? 32 : 18));
    if (best) open((best as { id: string }).id);
  };

  // Me localiser : la permission n'est demandée qu'à ce toucher ; refus = message clair, la carte reste utilisable.
  const locate = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') { Alert.alert('Position non autorisée', 'Déplacez la carte ou cherchez un spot. Vous pouvez autoriser la position dans les Réglages de l’iPhone.'); return; }
      const p = (await Location.getLastKnownPositionAsync()) ?? (await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }));
      const pos = { lat: p.coords.latitude, lon: p.coords.longitude };
      setMe(pos);
      map.current?.animateToRegion({ latitude: pos.lat, longitude: pos.lon, latitudeDelta: 0.9, longitudeDelta: 0.9 }, 650);
    } catch { Alert.alert('Position indisponible', 'Réessayez dans un instant, ou cherchez un spot.'); }
  };

  // « Autour de vous » (à la demande) : les 2 spots les plus proches et la bouée de référence du plus proche.
  const near = useMemo(() => {
    if (!me) return null;
    const sp = index.spots.map(s => ({ s, k: hav({ lat: me.lat, lon: me.lon }, spotPoint(s)) })).sort((a, b) => a.k - b.k).slice(0, 2);
    return { spots: sp, buoy: sp[0] ? refBuoy(index.buoys, sp[0].s) : null };
  }, [me, index]);

  const t = index.spots[0]?.now.t, tp = t ? partsIn(tMs(t), 'Europe/Paris') : null;
  const bottom = barBottom(ins.bottom) + FLOAT_BAR_H + 10;
  const col = windCol();

  return (
    <View style={StyleSheet.absoluteFill} onLayout={e => setSize({ w: e.nativeEvent.layout.width, h: e.nativeEvent.layout.height })}>
      <MapView ref={map} style={StyleSheet.absoluteFill} initialRegion={memRegion || START} onRegionChangeComplete={onRegion} mapType={type}
        userInterfaceStyle={dark ? 'dark' : 'light'} showsUserLocation={!!me} showsMyLocationButton={false}
        mapPadding={{ top: ins.top + 60, bottom: bottom + 60, left: 0, right: 0 }} onMarkerPress={e => open(e.nativeEvent.id)} onPress={e => tapMap(e.nativeEvent.coordinate)}
        rotateEnabled={false} pitchEnabled={false} showsPointsOfInterests={false} showsCompass={false} toolbarEnabled={false}>
        {index.spots.map(s => {
          const big = labeled.has(s.slug), n = s.now;
          const bg = mode === 'vent' ? windCell(n.wind) : mode === 'periode' ? periodCell(n.tp) : sizeCell(n.hs);
          const wc = windCat(n.wind, n.wdir, s.ori);
          const label = mode === 'vent'
            ? `${s.name}, vent ${n.wind ?? '—'} kilomètres heure, ${sector(n.wdir)}${wc ? ', ' + wc : ''}`
            : `${s.name}, houle ${fr(n.hs)} mètre, ${n.tp != null ? Math.round(n.tp) + ' secondes' : ''}, ${sector(n.dir)}`;
          return (
            <Marker key={`${s.slug}:${big ? 1 : 0}:${mode}:${dark ? 'd' : 'l'}`} identifier={`s:${s.slug}`} coordinate={{ latitude: s.lat, longitude: s.lon }}
              onPress={() => open(`s:${s.slug}`)} tracksViewChanges={false} anchor={{ x: 0.5, y: 0.5 }} zIndex={big ? 5 : 1} accessibilityLabel={label}>
              {big ? (
                <View style={[st.spot, { backgroundColor: bg }]}>
                  {mode !== 'periode' && <Arrow dir={mode === 'vent' ? n.wdir : n.dir} size={10} color={C.ink} />}
                  {mode === 'vent' ? (
                    <>
                      <Text style={st.spotT}>{n.wind ?? '—'}</Text>
                      {!!wc && <View style={[st.wdot, { backgroundColor: col[wc] }]} />}
                    </>
                  ) : mode === 'periode' ? (
                    <><Text style={st.spotT}>{n.tp != null ? Math.round(n.tp) : '—'}<Text style={st.spotU}> s</Text></Text><Text style={st.spotS}>{fr(n.hs)}</Text></>
                  ) : (
                    <><Text style={st.spotT}>{fr(n.hs)}</Text><Text style={st.spotS}>{n.tp != null ? `${Math.round(n.tp)} s` : ''}</Text></>
                  )}
                  {isFav(s.slug) && <View style={st.fav} />}
                </View>
              ) : (
                <View style={st.hit}><View style={[st.dotSpot, { backgroundColor: bg }]} /></View>
              )}
            </Marker>
          );
        })}
        {index.buoys.map(b => {
          const f = freshOf(b), lab = buoyLab.has(b.id);
          const ring = f === 'live' ? C.live : f === 'recent' ? '#f2c66b' : '#9aa4a8';
          return (
            <Marker key={`${b.id}:${lab ? 1 : 0}:${f}:${dark ? 'd' : 'l'}`} identifier={`b:${b.id}`} coordinate={{ latitude: b.lat, longitude: b.lon }}
              onPress={() => open(`b:${b.id}`)} tracksViewChanges={false} anchor={{ x: 0.5, y: lab ? 0.25 : 0.5 }} zIndex={10}
              accessibilityLabel={`Bouée ${b.name}, mesure ${fr(b.hs)} mètre${perTxt(b) ? ', ' + perTxt(b) : ''}, ${f === 'live' ? 'en direct' : f === 'off' ? 'muette' : 'pas en direct'}`}>
              <View style={[st.buWrap, (f === 'old' || f === 'off') && { opacity: 0.5 }]}>
                <View style={[st.buRing, { borderColor: ring }]}><View style={st.buCore} />{f === 'live' && <View style={st.buLive} />}</View>
                {lab && f !== 'off' && <View style={st.buLab}><Text style={st.buLabT}>{fr(b.hs)} m{perTxt(b) ? ` · ${perTxt(b)}` : ''}</Text></View>}
              </View>
            </Marker>
          );
        })}
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
      <View style={[st.when, { top: ins.top + 62 }]} pointerEvents="none">
        <Text style={st.whenT}>{tp ? `Prévision ${JOURS[tp.wd]} ${tp.h} h` : 'Prévision'}{offline ? ' · hors connexion' : ''}</Text>
      </View>

      <Pressable onPress={locate} style={({ pressed }) => [st.round, st.locate, { bottom: bottom + (near ? 172 : 66) }, me && st.roundOn, pressed && st.pressed]} accessibilityLabel="Me localiser">
        <Svg width={20} height={20} viewBox="0 0 24 24"><Path d="M20.5 3.5 3.5 10.6l7 2.4 2.4 7z" stroke={me ? C.onNight : C.ink} strokeWidth={1.9} strokeLinejoin="round" fill={me ? C.onNight : 'none'} /></Svg>
      </Pressable>

      {near && (
        <View style={[st.near, { bottom: bottom + 62 }]}>
          {near.spots.map(({ s, k }) => {
            const wc = windCat(s.now.wind, s.now.wdir, s.ori);
            return (
              <Pressable key={s.slug} onPress={() => open(`s:${s.slug}`)} style={({ pressed }) => [st.nearCard, pressed && st.pressed]} accessibilityLabel={`${s.name}, à ${Math.round(k)} kilomètres`}>
                <View style={st.nearHd}><Text style={st.nearN} numberOfLines={1}>{s.name}</Text><Text style={st.nearK}>{k < 1 ? '< 1' : Math.round(k)} km</Text></View>
                <Text style={st.nearV}>{fr(s.now.hs)}<Text style={st.nearU}> m</Text><Text style={st.nearS}>  {s.now.tp != null ? Math.round(s.now.tp) + ' s' : ''} {sector(s.now.dir)}</Text></Text>
                <Text style={st.nearW} numberOfLines={1}>vent {s.now.wind ?? '—'} {sector(s.now.wdir)}{wc ? ' · ' : ''}<Text style={{ color: wc ? col[wc] : C.ink2, fontFamily: F.tX }}>{wc ?? ''}</Text></Text>
              </Pressable>
            );
          })}
          {near.buoy && <NearBuoy b={near.buoy.b} onPress={() => open(`b:${near.buoy!.b.id}`)} />}
          <Pressable onPress={() => setMe(null)} style={st.nearX} hitSlop={8} accessibilityLabel="Fermer « Autour de vous »"><Text style={st.nearXT}>×</Text></Pressable>
        </View>
      )}

      <View style={[st.bar, { bottom }]}>
        {(['houle', 'periode', 'vent'] as Mode[]).map(m => (
          <Pressable key={m} onPress={() => setMode(m)} style={[st.seg, mode === m && st.segOn]} accessibilityRole="button" accessibilityState={{ selected: mode === m }}>
            <Text style={[st.segT, mode === m && st.segTOn]}>{m === 'houle' ? 'Houle' : m === 'periode' ? 'Période' : 'Vent'}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

function NearBuoy({ b, onPress }: { b: Buoy; onPress: () => void }) {
  const f = freshOf(b);
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [st.nearCard, st.nearBuoy, pressed && st.pressed]} accessibilityLabel={`Bouée ${b.name}`}>
      <View style={st.nearHd}><View style={[st.dot, { backgroundColor: f === 'live' ? '#2fc48a' : 'rgba(243,239,230,0.35)' }]} /><Text style={[st.nearN, { color: '#f2c66b' }]} numberOfLines={1}>{b.name}</Text></View>
      <Text style={[st.nearV, { color: '#f2c66b' }]}>{fr(b.hs)}<Text style={st.nearU}> m</Text></Text>
      <Text style={[st.nearW, { color: 'rgba(243,239,230,0.78)' }]} numberOfLines={1}>{perTxt(b)}{perTxt(b) ? ' · ' : ''}mesure</Text>
    </Pressable>
  );
}

const glass = () => ({ backgroundColor: C.glass, shadowColor: '#0b1b26', shadowOpacity: 0.18, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 6 }) as const;

const st = themed(() => StyleSheet.create({
  spot: { flexDirection: 'row', alignItems: 'center', gap: 4, minWidth: 44, height: 30, paddingHorizontal: 8, borderRadius: 15, justifyContent: 'center',
    borderWidth: 2, borderColor: C.card, shadowColor: '#0b1b26', shadowOpacity: 0.28, shadowRadius: 5, shadowOffset: { width: 0, height: 2 }, elevation: 3 },
  spotT: { fontFamily: F.num, fontSize: 12.5, color: C.ink, letterSpacing: -0.4 },
  spotU: { fontFamily: F.tX, fontSize: 10 },
  spotS: { fontFamily: F.tX, fontSize: 10.5, color: C.cellU },
  wdot: { width: 8, height: 8, borderRadius: 4, borderWidth: 1, borderColor: '#fffdf8' },
  fav: { position: 'absolute', top: -4, right: -4, width: 9, height: 9, borderRadius: 5, backgroundColor: '#0b1b26', borderWidth: 1.5, borderColor: '#fffdf8' },
  hit: { width: 26, height: 26, alignItems: 'center', justifyContent: 'center' },
  dotSpot: { width: 12, height: 12, borderRadius: 6, borderWidth: 2, borderColor: C.card, shadowColor: '#0b1b26', shadowOpacity: 0.3, shadowRadius: 3, shadowOffset: { width: 0, height: 1 }, elevation: 2 },
  buWrap: { alignItems: 'center', gap: 3 },
  buRing: { width: 22, height: 22, borderRadius: 11, backgroundColor: '#0b1b26', borderWidth: 3, alignItems: 'center', justifyContent: 'center',
    shadowColor: '#0b1b26', shadowOpacity: 0.3, shadowRadius: 4, shadowOffset: { width: 0, height: 2 }, elevation: 3 },
  buCore: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#f2c66b' },
  buLive: { position: 'absolute', right: -5, top: -5, width: 9, height: 9, borderRadius: 5, backgroundColor: '#2fc48a', borderWidth: 2, borderColor: '#0b1b26' },
  buLab: { paddingHorizontal: 7, height: 20, borderRadius: 7, backgroundColor: '#0b1b26', justifyContent: 'center' },
  buLabT: { fontFamily: F.num, fontSize: 10.5, color: '#f2c66b' },
  fade: { position: 'absolute', top: 0, left: 0, right: 0 },
  top: { position: 'absolute', left: 16, right: 16, flexDirection: 'row', gap: 10 },
  search: { flex: 1, height: 48, borderRadius: 24, flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 16, ...glass() },
  searchT: { fontFamily: F.t, fontSize: 15, color: C.ink2 },
  round: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', ...glass() },
  roundOn: { backgroundColor: C.night },
  pressed: { opacity: 0.7, transform: [{ scale: 0.97 }] },
  when: { position: 'absolute', left: 16, height: 26, borderRadius: 13, paddingHorizontal: 11, justifyContent: 'center', backgroundColor: C.glass },
  whenT: { fontFamily: F.tB, fontSize: 11.5, color: C.ink },
  locate: { position: 'absolute', right: 16 },
  bar: { position: 'absolute', left: 16, right: 16, height: 52, borderRadius: 26, padding: 4, flexDirection: 'row', gap: 2, ...glass() },
  seg: { flex: 1, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  segOn: { backgroundColor: C.night },
  segT: { fontFamily: F.tB, fontSize: 13.5, color: C.ink2 },
  segTOn: { fontFamily: F.tX, color: C.onNight },
  near: { position: 'absolute', left: 12, right: 12, height: 100, flexDirection: 'row', gap: 8 },
  nearCard: { flex: 1, minWidth: 0, borderRadius: 22, padding: 11, justifyContent: 'space-between', ...glass(), backgroundColor: C.card },
  nearBuoy: { backgroundColor: '#0b1b26' },
  nearHd: { flexDirection: 'row', alignItems: 'center', gap: 6, justifyContent: 'space-between' },
  nearN: { flexShrink: 1, fontFamily: F.tX, fontSize: 13.5, color: C.ink },
  nearK: { fontFamily: F.tB, fontSize: 11, color: C.ink2 },
  nearV: { fontFamily: F.numX, fontSize: 20, color: C.ink, letterSpacing: -0.8 },
  nearU: { fontFamily: F.tB, fontSize: 11, letterSpacing: 0 },
  nearS: { fontFamily: F.tX, fontSize: 11.5, color: C.ink2, letterSpacing: 0 },
  nearW: { fontFamily: F.tB, fontSize: 11, color: C.ink2 },
  nearX: { position: 'absolute', top: -12, right: -4, width: 26, height: 26, borderRadius: 13, backgroundColor: C.night, alignItems: 'center', justifyContent: 'center' },
  nearXT: { color: C.onNight, fontFamily: F.tX, fontSize: 15, marginTop: -2 },
  dot: { width: 8, height: 8, borderRadius: 4 },
}));
