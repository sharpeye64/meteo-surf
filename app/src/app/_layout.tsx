/** Racine de l'appli (Expo Router, chantier #8) : polices, thème clair / sombre, données partagées, et la pile de navigation.
 *  Les fiches d'un spot et d'une bouée s'ouvrent en PANNEAU NATIF à crans (formSheet) par-dessus les onglets : la carte reste
 *  montée derrière, avec sa zone et son zoom. Liens profonds automatiques : houlalah://spot/<slug>, houlalah://bouee/<slug>. */
import { Manrope_500Medium, Manrope_600SemiBold, Manrope_700Bold, Manrope_800ExtraBold } from '@expo-google-fonts/manrope';
import { Unbounded_500Medium, Unbounded_700Bold, Unbounded_800ExtraBold } from '@expo-google-fonts/unbounded';
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useColorScheme, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { DataProvider } from '../store';
import { C, isDark, setMode } from '../theme';

const SHEET = {
  presentation: 'formSheet' as const,
  sheetAllowedDetents: [0.55, 1.0],   // 1.0 = grand cran iOS : plein écran sous la barre d'état (demande du porteur)
  sheetInitialDetentIndex: 1,
  sheetGrabberVisible: true,
  sheetCornerRadius: 30,
  sheetLargestUndimmedDetentIndex: 0 as const,
};

export default function Root() {
  setMode(useColorScheme() === 'dark' ? 'dark' : 'light');
  const [fonts] = useFonts({ Unbounded_500Medium, Unbounded_700Bold, Unbounded_800ExtraBold, Manrope_500Medium, Manrope_600SemiBold, Manrope_700Bold, Manrope_800ExtraBold });
  if (!fonts) return <View style={{ flex: 1, backgroundColor: C.bg }} />;
  return (
    <SafeAreaProvider>
      <DataProvider>
        <StatusBar style={isDark() ? 'light' : 'dark'} />
        <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: C.bg } }}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="spot/[slug]" options={{ ...SHEET, contentStyle: { backgroundColor: C.bg } }} />
          <Stack.Screen name="bouee/[slug]" options={{ ...SHEET, contentStyle: { backgroundColor: C.bg } }} />
          <Stack.Screen name="recherche" options={{ ...SHEET, sheetAllowedDetents: [0.94], sheetInitialDetentIndex: 0, contentStyle: { backgroundColor: C.bg } }} />
          <Stack.Screen name="comparer" options={{ presentation: 'card', contentStyle: { backgroundColor: C.bg } }} />
        </Stack>
      </DataProvider>
    </SafeAreaProvider>
  );
}
