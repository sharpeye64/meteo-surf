import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Path } from 'react-native-svg';
import { C, F } from './theme';

export type Tab = 'spots' | 'carte' | 'bouees' | 'favoris';
const TABS: { k: Tab; label: string }[] = [
  { k: 'spots', label: 'Spots' }, { k: 'carte', label: 'Carte' }, { k: 'bouees', label: 'Bouées' }, { k: 'favoris', label: 'Favoris' },
];

/** Icônes fines au trait, comme la barre du bas du site mobile. */
function Icon({ k, color }: { k: Tab; color: string }) {
  const p = { stroke: color, strokeWidth: 1.8, fill: 'none', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  return (
    <Svg width={23} height={23} viewBox="0 0 24 24">
      {k === 'spots' && <><Path {...p} d="M3 15c2-2 4-2 6 0s4 2 6 0 4-2 6 0" /><Path {...p} d="M3 9c2-2 4-2 6 0s4 2 6 0 4-2 6 0" /></>}
      {k === 'carte' && <><Path {...p} d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0C18.5 15.4 12 21 12 21z" /><Circle {...p} cx={12} cy={10} r={2.4} /></>}
      {k === 'bouees' && <><Path {...p} d="M5 15a7 7 0 0 1 14 0z" /><Path {...p} d="M12 8V4M3 19c2-1.5 4-1.5 6 0s4 1.5 6 0 4-1.5 6 0" /></>}
      {k === 'favoris' && <Path {...p} d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.9z" />}
    </Svg>
  );
}

export default function TabBar({ tab, onTab }: { tab: Tab; onTab: (t: Tab) => void }) {
  const ins = useSafeAreaInsets();
  return (
    <View style={[st.bar, { paddingBottom: Math.max(ins.bottom, 8) }]}>
      {TABS.map(t => {
        const on = t.k === tab, col = on ? C.ink : C.ink3;
        return (
          <Pressable key={t.k} onPress={() => onTab(t.k)} style={st.item} accessibilityRole="tab" accessibilityState={{ selected: on }}>
            <Icon k={t.k} color={col} />
            <Text style={[st.t, { color: col }, on && { fontFamily: F.tX }]}>{t.label}</Text>
            {on && <View style={st.pip} />}
          </Pressable>
        );
      })}
    </View>
  );
}

const st = StyleSheet.create({
  bar: { flexDirection: 'row', backgroundColor: C.card, paddingTop: 8, borderTopWidth: 1, borderTopColor: C.line },
  item: { flex: 1, alignItems: 'center', gap: 3 },
  t: { fontFamily: F.tB, fontSize: 11.5 },
  pip: { position: 'absolute', top: -8, width: 22, height: 3, borderRadius: 2, backgroundColor: C.sandB },
});
