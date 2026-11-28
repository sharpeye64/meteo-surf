import { useLocalSearchParams } from 'expo-router';
import { Text, View } from 'react-native';
import SpotSheet from '../../SpotSheet';
import { useData } from '../../store';
import { C, F } from '../../theme';

/** houlalah://spot/<slug> : fiche d'un spot en panneau natif. Spot inconnu (lien ancien) : message clair. */
export default function SpotRoute() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { index } = useData();
  const spot = index?.spots.find(s => s.slug === slug);
  if (!spot) return <View style={{ flex: 1, backgroundColor: C.bg, padding: 30 }}><Text style={{ fontFamily: F.t, color: C.ink2, textAlign: 'center', marginTop: 30 }}>{index ? 'Ce spot n’existe pas ou plus.' : 'Chargement…'}</Text></View>;
  return <SpotSheet spot={spot} />;
}
