/** Petite icône ⓘ qui déplie, juste en dessous, les mentions pédagogiques indispensables (décision du porteur, 28/11 :
 *  montrer la donnée plutôt que la raconter ; l'explication reste accessible, mais jamais affichée d'office).
 *  À placer en dernier dans une rangée qui passe à la ligne (flexWrap) : le texte prend toute la largeur dessous. */
import * as Haptics from 'expo-haptics';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { C, F, themed } from './theme';

export default function Info({ lines, light }: { lines: string[]; light?: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Pressable onPress={() => { Haptics.selectionAsync().catch(() => {}); setOpen(o => !o); }} hitSlop={12}
        style={[st.i, light && st.iLight, open && (light ? st.iOnLight : st.iOn)]} accessibilityRole="button"
        accessibilityLabel={open ? 'Masquer l’explication' : 'Explication'} accessibilityState={{ expanded: open }}>
        <Text style={[st.iT, light && { color: C.onBuoy }, open && { color: light ? C.buoySurface : C.onNight }]}>i</Text>
      </Pressable>
      {open && (
        <View style={[st.tip, light && st.tipLight]} accessibilityLiveRegion="polite">
          {lines.map(l => <Text key={l} style={[st.tipT, light && { color: C.onBuoy }]}>{l}</Text>)}
        </View>
      )}
    </>
  );
}

const st = themed(() => StyleSheet.create({
  i: { width: 20, height: 20, borderRadius: 10, borderWidth: 1.3, borderColor: C.ink3, alignItems: 'center', justifyContent: 'center' },
  iLight: { borderColor: C.onBuoy2 },
  iOn: { backgroundColor: C.night, borderColor: C.night },
  iOnLight: { backgroundColor: C.measureOnBuoy, borderColor: C.measureOnBuoy },
  iT: { fontFamily: F.tX, fontSize: 11.5, color: C.ink3, marginTop: -1 },
  tip: { flexBasis: '100%', marginTop: 8, padding: 12, borderRadius: 14, backgroundColor: C.soft, gap: 4 },
  tipLight: { backgroundColor: 'rgba(243,239,230,0.08)' },
  tipT: { fontFamily: F.tR, fontSize: 12.5, lineHeight: 17, color: C.ink2 },
}));
