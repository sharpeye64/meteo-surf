import AsyncStorage from '@react-native-async-storage/async-storage';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { MapType, Marker, Region } from 'react-native-maps';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Defs, LinearGradient, Path, Rect, Stop } from 'react-native-svg';
import Brand from './Brand';
import { ageH, Buoy, fr, Index, perTxt, SpotLite } from './data';
import { Pulse } from './Live';
import { FLOAT_BAR_H } from './TabBar';
import { C, F, isDark, sizeCell, themed } from './theme';

type Props = { index: Index; onSpot: (s: SpotLite) => void; onBuoy: (b: Buoy) => void };
const START: Region = { latitude: 44.6, longitude: -3.2, latitudeDelta: 9.5, longitudeDelta: 9.5 };
const PLAN: MapType = Platform.OS === 'ios' ? 'mutedStandard' : 'standard';
const SAT: MapType = 'hybrid';
const KEY = 'houlalah.mapType';

/** Flèche de houle : pointe vers où va la houle (direction d'où elle vient + 180°). */
const arrow = (dir: number | null | undefined) => (dir == null ? null : { transform: [{ rotate: `${(dir + 180) % 360}deg` }] });

/** Carte plein écran, commandes flottantes « verre » (inspiration : applis de cartes marines). */
export default function MapScreen({ index, onSpot, onBuoy }: Props) {
  const ins = useSafeAreaInsets();
  const map = useRef<MapView>(null);
  const [reg, setReg] = useState<Region>(START);
  const [type, setType] = useState<MapType>(SAT);
  const [legend, setLegend] = useState(false);
  useEffect(() => { AsyncStorage.getItem(KEY).then(v => { if (v === 'plan') setType(PLAN); }).catch(() => {}); }, []);
  const sat = type === SAT;
  const toggleType = () => { const n = sat ? PLAN : SAT; setType(n); AsyncStorage.setItem(KEY, n === SAT ? 'sat' : 'plan').catch(() => {}); };

  const live = index.buoys.filter(b => ageH(b.time) < 2).length;
  const bottom = Math.max(ins.bottom, 10) + FLOAT_BAR_H + 14;

  // Tous les spots sont toujours sur la carte. Une seule pastille chiffrée par case de la grille (bouées d'abord, puis les
  // plus grosses houles) ; les autres spots sont de petits points de couleur, qui deviennent des pastilles en zoomant.
  const { labeled, buoyLab } = useMemo(() => {
    const cell = reg.latitudeDelta / 16, taken = new Set<string>(), labeled = new Set<string>(), buoyLab = new Set<string>();
    const free = (lat: number, lon: number) => {
      const k = `${Math.round(lat / cell)}:${Math.round(lon / (cell * 1.6))}`;
      if (taken.has(k)) return false; taken.add(k); return true;
    };
    [...index.buoys].sort((a, b) => ageH(a.time) - ageH(b.time)).forEach(b => { if (free(b.lat, b.lon)) buoyLab.add(b.id); });
    [...index.spots].sort((a, b) => (b.now.hs ?? 0) - (a.now.hs ?? 0)).forEach(s => { if (free(s.lat, s.lon)) labeled.add(s.slug); });
    return { labeled, buoyLab };
  }, [index, reg.latitudeDelta]);

  // Toucher d'un repère : on passe par la carte (onMarkerPress, plus fiable sur iPhone) et par le repère lui-même,
  // en ignorant le second appel s'ils arrivent tous les deux.
  // Secours : si l'iPhone ne signale pas le toucher du repère, on prend le toucher de la carte et on cherche le repère
  // le plus proche à l'écran (projection Mercator de la zone visible). Les bouées passent devant les spots.
  const [size, setSize] = useState({ w: 1, h: 1 });
  const tapMap = (c: { latitude: number; longitude: number }) => {
    const merc = (la: number) => Math.log(Math.tan(Math.PI / 4 + (la * Math.PI) / 360));
    const top = merc(reg.latitude + reg.latitudeDelta / 2), bot = merc(reg.latitude - reg.latitudeDelta / 2);
    const west = reg.longitude - reg.longitudeDelta / 2;
    const px = (la: number, lo: number) => [((lo - west) / reg.longitudeDelta) * size.w, ((top - merc(la)) / (top - bot)) * size.h];
    const [tx, ty] = px(c.latitude, c.longitude);
    let best: { id: string; d: number } | null = null;
    const look = (id: string, la: number, lo: number, r: number, dy = 0, bonus = 0) => {
      const [x, y] = px(la, lo), d = Math.hypot(x - tx, y + dy - ty) - bonus;
      if (d < r && (!best || d < best.d)) best = { id, d };
    };
    index.buoys.forEach(b => { look(`b:${b.id}`, b.lat, b.lon, 34, 0, 8); if (buoyLab.has(b.id)) look(`b:${b.id}`, b.lat, b.lon, 30, 22, 8); });
    index.spots.forEach(s => look(`s:${s.slug}`, s.lat, s.lon, labeled.has(s.slug) ? 28 : 16));
    if (best) open((best as { id: string }).id);
  };

  const last = useRef(0);
  const open = (id: string) => {
    const now = Date.now(); if (now - last.current < 600) return; last.current = now;
    if (id.startsWith('b:')) { const b = index.buoys.find(x => x.id === id.slice(2)); if (b) onBuoy(b); }
    else { const s = index.spots.find(x => x.slug === id.slice(2)); if (s) onSpot(s); }
  };

  const hour = useMemo(() => { const d = new Date(); return `${d.getHours()} h`; }, [index]);

  return (
    <View style={StyleSheet.absoluteFill} onLayout={e => setSize({ w: e.nativeEvent.layout.width, h: e.nativeEvent.layout.height })}>
      <StatusBar style={sat || isDark() ? 'light' : 'dark'} />
      <MapView ref={map} style={StyleSheet.absoluteFill} initialRegion={START} onRegionChangeComplete={setReg} mapType={type} userInterfaceStyle={isDark() ? 'dark' : 'light'}
        mapPadding={{ top: ins.top, bottom, left: 0, right: 0 }} onMarkerPress={e => open(e.nativeEvent.id)} onPress={e => tapMap(e.nativeEvent.coordinate)}
        rotateEnabled={false} pitchEnabled={false} showsPointsOfInterests={false} showsCompass={false} toolbarEnabled={false}>
        {index.spots.map(s => {
          const big = labeled.has(s.slug);
          return (
            <Marker key={`${s.slug}:${big}`} identifier={`s:${s.slug}`} coordinate={{ latitude: s.lat, longitude: s.lon }} onPress={() => open(`s:${s.slug}`)}
              tracksViewChanges={false} anchor={{ x: 0.5, y: 0.5 }} zIndex={big ? 5 : 1}>
              {big ? (
                <View style={[st.spot, { backgroundColor: sizeCell(s.now.hs) }]}>
                  {!!arrow(s.now.dir) && <Text style={[st.spotA, arrow(s.now.dir)]}>↑</Text>}
                  <Text style={st.spotT}>{fr(s.now.hs)}</Text>
                </View>
              ) : (
                <View style={st.hit}><View style={[st.dotSpot, { backgroundColor: sizeCell(s.now.hs) }]} /></View>
              )}
            </Marker>
          );
        })}
        {index.buoys.map((b, i) => {
          const old = ageH(b.time) >= 6, fresh = ageH(b.time) < 2, lab = buoyLab.has(b.id);
          return (
            <Marker key={`${b.id}:${lab}`} identifier={`b:${b.id}`} coordinate={{ latitude: b.lat, longitude: b.lon }} onPress={() => open(`b:${b.id}`)}
              tracksViewChanges={!old} anchor={{ x: 0.5, y: lab ? 0.3 : 0.5 }} zIndex={10}>
              <View style={[st.buWrap, old && { opacity: 0.55 }]}>
                <View style={st.buHalo}>
                  {!old && <Pulse size={20} color={fresh ? C.live : C.sandB} delay={(i % 4) * 450} />}
                  <View style={[st.buRing, fresh && { borderColor: C.live }]}><View style={st.buCore} /></View>
                </View>
                {lab && (
                  <View style={st.buLab}>
                    <Text style={st.buLabT}>{fr(b.hs)} m{perTxt(b) ? ` · ${perTxt(b)}` : ''}</Text>
                  </View>
                )}
              </View>
            </Marker>
          );
        })}
      </MapView>

      {/* Fondu en haut, pour que l'heure et la batterie restent lisibles sur la carte. */}
      <Svg style={[st.fade, { height: ins.top + 70 }]} pointerEvents="none">
        <Defs>
          <LinearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={sat ? '#0b1720' : C.bg} stopOpacity={sat ? 0.55 : 0.85} />
            <Stop offset="1" stopColor={sat ? '#0b1720' : C.bg} stopOpacity={0} />
          </LinearGradient>
        </Defs>
        <Rect width="100%" height="100%" fill="url(#g)" />
      </Svg>

      {/* En haut à gauche : la marque et l'heure de la prévision. */}
      <View style={[st.brand, { top: ins.top + 8 }]} pointerEvents="none">
        <Brand h={16} />
        <View style={st.sep} />
        <Text style={st.brandT}>Houle à {hour}</Text>
      </View>

      {/* À droite : fond de carte et retour à toute la côte. */}
      <View style={[st.tools, { bottom }]}>
        <Pressable onPress={toggleType} style={({ pressed }) => [st.tool, pressed && st.pressed]} accessibilityLabel={sat ? 'Passer au plan' : 'Passer en vue satellite'}>
          <Svg width={22} height={22} viewBox="0 0 24 24">
            <Path d="M12 3 2.5 8 12 13l9.5-5z" stroke={C.ink} strokeWidth={1.8} strokeLinejoin="round" fill={sat ? C.sand : 'none'} />
            <Path d="m2.5 12.5 9.5 5 9.5-5M2.5 16.5l9.5 5 9.5-5" stroke={C.ink} strokeWidth={1.8} strokeLinejoin="round" fill="none" />
          </Svg>
        </Pressable>
        <View style={st.toolSep} />
        <Pressable onPress={() => map.current?.animateToRegion(START, 650)} style={({ pressed }) => [st.tool, pressed && st.pressed]} accessibilityLabel="Revoir toute la côte">
          <Svg width={22} height={22} viewBox="0 0 24 24">
            <Path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" stroke={C.ink} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" fill="none" />
            <Circle cx={12} cy={12} r={2.2} fill={C.ink} />
          </Svg>
        </Pressable>
      </View>

      {/* En bas à gauche : bouées en direct, s'ouvre sur la légende. */}
      <View style={[st.legWrap, { bottom }]}>
        {legend && (
          <Pressable onPress={() => setLegend(false)} style={st.legCard}>
            <Text style={st.legH}>Houle prévue maintenant</Text>
            <View style={st.ramp}>{[0, 0.5, 1, 1.5, 2, 2.5, 3, 4].map(h => <View key={h} style={{ flex: 1, backgroundColor: sizeCell(h) }} />)}</View>
            <View style={st.rampL}><Text style={st.small}>0 m</Text><Text style={st.small}>2 m</Text><Text style={st.small}>4 m +</Text></View>
            <View style={st.legRow}><View style={[st.spot, st.spotMini, { backgroundColor: sizeCell(1.6) }]}><Text style={[st.spotA, arrow(290)]}>↑</Text><Text style={st.spotT}>1,6</Text></View><Text style={st.legTxt}>Spot : hauteur au large, flèche = sens de la houle</Text></View>
            <View style={st.legRow}><View style={[st.hit, { width: 46 }]}><View style={[st.dotSpot, { backgroundColor: sizeCell(1.2) }]} /></View><Text style={st.legTxt}>Autre spot : zoomez pour voir sa hauteur</Text></View>
            <View style={st.legRow}><View style={[st.buRing, { borderColor: C.live }]}><View style={st.buCore} /></View><Text style={st.legTxt}>Bouée : mesure réelle (contour vert = moins de 2 h)</Text></View>
          </Pressable>
        )}
        <Pressable onPress={() => setLegend(v => !v)} style={({ pressed }) => [st.pill, pressed && st.pressed]} accessibilityLabel="Afficher la légende">
          <View style={st.dot} />
          <Text style={st.pillT}>{live} bouée{live > 1 ? 's' : ''} en direct</Text>
          <Svg width={12} height={12} viewBox="0 0 24 24" style={{ transform: [{ rotate: legend ? '180deg' : '0deg' }] }}>
            <Path d="m6 15 6-6 6 6" stroke={C.ink2} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" fill="none" />
          </Svg>
        </Pressable>
      </View>
    </View>
  );
}

