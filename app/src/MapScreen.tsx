import AsyncStorage from '@react-native-async-storage/async-storage';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { MapType, Marker, Region } from 'react-native-maps';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Defs, LinearGradient, Path, Rect, Stop } from 'react-native-svg';
import Brand from './Brand';
import { ageH, Buoy, fr, Index, SpotLite } from './data';
import { FLOAT_BAR_H } from './TabBar';
import { C, F, sizeCell } from './theme';

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

  // Une seule pastille par case de la grille (les bouées d'abord, puis les plus grosses houles) : on en voit plus en zoomant.
  const { spots, buoys } = useMemo(() => {
    const cell = reg.latitudeDelta / 11, taken = new Set<string>();
    const free = (lat: number, lon: number) => {
      const k = `${Math.round(lat / cell)}:${Math.round(lon / (cell * 1.5))}`;
      if (taken.has(k)) return false; taken.add(k); return true;
    };
    const bs = [...index.buoys].sort((a, b) => ageH(a.time) - ageH(b.time)).filter(b => free(b.lat, b.lon));
    const ss = [...index.spots].sort((a, b) => (b.now.hs ?? 0) - (a.now.hs ?? 0)).filter(s => free(s.lat, s.lon));
    return { spots: ss, buoys: bs };
  }, [index, reg.latitudeDelta]);

  const hour = useMemo(() => { const d = new Date(); return `${d.getHours()} h`; }, [index]);

  return (
    <View style={StyleSheet.absoluteFill}>
      <StatusBar style={sat ? 'light' : 'dark'} />
      <MapView ref={map} style={StyleSheet.absoluteFill} initialRegion={START} onRegionChangeComplete={setReg} mapType={type}
        mapPadding={{ top: ins.top, bottom, left: 0, right: 0 }}
        rotateEnabled={false} pitchEnabled={false} showsPointsOfInterests={false} showsCompass={false} toolbarEnabled={false}>
        {spots.map(s => (
          <Marker key={s.slug} coordinate={{ latitude: s.lat, longitude: s.lon }} onPress={() => onSpot(s)} tracksViewChanges={false} anchor={{ x: 0.5, y: 0.5 }}>
            <View style={[st.spot, { backgroundColor: sizeCell(s.now.hs) }]}>
              {!!arrow(s.now.dir) && <Text style={[st.spotA, arrow(s.now.dir)]}>↑</Text>}
              <Text style={st.spotT}>{fr(s.now.hs)}</Text>
            </View>
          </Marker>
        ))}
        {buoys.map(b => {
          const old = ageH(b.time) >= 6, fresh = ageH(b.time) < 2;
          return (
            <Marker key={b.id} coordinate={{ latitude: b.lat, longitude: b.lon }} onPress={() => onBuoy(b)} tracksViewChanges={false} anchor={{ x: 0.5, y: 0.3 }}>
              <View style={[st.buWrap, old && { opacity: 0.55 }]}>
                <View style={[st.buRing, fresh && { borderColor: C.live }]}><View style={st.buCore} /></View>
                <View style={st.buLab}>
                  <Text style={st.buLabT}>{fr(b.hs)} m{b.tp ? ` · ${Math.round(b.tp)} s` : ''}</Text>
                </View>
              </View>
            </Marker>
          );
        })}
      </MapView>

      {/* Fondu en haut, pour que l'heure et la batterie restent lisibles sur la carte. */}
      <Svg style={[st.fade, { height: ins.top + 70 }]} pointerEvents="none">
        <Defs>
          <LinearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={sat ? '#0b1720' : '#eef1f2'} stopOpacity={sat ? 0.55 : 0.85} />
            <Stop offset="1" stopColor={sat ? '#0b1720' : '#eef1f2'} stopOpacity={0} />
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

const glass = {
  backgroundColor: 'rgba(255,255,255,0.93)',
  shadowColor: '#0b1720', shadowOpacity: 0.18, shadowRadius: 16, shadowOffset: { width: 0, height: 6 }, elevation: 6,
} as const;

const st = StyleSheet.create({
  spot: { flexDirection: 'row', alignItems: 'center', gap: 2, minWidth: 40, height: 26, paddingHorizontal: 8, borderRadius: 13, justifyContent: 'center',
    borderWidth: 2, borderColor: '#fff', shadowColor: '#0b1720', shadowOpacity: 0.25, shadowRadius: 4, shadowOffset: { width: 0, height: 2 }, elevation: 3 },
  spotMini: { minWidth: 46 },
  spotA: { fontSize: 11, fontWeight: '900', color: C.ink, marginTop: -1 },
  spotT: { fontFamily: F.num, fontSize: 11.5, color: C.ink },
  buWrap: { alignItems: 'center' },
  buRing: { width: 20, height: 20, borderRadius: 10, backgroundColor: C.sand, borderWidth: 3, borderColor: '#fff', alignItems: 'center', justifyContent: 'center',
    shadowColor: '#0b1720', shadowOpacity: 0.3, shadowRadius: 4, shadowOffset: { width: 0, height: 2 }, elevation: 3 },
  buCore: { width: 7, height: 7, borderRadius: 4, backgroundColor: C.ink },
  buLab: { marginTop: 3, paddingHorizontal: 7, height: 20, borderRadius: 7, backgroundColor: C.ink, justifyContent: 'center' },
  buLabT: { fontFamily: F.tX, fontSize: 11, color: C.sandA },
  fade: { position: 'absolute', top: 0, left: 0, right: 0 },
  brand: { position: 'absolute', left: 14, height: 40, borderRadius: 20, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center', gap: 10, ...glass },
  sep: { width: 1, height: 16, backgroundColor: C.line },
  brandT: { fontFamily: F.tX, fontSize: 12.5, color: C.ink },
  tools: { position: 'absolute', right: 14, borderRadius: 24, width: 48, alignItems: 'center', ...glass },
  tool: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 24 },
  toolSep: { width: 24, height: 1, backgroundColor: C.line },
  pressed: { opacity: 0.6 },
  legWrap: { position: 'absolute', left: 14, right: 76, alignItems: 'flex-start', gap: 8 },
  pill: { height: 44, borderRadius: 22, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 9, ...glass },
  dot: { width: 9, height: 9, borderRadius: 5, backgroundColor: C.live },
  pillT: { fontFamily: F.tX, fontSize: 13.5, color: C.ink },
  legCard: { alignSelf: 'stretch', borderRadius: 22, padding: 14, gap: 8, ...glass },
  legH: { fontFamily: F.num, fontSize: 13, color: C.ink },
  ramp: { flexDirection: 'row', height: 7, borderRadius: 4, overflow: 'hidden' },
  rampL: { flexDirection: 'row', justifyContent: 'space-between', marginTop: -3 },
  small: { fontFamily: F.tB, fontSize: 10.5, color: C.ink2 },
  legRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  legTxt: { flex: 1, fontFamily: F.t, fontSize: 12, color: C.ink2, lineHeight: 16 },
});
