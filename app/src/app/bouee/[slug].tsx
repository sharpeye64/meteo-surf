import { router, useLocalSearchParams } from 'expo-router';
import { Text, View } from 'react-native';
import { BuoyPage } from '../../BuoyScreens';
import { useData } from '../../store';
import { C, F } from '../../theme';

/** houlalah://bouee/<slug> : page d'une bouée en panneau natif. */
export default function BuoyRoute() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { index } = useData();
  const buoy = index?.buoys.find(b => b.slug === slug);
  if (!buoy) return <View style={{ flex: 1, backgroundColor: C.bg, padding: 30 }}><Text style={{ fontFamily: F.t, color: C.ink2, textAlign: 'center', marginTop: 30 }}>{index ? 'Cette bouée n’existe pas ou plus.' : 'Chargement…'}</Text></View>;
  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <BuoyPage buoy={buoy} onBack={() => router.back()} onSpot={s => router.push({ pathname: '/spot/[slug]', params: { slug: s } })} />
    </View>
  );
}
