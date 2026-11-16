import Svg, { Path } from 'react-native-svg';

/** Flèche dans le sens où va la houle ou le vent (la donnée est la direction d'où ils viennent). */
export default function Arrow({ dir, size = 16, color = '#10202c' }: { dir?: number | null; size?: number; color?: string }) {
  if (dir == null) return null;
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" style={{ transform: [{ rotate: `${(dir + 180) % 360}deg` }] }}>
      <Path d="M12 3l6 15-6-3.5L6 18z" fill={color} />
    </Svg>
  );
}
