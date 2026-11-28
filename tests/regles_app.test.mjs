// Règles métier de l'APPLICATION (issue #4) sur les cas communs tests/regles_communes.json, sans réseau :
//   node tests/regles_app.test.mjs        (Node ≥ 23 : lit le .ts)
// Les mêmes cas sont joués sur le site (tests/regles_site.test.js) et le robot (tests/test_regles.py).
import { readFileSync } from 'node:fs';
import { ageWords, candidates, freshState, liveLim, pickRef, sector, windCat } from '../app/src/rules.ts';
import { createReloader } from '../app/src/reload.ts';
import { createCachedLoader } from '../app/src/cache.ts';
import { resolveSel } from '../app/src/selection.ts';
import { bucketOf, clusters, levelOf, place } from '../app/src/density.ts';

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

// ---------- densité de la carte (src/density.ts) : niveaux, hystérésis, collisions, regroupements ----------
eq('carte : niveaux loin / milieu / près', [levelOf(9), levelOf(1.5), levelOf(0.3)], ['far', 'mid', 'near']);
eq('carte : hystérésis aux seuils (pas d’aller-retour)', [levelOf(3.0, 'far'), levelOf(3.4, 'mid'), levelOf(0.75, 'near'), levelOf(0.65, 'mid')], ['far', 'mid', 'near', 'mid']);
eq('carte : palier de zoom stable aux petits pincements', [bucketOf(1.0), bucketOf(1.2, 0), bucketOf(1.6, 0)], [0, 0, 1]);
{
  // trois spots d'Hossegor à 300 m : à l'échelle « milieu » une seule pastille, les autres en points ; plus près, toutes
  const it = (id, lat, prio) => ({ id, lat, lon: -1.44, prio, sizes: [{ w: 92, h: 32 }] });
  const hs = [it('a', 43.665, 3), it('b', 43.668, 2), it('c', 43.671, 1)];
  eq('carte : collisions à l’échelle large → la priorité gagne', place(hs, 393 / 1.5), { a: 0, b: -1, c: -1 });
  eq('carte : collisions à l’échelle proche → toutes placées', place(hs, 393 / 0.01), { a: 0, b: 0, c: 0 });
  eq('carte : un obstacle (point de bouée) écarte la pastille', place([it('a', 43.665, 3)], 393 / 1.5, 3, [{ id: 'b', lat: 43.665, lon: -1.44, prio: 0, sizes: [{ w: 16, h: 16 }] }]), { a: -1 });
  const two = [{ id: 'x', lat: 43.665, lon: -1.44, prio: 2, sizes: [{ w: 92, h: 32 }] }, { id: 'y', lat: 43.6656, lon: -1.44, prio: 1, sizes: [{ w: 120, h: 44 }, { w: 30, h: 14, dy: 40 }] }];
  eq('carte : repli sur la taille suivante', place(two, 393 / 0.5), { x: 0, y: 1 });
  const cl = clusters([{ region: 'Landes', lat: 44, lon: -1.3, hs: 1 }, { region: 'Landes', lat: 43.7, lon: -1.4, hs: 2 }, { region: 'Landes', lat: 43.85, lon: -1.35, hs: null }], s => s.hs);
  eq('carte : regroupement par région (spot central, fourchette, nombre)', cl.map(c => [c.region, c.lat, c.n, c.min, c.max]), [['Landes', 43.85, 3, 1, 2]]);
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
// ---------- copie hors connexion (src/cache.ts) : réponses inversées, stockage simulé, panne ensuite (revue PR #22) ----------
{
  const mem = new Map(), store = { getItem: async k => (mem.has(k) ? mem.get(k) : null), setItem: async (k, v) => { mem.set(k, v); } };
  const q = [], get = createCachedLoader(() => { const d = deferred(); q.push(d); return d.p; }, store);
  const a = get('spots/x.json', 'cache:spot:x'), b = get('spots/x.json', 'cache:spot:x');   // deux demandes de la même fiche
  q[1].ok({ v: 'récente' }); await b;
  q[0].ok({ v: 'ancienne' }); await a;           // la réponse lente de la 1re demande arrive après
  eq('copie : une réponse plus ancienne n’écrase pas la copie plus récente', JSON.parse(mem.get('cache:spot:x')).v, 'récente');
  const c = get('spots/x.json', 'cache:spot:x'); q[2].ko(new Error('réseau'));
  const rc = await c;
  eq('copie : panne après des réponses inversées → la copie la plus récente, hors connexion', [rc.data.v, rc.offline], ['récente', true]);
  const e = get('spots/y.json', 'cache:spot:y'); q[3].ok({ v: 'y' }); await e;
  eq('copie : une autre fiche a sa propre copie', [JSON.parse(mem.get('cache:spot:y')).v, JSON.parse(mem.get('cache:spot:x')).v], ['y', 'récente']);
  const f = get('index.json', 'cache:index'), g = get('index.json', 'cache:index'), h = get('index.json', 'cache:index');
  q[5].ok({ v: 'index 2' }); await g; q[4].ok({ v: 'index 1' }); await f; q[6].ok({ v: 'index 3' }); await h;
  eq('copie : index, trois demandes dans le désordre → la plus récente est gardée', JSON.parse(mem.get('cache:index')).v, 'index 3');
  const k = get('index.json', 'cache:index'); q[7].ko(new Error('réseau')); const rk = await k;
  eq('copie : index, panne ensuite → dernier index', [rk.data.v, rk.offline], ['index 3', true]);
  let thrown = false; const z = get('bouees/z.json', 'cache:buoy:z'); q[8].ko(new Error('réseau')); try { await z; } catch { thrown = true; }
  eq('copie : ni réseau ni copie → erreur', thrown, true);
}
// ---------- sélection jour / heure de la fiche après un rechargement (src/selection.ts) ----------
{
  const H = 36e5, T0 = Date.UTC(2026, 10, 27, 23), days = n => Array.from({ length: n }, (_, d) => ({ date: `2026-11-${28 + d}`, idx: Array.from({ length: 24 }, (_, h) => d * 24 + h) }));
  eq('sélection : jour et heure choisis encore présents → gardés', resolveSel(days(7), T0, { date: '2026-11-30', ms: T0 + 60 * H }), { dayI: 2, hourI: 60 });
  eq('sélection : nouvelle série plus courte, jour choisi disparu → premier jour, heure par défaut', resolveSel(days(2), T0, { date: '2026-12-02', ms: T0 + 100 * H }), { dayI: 0, hourI: null });
  eq('sélection : série rechargée qui commence 3 h plus tard → même INSTANT (autre position)', resolveSel(days(7).map(x => ({ ...x, idx: x.idx.map(i => i - 3) })), T0 + 3 * H, { date: '2026-11-29', ms: T0 + 30 * H }), { dayI: 1, hourI: 27 });
  eq('sélection : instant choisi hors du jour → heure par défaut', resolveSel(days(7), T0, { date: '2026-11-28', ms: T0 + 30 * H }), { dayI: 0, hourI: null });
  eq('sélection : série vide → rien à afficher (pas de plantage)', resolveSel([], T0, { date: null, ms: null }), null);
}
console.log(fails ? `\nÉCHECS : ${fails}` : '\nTOUT OK');
process.exit(fails ? 1 : 0);
