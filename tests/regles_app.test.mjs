// Règles métier de l'APPLICATION (issue #4) sur les cas communs tests/regles_communes.json, sans réseau :
//   node tests/regles_app.test.mjs        (Node ≥ 23 : lit le .ts)
// Les mêmes cas sont joués sur le site (tests/regles_site.test.js) et le robot (tests/test_regles.py).
import { readFileSync } from 'node:fs';
import { ageWords, candidates, freshState, liveLim, pickRef, sector, windCat } from '../app/src/rules.ts';
import { createReloader } from '../app/src/reload.ts';

const C = JSON.parse(readFileSync(new URL('./regles_communes.json', import.meta.url), 'utf8'));
let fails = 0;
const eq = (name, got, want) => { const ok = JSON.stringify(got) === JSON.stringify(want); if (!ok) fails++; console.log(`[${ok ? 'OK' : 'ÉCHEC'}] ${name} : ${JSON.stringify(got)}${ok ? '' : ' (attendu ' + JSON.stringify(want) + ')'}`); };

const age = a => (a == null ? NaN : a);   // heure illisible → âge non numérique
for (const f of C.fresh) eq(`fraîcheur ${f.id} ${f.age} h${f.lim ? ' lim ' + f.lim : ''}${f.silent ? ' muette' : ''}`, freshState(age(f.age), liveLim(f), !!f.silent), f.want);
for (const x of C.ageWords) eq(`âge en mots ${x.age} h`, ageWords(age(x.age), x.t || '2026-11-27T10:00+01:00'), x.want);
for (const x of C.sector) eq(`secteur ${x.deg}°`, sector(x.deg), x.want);
for (const w of C.wind) eq(`vent ${w.v} km/h du ${w.wdir}° (plage vers ${w.ori}°)`, windCat(w.v, w.wdir, w.ori), w.want);

export function pool(ages) {
  return Object.entries(ages).map(([id, a]) => {
    const s = C.stations.find(x => x.id === id), o = typeof a === 'object' ? a : { age: a };
    return { ...s, ageH: age(o.age), lim: liveLim(s), silent: !!o.silent, hs: 'hs' in o ? o.hs : 1.2 };
  });
}
for (const p of C.pick) {
  const list = candidates(p.spot, pool(p.ages)), r = pickRef(list);
  eq(`bouée : ${p.case}`, r ? r.b.id : null, p.want);
  if (p.cands) eq(`  candidates : ${p.case}`, list.map(o => o.b.id).sort(), [...p.cands].sort());
}
// ---------- reprise réseau d'une fiche (src/reload.ts) : mêmes demandes, réponses dans le désordre, panne partielle ----------
const deferred = () => { let ok, ko; const p = new Promise((a, b) => { ok = a; ko = b; }); return { p, ok, ko }; };
{
  const q = [], seen = [];
  const r = createReloader(() => { const d = deferred(); q.push(d); return d.p; }, s => seen.push(s));
  const a = r.run(), b = r.run();                  // deux demandes de la même fiche (retour au premier plan pendant un chargement)
  q[1].ok({ data: 'récente', offline: false }); await b;
  q[0].ok({ data: 'ancienne', offline: false }); await a;   // la réponse lente de la 1re demande arrive après
  eq('reprise : la réponse d’une demande plus ancienne est ignorée', r.state.data, 'récente');
  const c = r.run(); q[2].ko(new Error('réseau')); await c;
  eq('reprise : panne après un succès → données gardées, marquées hors connexion, sans erreur', [r.state.data, r.state.offline, r.state.err], ['récente', true, false]);
  const d = r.run(); q[3].ok({ data: 'cache', offline: true }); await d;
  eq('reprise : données tirées du cache du téléphone → hors connexion', [r.state.data, r.state.offline], ['cache', true]);
  const e = r.run(); q[4].ok({ data: 'en ligne', offline: false }); await e;
  eq('reprise : retour du réseau → plus hors connexion', [r.state.data, r.state.offline], ['en ligne', false]);
  r.stop(); const f = r.run(); q[5].ok({ data: 'après fermeture', offline: false }); await f;
  eq('reprise : fiche fermée → plus aucune mise à jour', [seen.length, r.state.data], [4, 'en ligne']);
}
{
  const r = createReloader(() => Promise.reject(new Error('réseau')), () => {});
  await r.run();
  eq('reprise : rien en cache et pas de réseau → erreur affichée', [r.state.data, r.state.err], [null, true]);
}
console.log(fails ? `\nÉCHECS : ${fails}` : '\nTOUT OK');
process.exit(fails ? 1 : 0);