const glass = () => ({
  backgroundColor: C.glass,
  shadowColor: '#0b1720', shadowOpacity: 0.18, shadowRadius: 16, shadowOffset: { width: 0, height: 6 }, elevation: 6,
}) as const;

const st = themed(() => StyleSheet.create({
  spot: { flexDirection: 'row', alignItems: 'center', gap: 2, minWidth: 40, height: 26, paddingHorizontal: 8, borderRadius: 13, justifyContent: 'center',
    borderWidth: 2, borderColor: '#fff', shadowColor: '#0b1720', shadowOpacity: 0.25, shadowRadius: 4, shadowOffset: { width: 0, height: 2 }, elevation: 3 },
  spotMini: { minWidth: 46 },
  spotA: { fontSize: 11, fontWeight: '900', color: C.ink, marginTop: -1 },
  spotT: { fontFamily: F.num, fontSize: 11.5, color: C.ink },
  hit: { width: 26, height: 26, alignItems: 'center', justifyContent: 'center' },
  dotSpot: { width: 12, height: 12, borderRadius: 6, borderWidth: 2, borderColor: '#fff',
    shadowColor: '#0b1720', shadowOpacity: 0.3, shadowRadius: 3, shadowOffset: { width: 0, height: 1 }, elevation: 2 },
  buWrap: { alignItems: 'center' },
  buHalo: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', marginBottom: -12 },
  buRing: { width: 20, height: 20, borderRadius: 10, backgroundColor: C.sand, borderWidth: 3, borderColor: '#fff', alignItems: 'center', justifyContent: 'center',
    shadowColor: '#0b1720', shadowOpacity: 0.3, shadowRadius: 4, shadowOffset: { width: 0, height: 2 }, elevation: 3 },
  buCore: { width: 7, height: 7, borderRadius: 4, backgroundColor: '#10202c' },
  buLab: { marginTop: 3, paddingHorizontal: 7, height: 20, borderRadius: 7, backgroundColor: '#10202c', justifyContent: 'center' },
  buLabT: { fontFamily: F.tX, fontSize: 11, color: '#f4e2b8' },
  fade: { position: 'absolute', top: 0, left: 0, right: 0 },
  brand: { position: 'absolute', left: 14, height: 40, borderRadius: 20, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center', gap: 10, ...glass() },
  sep: { width: 1, height: 16, backgroundColor: C.line },
  brandT: { fontFamily: F.tX, fontSize: 12.5, color: C.ink },
  tools: { position: 'absolute', right: 14, borderRadius: 24, width: 48, alignItems: 'center', ...glass() },
  tool: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 24 },
  toolSep: { width: 24, height: 1, backgroundColor: C.line },
  pressed: { opacity: 0.6 },
  legWrap: { position: 'absolute', left: 14, right: 76, alignItems: 'flex-start', gap: 8 },
  pill: { height: 44, borderRadius: 22, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 9, ...glass() },
  dot: { width: 9, height: 9, borderRadius: 5, backgroundColor: C.live },
  pillT: { fontFamily: F.tX, fontSize: 13.5, color: C.ink },
  legCard: { alignSelf: 'stretch', borderRadius: 22, padding: 14, gap: 8, ...glass() },
  legH: { fontFamily: F.num, fontSize: 13, color: C.ink },
  ramp: { flexDirection: 'row', height: 7, borderRadius: 4, overflow: 'hidden' },
  rampL: { flexDirection: 'row', justifyContent: 'space-between', marginTop: -3 },
  small: { fontFamily: F.tB, fontSize: 10.5, color: C.ink2 },
  legRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  legTxt: { flex: 1, fontFamily: F.t, fontSize: 12, color: C.ink2, lineHeight: 16 },
}));
