// Règles métier du SITE (issue #4) sur les cas communs tests/regles_communes.json, sans réseau ni navigateur :
//   node tests/regles_site.test.js
// Les fonctions sont extraites telles quelles de web/index.html (aucune copie) : pvLim, pvFresh, windInfo, hav,
// nearestCoast, buoyChoices, prefRank, pickBuoy. Les mêmes cas sont joués sur l'appli et le robot.
const fs = require('fs'), path = require('path'), vm = require('vm');
const html = fs.readFileSync(process.env.REGLES_HTML || path.join(__dirname, '..', 'web', 'index.html'), 'utf8');   // REGLES_HTML : autre version du site (comparaison)
const C = JSON.parse(fs.readFileSync(path.join(__dirname, 'regles_communes.json'), 'utf8'));

/** Source d'une fonction « function nom(…){…} » (accolades équilibrées) ou d'une ligne « const nom=… ». */
function grab(name) {
  let i = html.indexOf(`function ${name}(`);
  if (i < 0) { const m = html.match(new RegExp(`^(const|let) ${name}\\s*=.*$`, 'm')); if (!m) throw new Error('introuvable : ' + name); return m[0]; }
  let j = html.indexOf('{', i), depth = 0;
  for (; j < html.length; j++) { if (html[j] === '{') depth++; else if (html[j] === '}' && --depth === 0) break; }
  return html.slice(i, j + 1);
}
const src = ['rad', 'sectors', 'sector', 'angDiff', 'clamp', 'windInfo', 'tideFactor', 'spotOff', 'analyse', 'pvLim', 'pvSilent', 'pvUsable', 'pvFresh', 'hav', 'BUOY_ONLY', 'nearestCoast', 'buoyChoices', 'LANDES_CF_KM', 'prefRank', 'pickBuoy']
  .map(grab).join('\n');
const ctx = { state: {}, stampTxt: t => 'le ' + t, dmy: t => t, tDate: t => new Date(t), summarise: d => ({ date: d }), Math, Date, JSON, Number, Object };
vm.createContext(ctx);
vm.runInContext(src + '\nthis.F={windInfo,pvFresh,buoyChoices,pickBuoy,sector,analyse};', ctx);
const F = ctx.F;

let fails = 0;
const eq = (name, got, want) => { const ok = JSON.stringify(got) === JSON.stringify(want); if (!ok) fails++; console.log(`[${ok ? 'OK' : 'ÉCHEC'}] ${name} : ${JSON.stringify(got)}${ok ? '' : ' (attendu ' + JSON.stringify(want) + ')'}`); };
const NOW = Date.now(), at = h => (h == null ? 'heure illisible' : new Date(NOW - h * 36e5).toISOString());
const age = a => (a == null ? NaN : a);

for (const f of C.fresh) {
  if (f.silent || f.lim) continue;   // le site n'a ni l'indicateur « muette » ni le « lim » du robot : il déduit la cadence de l'identifiant
  eq(`fraîcheur ${f.id} ${f.age} h`, F.pvFresh(age(f.age), at(f.age), f.id).c, f.want);
}
for (const x of C.sector) eq(`secteur ${x.deg}°`, F.sector(x.deg), x.want);
for (const w of C.wind) eq(`vent ${w.v} km/h du ${w.wdir}° (plage vers ${w.ori}°)`, F.windInfo(w.v, w.wdir, w.ori == null ? null : (w.ori + 180) % 360).label ?? null, w.want);

for (const p of C.pick) {
  const st = { coast: [], offshore: [], gascogne: null, radarView: {} };
  for (const [id, a] of Object.entries(p.ages)) {
    const s = C.stations.find(x => x.id === id), o = typeof a === 'object' ? a : { age: a };
    const b = { id: s.id, name: s.name, sub: s.sub, lat: s.lat, lon: s.lon, silent: !!o.silent, latest: { time: at(o.age), hs: 'hs' in o ? o.hs : 1.2 }, obs: [], model: [] };
    if (s.kind === 'gascogne') st.gascogne = b; else st[s.kind === 'coast' ? 'coast' : 'offshore'].push(b);
  }
  ctx.state = st;
  vm.runInContext('this.R=(s=>{ const l=buoyChoices(s), c=pickBuoy(l); return {id:c?c.key:null, cands:l.map(o=>o.key)}; })(this.SPOT)', Object.assign(ctx, { SPOT: p.spot }));
  eq(`bouée : ${p.case}`, ctx.R.id, p.want);
  if (p.cands) eq(`  candidates : ${p.case}`, [...ctx.R.cands].sort(), [...p.cands].sort());
}
// ---------- vent dans le VRAI calcul des heures (analyse), pas seulement windInfo (revue PR #22) ----------
const hours = 4, times = Array.from({ length: hours }, (_, i) => `2026-11-27T1${i}:00+01:00`);
const m = { hourly: { time: times, wave_height: [1.2, 1.2, 1.2, 1.2], wave_period: [10, 10, 10, 10], wave_direction: [290, 290, 290, 290] } };
const w = { hourly: { wind_speed_10m: [20, 20, 5, null], wind_direction_10m: [90, 270, 90, 90] } };
const spot = ori => ({ name: 'Test', ori, min: 0.6, max: 2.5, tide: 'Toutes' });
eq('analyse : plage vers 270° → offshore, onshore, lisse, vitesse absente', F.analyse(spot(270), m, w).hours.map(h => h.wind ?? null), ['offshore', 'onshore', 'lisse', null]);
eq('analyse : orientation absente (null) → aucune qualification (avant : comptée 180°)', F.analyse(spot(null), m, w).hours.map(h => h.wind ?? null), [null, null, null, null]);
eq('analyse : orientation non renseignée (undefined) → aucune qualification (avant : NaN)', F.analyse(spot(undefined), m, w).hours.map(h => h.wind ?? null), [null, null, null, null]);
// ---------- pastilles : une bouée muette l'est partout (carte, survol, panneau), quel que soit l'âge de sa dernière mesure ----------
ctx.state = { coast: [{ id: '03302', silent: true }], offshore: [] };
eq('pastille : bouée muette avec une mesure récente → indisponible, « aucune mesure depuis »', [F.pvFresh(0.5, '2026-11-27T10:00+01:00', '03302').c, /aucune mesure depuis/.test(F.pvFresh(0.5, '2026-11-27T10:00+01:00', '03302').t)], ['off', true]);
eq('pastille : heure dans le futur → « heure incohérente » ; illisible → « heure inconnue »', [F.pvFresh(-1, 'x', '06402').t, F.pvFresh(NaN, 'x', '06402').t], ['heure incohérente', 'heure inconnue']);
// ---------- choix fait à la main : respecté, même pour une bouée muette ----------
ctx.state = { coast: [{ id: '03302', name: 'Cap Ferret', lat: 44.6525, lon: -1.4467, silent: true, latest: { time: at(60), hs: 1 }, obs: [] }], offshore: [],
  gascogne: { lat: 45.2, lon: -5, latest: { time: at(1), hs: 2 }, obs: [], model: [] }, radarView: { Lacanau: '03302' } };
vm.runInContext('this.R=pickBuoy(buoyChoices(this.SPOT)).key', Object.assign(ctx, { SPOT: C.pick[0].spot }));
eq('choix fait à la main : Cap Ferret muette reste affichée si on l’a choisie', ctx.R, '03302');
console.log(fails ? `\nÉCHECS : ${fails}` : '\nTOUT OK');
process.exit(fails ? 1 : 0);
