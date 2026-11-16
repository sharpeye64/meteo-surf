import { useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { Marker, Region } from 'react-native-maps';
import { ageH, Buoy, fr, Index, SpotLite } from './data';
import { C, F, sizeCell } from './theme';

type Props = { index: Index; onSpot: (s: SpotLite) => void; onBuoy: (b: Buoy) => void };
const START: Region = { latitude: 44.6, longitude: -3.2, latitudeDelta: 9.5, longitudeDelta: 9.5 };

/** Carte native (Apple Plans / Google Maps) : les spots en cases colorées, les bouées en pastilles sable.
 *  Comme sur l'accueil du site, on n'affiche qu'une pastille par groupe de spots trop proches (on en voit plus en zoomant). */
export default function MapScreen({ index, onSpot, onBuoy }: Props) {
  const [reg, setReg] = useState<Region>(START);
  const map = useRef<MapView>(null);
  const shown = useMemo(() => {
    const cell = reg.latitudeDelta / 14, taken = new Set<string>(), out: SpotLite[] = [];
    [...index.spots].sort((a, b) => (b.now.hs ?? 0) - (a.now.hs ?? 0)).forEach(s => {
      const k = `${Math.round(s.lat / cell)}:${Math.round(s.lon / (cell * 1.4))}`;
      if (!taken.has(k)) { taken.add(k); out.push(s); }
    });
    return out;
  }, [index, reg.latitudeDelta]);

  return (
    <View style={{ flex: 1 }}>
      <MapView ref={map} style={StyleSheet.absoluteFill} initialRegion={START} onRegionChangeComplete={setReg}
        rotateEnabled={false} pitchEnabled={false} showsPointsOfInterests={false} toolbarEnabled={false}>
        {shown.map(s => (
          <Marker key={s.slug} coordinate={{ latitude: s.lat, longitude: s.lon }} onPress={() => onSpot(s)} tracksViewChanges={false} anchor={{ x: 0.5, y: 0.5 }}>
            <View style={[st.pt, { backgroundColor: sizeCell(s.now.hs) }]}><Text style={st.ptT}>{fr(s.now.hs)}</Text></View>
          </Marker>
        ))}
        {index.buoys.map(b => (
          <Marker key={b.id} coordinate={{ latitude: b.lat, longitude: b.lon }} onPress={() => onBuoy(b)} tracksViewChanges={false} anchor={{ x: 0.5, y: 0.5 }}>
            <View style={[st.bu, ageH(b.time) >= 6 && { opacity: 0.6 }]}><Text style={st.buT}>{fr(b.hs)}</Text></View>
          </Marker>
        ))}
      </MapView>
      <View style={st.legend} pointerEvents="box-none">
        <Text style={st.legT}>Houle prévue maintenant</Text>
        <View style={st.ramp}>{[0, 0.5, 1, 1.5, 2, 2.5, 3, 4].map(h => <View key={h} style={{ flex: 1, backgroundColor: sizeCell(h) }} />)}</View>
        <View style={st.legRow}><Text style={st.legS}>0 m</Text><View style={st.legBu}><View style={st.dotSand} /><Text style={st.legS}>bouée : mesure réelle</Text></View><Text style={st.legS}>4 m +</Text></View>
      </View>
      <Pressable style={st.reset} onPress={() => map.current?.animateToRegion(START, 600)} accessibilityLabel="Revoir toute la côte">
        <Text style={st.resetT}>Toute la côte</Text>
      </Pressable>
    </View>
  );
}

const st = StyleSheet.create({
  pt: { minWidth: 34, height: 24, paddingHorizontal: 6, borderRadius: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1.5, borderColor: '#fff' },
  ptT: { fontFamily: F.tX, fontSize: 11.5, color: C.ink },
  bu: { minWidth: 36, height: 24, paddingHorizontal: 7, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: C.sandB, borderWidth: 1.5, borderColor: C.sandText },
  buT: { fontFamily: F.tX, fontSize: 11.5, color: C.sandText },
  legend: { position: 'absolute', left: 12, right: 12, bottom: 12, backgroundColor: C.card, borderRadius: 18, padding: 12, shadowColor: '#10202c', shadowOpacity: 0.15, shadowRadius: 14, elevation: 4 },
  legT: { fontFamily: F.num, fontSize: 13, color: C.ink },
  ramp: { flexDirection: 'row', height: 7, borderRadius: 4, overflow: 'hidden', marginTop: 8 },
  legRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 5 },
  legS: { fontFamily: F.tB, fontSize: 11, color: C.ink2 },
  legBu: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  dotSand: { width: 10, height: 10, borderRadius: 5, backgroundColor: C.sandB, borderWidth: 1, borderColor: C.sandText },
  reset: { position: 'absolute', top: 12, right: 12, height: 38, paddingHorizontal: 14, borderRadius: 19, backgroundColor: C.card, justifyContent: 'center' },
  resetT: { fontFamily: F.tX, fontSize: 12.5, color: C.ink },
});
