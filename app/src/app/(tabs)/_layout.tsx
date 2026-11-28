/** Les trois onglets (Carte, Ma côte, Bouées) avec la pilule flottante. Tant que l'index n'est pas là : chargement, ou
 *  message clair avec « Réessayer » (sans réseau et sans copie sur le téléphone). */
import { TabList, Tabs, TabSlot, TabTrigger } from 'expo-router/ui';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { useData } from '../../store';
import { PillBar, TabButton, TABS } from '../../TabBar';
import { C, F, themed } from '../../theme';

export default function TabsLayout() {
  const { index, err, reload } = useData();
  if (!index) {
    return (
      <View style={st.center}>
        {err ? (
          <>
            <Text style={st.msg}>Impossible de charger les prévisions.{'\n'}Vérifiez la connexion.</Text>
            <Pressable onPress={reload} style={st.retry} accessibilityRole="button"><Text style={st.retryT}>Réessayer</Text></Pressable>
          </>
        ) : <ActivityIndicator color={C.ink} />}
      </View>
    );
  }
  return (
    <Tabs>
      <TabSlot />
      <TabList asChild>
        <PillBar>
          {TABS.map(t => (
            <TabTrigger key={t.k} name={t.k} href={t.href} asChild>
              <TabButton k={t.k} label={t.label} />
            </TabTrigger>
          ))}
        </PillBar>
      </TabList>
    </Tabs>
  );
}

const st = themed(() => StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30, backgroundColor: C.bg },
  msg: { color: C.ink2, fontSize: 16, textAlign: 'center', fontFamily: F.t, lineHeight: 23 },
  retry: { marginTop: 16, backgroundColor: C.night, paddingHorizontal: 22, height: 46, borderRadius: 23, justifyContent: 'center' },
  retryT: { color: C.onNight, fontFamily: F.tX, fontSize: 14 },
}));
