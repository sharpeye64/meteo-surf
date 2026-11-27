// Règles métier de l'APPLICATION (issue #4) sur les cas communs tests/regles_communes.json, sans réseau :
//   node tests/regles_app.test.mjs        (Node ≥ 23 : lit le .ts)
// Les mêmes cas sont joués sur le site (tests/regles_site.test.js) et le robot (tests/test_regles.py).
import { readFileSync } from 'node:fs';
import { candidates, freshState, liveLim, pickRef, sector, windCat } from '../app/src/rules.ts';

const C = JSON.parse(readFileSync(new URL('./regles_communes.json', import.meta.url), 'utf8'));
let fails = 0;
const eq = (name, got, want) => { const ok = JSON.stringify(got) === JSON.stringify(want); if (!ok) fails++; console.log(`[${ok ? 'OK' : 'ÉCHEC'}] ${name} : ${JSON.stringify(got)}${ok ? '' : ' (attendu ' + JSON.stringify(want) + ')'}`); };

for (const f of C.fresh) eq(`fraîcheur ${f.id} ${f.age} h${f.lim ? ' lim ' + f.lim : ''}${f.silent ? ' muette' : ''}`, freshState(f.age, liveLim(f), !!f.silent), f.want);
for (const x of C.sector) eq(`secteur ${x.deg}°`, sector(x.deg), x.want);
for (const w of C.wind) eq(`vent ${w.v} km/h du ${w.wdir}° (plage vers ${w.ori}°)`, windCat(w.v, w.wdir, w.ori), w.want);

export function pool(ages) {
  return Object.entries(ages).map(([id, a]) => {
    const s = C.stations.find(x => x.id === id), o = typeof a === 'object' ? a : { age: a };
    return { ...s, ageH: o.age, lim: liveLim(s), silent: !!o.silent, hs: 'hs' in o ? o.hs : 1.2 };
  });
}
for (const p of C.pick) {
  const list = candidates(p.spot, pool(p.ages)), r = pickRef(list);
  eq(`bouée : ${p.case}`, r ? r.b.id : null, p.want);
  if (p.cands) eq(`  candidates : ${p.case}`, list.map(o => o.b.id).sort(), [...p.cands].sort());
}
console.log(fails ? `\nÉCHECS : ${fails}` : '\nTOUT OK');
process.exit(fails ? 1 : 0);
