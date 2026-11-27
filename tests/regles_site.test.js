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
const src = ['rad', 'sectors', 'sector', 'angDiff', 'windInfo', 'pvLim', 'pvFresh', 'hav', 'BUOY_ONLY', 'nearestCoast', 'buoyChoices', 'LANDES_CF_KM', 'prefRank', 'pickBuoy']
  .map(grab).join('\n');
const ctx = { state: {}, stampTxt: t => 'le ' + t, dmy: t => t, tDate: t => new Date(t), Math, Date, JSON };
vm.createContext(ctx);
vm.runInContext(src + '\nthis.F={windInfo,pvFresh,buoyChoices,pickBuoy,sector};', ctx);
const F = ctx.F;

let fails = 0;
const eq = (name, got, want) => { const ok = JSON.stringify(got) === JSON.stringify(want); if (!ok) fails++; console.log(`[${ok ? 'OK' : 'ÉCHEC'}] ${name} : ${JSON.stringify(got)}${ok ? '' : ' (attendu ' + JSON.stringify(want) + ')'}`); };
const NOW = Date.now(), at = h => new Date(NOW - h * 36e5).toISOString();

for (const f of C.fresh) {
  if (f.silent || f.lim) continue;   // le site n'a ni l'indicateur « muette » ni le « lim » du robot : il déduit la cadence de l'identifiant
  eq(`fraîcheur ${f.id} ${f.age} h`, F.pvFresh(f.age, at(f.age), f.id).c, f.want);
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
console.log(fails ? `\nÉCHECS : ${fails}` : '\nTOUT OK');
process.exit(fails ? 1 : 0);
