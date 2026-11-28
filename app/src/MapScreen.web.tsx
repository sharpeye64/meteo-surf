import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { C, F, themed } from './theme';

/** La carte native n'existe que sur téléphone : l'aperçu web de développement affiche un message et l'accès à la recherche. */
export default function MapScreen() {
  return (
    <View style={st.c}>
      <Text style={st.t}>Carte</Text>
      <Text style={st.s}>La carte s’affiche sur le téléphone (Apple Plans sur iPhone, Google Maps sur Android).</Text>
      <Pressable onPress={() => router.push('/recherche')} style={st.b}><Text style={st.bt}>Chercher un spot</Text></Pressable>
    </View>
  );
}
const st = themed(() => StyleSheet.create({
  c: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30, gap: 8, backgroundColor: C.bg },
  t: { fontFamily: F.num, fontSize: 20, color: C.ink },
  s: { fontFamily: F.t, fontSize: 14, color: C.ink2, textAlign: 'center' },
  b: { marginTop: 10, height: 46, paddingHorizontal: 20, borderRadius: 23, backgroundColor: C.night, justifyContent: 'center' },
  bt: { fontFamily: F.tX, color: C.onNight },
}));
