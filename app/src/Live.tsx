import { useEffect, useRef } from 'react';
import { Animated, Easing, StyleProp, ViewStyle } from 'react-native';
import { C } from './theme';

/** Feu « en direct » qui clignote doucement, comme le bandeau des bouées du site (décalé selon `delay`). */
export function Blink({ size = 8, color = C.live, delay = 0, style }: { size?: number; color?: string; delay?: number; style?: StyleProp<ViewStyle> }) {
  const v = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    const a = Animated.loop(Animated.sequence([
      Animated.delay(delay),
      Animated.timing(v, { toValue: 0.25, duration: 700, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      Animated.timing(v, { toValue: 1, duration: 700, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      Animated.delay(Math.max(0, 1400 - delay)),
    ]));
    a.start();
    return () => a.stop();
  }, [v, delay]);
  return <Animated.View style={[{ width: size, height: size, borderRadius: size / 2, backgroundColor: color, opacity: v }, style]} />;
}

/** Onde qui s'élargit et s'efface autour d'une bouée sur la carte. */
export function Pulse({ size = 20, color = C.live, delay = 0 }: { size?: number; color?: string; delay?: number }) {
  const v = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const a = Animated.loop(Animated.sequence([
      Animated.delay(delay),
      Animated.timing(v, { toValue: 1, duration: 1800, easing: Easing.out(Easing.quad), useNativeDriver: true }),
      Animated.timing(v, { toValue: 0, duration: 0, useNativeDriver: true }),
      Animated.delay(Math.max(0, 900 - delay)),
    ]));
    a.start();
    return () => a.stop();
  }, [v, delay]);
  return (
    <Animated.View pointerEvents="none" style={{
      position: 'absolute', width: size, height: size, borderRadius: size / 2, backgroundColor: color,
      opacity: v.interpolate({ inputRange: [0, 1], outputRange: [0.55, 0] }),
      transform: [{ scale: v.interpolate({ inputRange: [0, 1], outputRange: [0.8, 2.3] }) }],
    }} />
  );
}
