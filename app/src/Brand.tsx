import { SvgXml } from 'react-native-svg';
import symbol from './brand/symbol';
import wordmark from './brand/wordmark';
import { C } from './theme';

/** Logo fourni par l'utilisateur (le « h » dont l'arche devient une houle) + le mot « houlalah ». */
export default function Brand({ h = 22, ink = C.ink }: { h?: number; ink?: string }) {
  return (
    <>
      <SvgXml xml={symbol} height={h} width={(h * 683) / 477} />
      <SvgXml xml={wordmark.replace('fill="#E9C694"', `fill="${ink}"`)} height={h * 0.62} width={(h * 0.62 * 1006) / 185} />
    </>
  );
}
