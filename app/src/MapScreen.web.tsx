import { StyleSheet, Text, View } from 'react-native';
import { Buoy, Index, SpotLite } from './data';
import { C, F } from './theme';

/** La carte native n'existe que sur téléphone : la version web (aperçu de développement) affiche un simple message. */
export default function MapScreen(_: { index: Index; onSpot: (s: SpotLite) => void; onBuoy: (b: Buoy) => void }) {
  return (
    <View style={st.c}>
      <Text style={st.t}>Carte</Text>
      <Text style={st.s}>La carte s’affiche sur le téléphone (Apple Plans sur iPhone, Google Maps sur Android).</Text>
    </View>
  );
}
const st = StyleSheet.create({
  c: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30, gap: 8 },
  t: { fontFamily: F.num, fontSize: 20, color: C.ink },
  s: { fontFamily: F.t, fontSize: 14, color: C.ink2, textAlign: 'center' },
});
