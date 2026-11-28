/** Cartouche de fraîcheur des données (revue de René, PR #23) : l'heure de la prévision affichée ET l'âge de la génération
 *  par le robot, recalculés chaque minute. Données en retard (> 3 h) ou anciennes (> 6 h) : dit en clair, en couleur
 *  d'avertissement ; hors connexion : dit aussi. Jamais caché, jamais « maintenant » pour une valeur d'une autre heure. */
import { StyleSheet, Text, View } from 'react-native';
import { useData, useDataAge } from './store';
import { agoWords } from './series';
import { C, F, themed } from './theme';
import { partsIn, tMs } from './time';

const J = ['dim.', 'lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.'];

/** « Prévision sam. 11 h · calculée il y a 25 min » (t = heure des valeurs affichées, heure de Paris). */
export default function Stamp({ t, style }: { t?: string | null; style?: object }) {
  const { offline } = useData();
  const age = useDataAge();
  const p = t ? partsIn(tMs(t), 'Europe/Paris') : null;
  const warn = age.level !== 'ok' || offline;
  const what = p ? `Prévision ${J[p.wd]} ${p.h} h` : 'Prévision';
  const tail = age.level === 'old' ? `ancienne, calculée ${agoWords(age.h)}` : `calculée ${agoWords(age.h)}`;
  return (
    <View style={[st.box, warn && st.warn, style]} accessibilityRole="text"
      accessibilityLabel={`${what}, ${tail}${offline ? ', hors connexion' : ''}`}>
      <Text style={[st.t, warn && { color: C.warn }]} numberOfLines={1}>
        {what}<Text style={st.s}> · {tail}{offline ? ' · hors connexion' : ''}</Text>
      </Text>
    </View>
  );
}

const st = themed(() => StyleSheet.create({
  box: { alignSelf: 'flex-start', height: 26, borderRadius: 13, paddingHorizontal: 11, justifyContent: 'center', backgroundColor: C.glass },
  warn: { backgroundColor: C.warnBg },
  t: { fontFamily: F.tX, fontSize: 11.5, color: C.ink },
  s: { fontFamily: F.tB },
}));
