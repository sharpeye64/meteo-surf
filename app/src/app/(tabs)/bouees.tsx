import { router } from 'expo-router';
import { View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { BuoyList } from '../../BuoyScreens';
import { useData } from '../../store';
import { C } from '../../theme';

export default function Bouees() {
  const { index, favs } = useData();
  const ins = useSafeAreaInsets();
  return (
    <View style={{ flex: 1, paddingTop: ins.top, backgroundColor: C.bg }}>
      <BuoyList index={index!} favs={favs} onOpen={b => router.push({ pathname: '/bouee/[slug]', params: { slug: b.slug } })} />
    </View>
  );
}
