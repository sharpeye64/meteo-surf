/** Barre d'onglets en PILULE flottante (demande du porteur, chantier #8) : verre crème posé sur le contenu, bulle bleu nuit
 *  qui glisse sous l'onglet actif (l'or reste réservé aux mesures), petit retour haptique. Sans animation si l'iPhone demande
 *  de réduire les animations. */
import * as Haptics from 'expo-haptics';
import { usePathname } from 'expo-router';
import { TabTriggerSlotProps } from 'expo-router/ui';
import { ReactNode, Ref, useEffect, useRef, useState } from 'react';
import { Animated, Easing, Pressable, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';
import { useData } from './store';
import { C, F, themed } from './theme';

export type Tab = 'carte' | 'macote' | 'bouees';
export const TABS: { k: Tab; label: string; href: '/' | '/macote' | '/bouees' }[] = [
  { k: 'carte', label: 'Carte', href: '/' }, { k: 'macote', label: 'Ma côte', href: '/macote' }, { k: 'bouees', label: 'Bouées', href: '/bouees' },
];

/** Hauteur de la pilule ; les écrans placent leurs commandes au-dessus. */
export const FLOAT_BAR_H = 60;
export const barBottom = (insetBottom: number) => Math.max(insetBottom - 8, 14);

/** Place à laisser en bas des écrans qui défilent, pour que la fin du contenu ne reste pas cachée sous la pilule. */
export function useBarSpace() {
  const ins = useSafeAreaInsets();
  return barBottom(ins.bottom) + FLOAT_BAR_H + 18;
}

export function TabIcon({ k, color }: { k: Tab; color: string }) {
  const p = { stroke: color, strokeWidth: 1.8, fill: 'none', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  return (
    <Svg width={24} height={24} viewBox="0 0 24 24">
      {k === 'carte' && <Path {...p} d="M9 4 3.5 6v14L9 18l6 2 5.5-2V4L15 6z M9 4v14 M15 6v14" />}
      {k === 'macote' && <Path {...p} d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.9z" />}
      {k === 'bouees' && <Path {...p} d="M5 15a7 7 0 0 1 14 0z M12 8V4 M3 19c2-1.5 4-1.5 6 0s4 1.5 6 0 4-1.5 6 0" />}
    </Svg>
  );
}

/** Bouton d'onglet (enfant d'un TabTrigger « asChild »). */
export function TabButton({ k, label, isFocused, onPress, ref, ...rest }: TabTriggerSlotProps & { k: Tab; label: string; ref?: Ref<unknown> }) {
  const col = isFocused ? C.onNight : C.ink2;
  return (
    <Pressable {...rest} ref={ref as never} accessibilityRole="tab" accessibilityState={{ selected: !!isFocused }} accessibilityLabel={label}
      onPress={e => { if (!isFocused) Haptics.selectionAsync().catch(() => {}); onPress?.(e); }} style={st.item}>
      <TabIcon k={k} color={col} />
      <Text style={[st.t, { color: col }, isFocused && { fontFamily: F.tX }]}>{label}</Text>
    </Pressable>
  );
}

/** La pilule : fond en verre, bulle active animée, puis les boutons (passés en enfants). */
export function PillBar({ children }: { children: ReactNode }) {
  const ins = useSafeAreaInsets();
  const { reduceMotion } = useData();
  const path = usePathname();
  const i = path.startsWith('/macote') ? 1 : path.startsWith('/bouees') ? 2 : 0;
  const [w, setW] = useState(0);
  const x = useRef(new Animated.Value(0)).current;
  const placed = useRef(false);
  const item = w ? (w - 12) / 3 : 0;
  useEffect(() => {
    if (!item) return;
    // premier affichage (ou lien direct vers un onglet) : bulle posée sans glisser ; ensuite, ressort
    if (reduceMotion || !placed.current) { placed.current = true; x.setValue(i * item); return; }
    Animated.spring(x, { toValue: i * item, useNativeDriver: true, speed: 18, bounciness: 6 }).start();
  }, [i, item, reduceMotion, x]);
  return (
    <View style={[st.pill, { bottom: barBottom(ins.bottom) }]} onLayout={e => setW(e.nativeEvent.layout.width)}>
      {!!item && <Animated.View pointerEvents="none" style={[st.bubble, { width: item, transform: [{ translateX: x }] }]} />}
      {children}
    </View>
  );
}

const st = themed(() => StyleSheet.create({
  pill: {
    position: 'absolute', left: 22, right: 22, height: FLOAT_BAR_H, borderRadius: FLOAT_BAR_H / 2, padding: 6, flexDirection: 'row',
    backgroundColor: C.glass, borderWidth: StyleSheet.hairlineWidth, borderColor: C.line,
    shadowColor: '#0b1b26', shadowOpacity: 0.24, shadowRadius: 20, shadowOffset: { width: 0, height: 10 }, elevation: 10,
  },
  bubble: { position: 'absolute', left: 6, top: 6, bottom: 6, borderRadius: (FLOAT_BAR_H - 12) / 2, backgroundColor: C.night },
  item: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 2, borderRadius: (FLOAT_BAR_H - 12) / 2 },
  t: { fontFamily: F.tB, fontSize: 11 },
}));

// Easing réservé aux transitions qui ne passent pas par un ressort (cohérence des durées, 0,2 à 0,4 s : DESIGN_SYSTEM).
export const EASE = Easing.bezier(0.2, 0.8, 0.2, 1);
