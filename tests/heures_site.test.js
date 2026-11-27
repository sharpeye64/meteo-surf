// Test des heures du SITE (issue #2), sans réseau :   node tests/heures_site.test.js
// Lancé sous plusieurs fuseaux d'APPAREIL (TZ=Europe/Paris, Europe/Lisbon, America/New_York, Asia/Tokyo) : les résultats
// doivent être identiques. Les fonctions sont lues directement dans web/index.html (bloc « CONTRAT HORAIRE »).
const fs = require('fs'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'web', 'index.html'), 'utf8');
const a = html.indexOf('// ===== CONTRAT HORAIRE (issue #2) ====='), b = html.indexOf('function fcStaleNote(){');
if (a < 0 || b < a) { console.error('bloc CONTRAT HORAIRE introuvable'); process.exit(1); }
const src = html.slice(a, b) + `
const DAYS_LONG=['dimanche','lundi','mardi','mercredi','jeudi','vendredi','samedi'];
` + html.match(/function stampTxt\(t\)\{[\s\S]*?\n\}/)[0] + `
const hoKey=${html.match(/const hoKey=(t=>\{[^\n]*?\};)/)[1].replace(/;$/, '')};
${html.match(/const hoP=[^\n]*/)[0]}
${html.match(/const hoHrTxt=[^\n]*/)[0]}
module.exports={tMs,tKey,tOffMin,placeTz,tzNow,tzParts,stampTxt,hoKey,hoP,hoHrTxt};`;
const m = { exports: {} }; new Function('module', src)(m);
const T = m.exports;
let fails = 0;
const eq = (name, got, want) => { const ok = JSON.stringify(got) === JSON.stringify(want); if (!ok) fails++; console.log(`[${ok ? 'OK' : 'ÉCHEC'}] ${name} : ${JSON.stringify(got)}${ok ? '' : ' (attendu ' + JSON.stringify(want) + ')'}`); };
const Z = (y, mo, d, h, mi = 0) => Date.UTC(y, mo - 1, d, h, mi);
const devTz = Intl.DateTimeFormat().resolvedOptions().timeZone; console.log('fuseau de l’appareil :', devTz);
if (process.env.TZ && process.platform === 'linux' && devTz !== process.env.TZ) { console.error('le fuseau demandé n’est pas appliqué'); process.exit(1); }

eq('nouveau format, Paris hiver', T.tMs('2026-11-27T10:00+01:00'), Z(2026, 11, 27, 9));
eq('nouveau format, Lisbonne (même instant que 10 h à Paris)', T.tMs('2026-11-27T09:00+00:00'), Z(2026, 11, 27, 9));
eq('ancien format (sans décalage) = heure de Paris, hiver', T.tMs('2026-11-27T10:00'), Z(2026, 11, 27, 9));
eq('ancien format = heure de Paris, été', T.tMs('2026-07-01T10:00'), Z(2026, 7, 1, 8));
eq('heure répétée du 25/10 (ancien format) : la première (+02:00)', T.tMs('2026-10-25T02:30'), Z(2026, 10, 25, 0, 30));
eq('heure répétée du 25/10 avec décalage : la seconde (+01:00) reste distincte', T.tMs('2026-10-25T02:30+01:00'), Z(2026, 10, 25, 1, 30));
eq('heure inexistante du 29/03 (ancien format) : décalage d’avant', T.tMs('2026-03-29T02:30'), Z(2026, 3, 29, 1, 30));
eq('même clé absolue pour Lacanau 10 h et Ericeira 9 h', T.tKey('2026-11-27T10:00+01:00') === T.tKey('2026-11-27T09:00+00:00'), true);
eq('carte : clé absolue (UTC), affichée à l’heure de Paris, pour une heure de Lisbonne', [T.hoKey('2026-11-27T09:00+00:00'), T.hoP(T.hoKey('2026-11-27T09:00+00:00')).h], ['2026-11-27T09', 10]);
eq('décalage lu dans la chaîne', [T.tOffMin('2026-11-27T09:00+00:00'), T.tOffMin('2026-07-01T10:00+02:00'), T.tOffMin('2026-11-27T10:00')], [0, 120, 60]);
eq('fuseau des spots', [T.placeTz({ region: 'Portugal Centre' }), T.placeTz({ region: 'Landes' }), T.placeTz({ tz: 'Europe/Madrid' })], ['Europe/Lisbon', 'Europe/Paris', 'Europe/Madrid']);
eq('parties d’un instant à Lisbonne et à Paris', [T.tzParts(Z(2026, 11, 27, 9), 'Europe/Lisbon').h, T.tzParts(Z(2026, 11, 27, 9), 'Europe/Paris').h], [9, 10]);
eq('jour changé à minuit selon le lieu', [T.tzParts(Z(2026, 11, 27, 23, 30), 'Europe/Lisbon').date, T.tzParts(Z(2026, 11, 27, 23, 30), 'Europe/Paris').date], ['2026-11-27', '2026-11-28']);
// date d'une mesure, jugée à l'heure du LIEU : 28/11 à 0 h 30 à Paris = 27/11 à 23 h 30 à Lisbonne
const realNow = Date.now;
Date.now = () => Z(2026, 11, 27, 23, 30);
eq('mesure de Lisbonne 22 h : « aujourd’hui » (il est 23 h 30 à Lisbonne)', T.stampTxt('2026-11-27T22:00+00:00'), 'aujourd’hui 22h');
eq('mesure de Paris 23 h la veille : « hier » (il est 0 h 30 à Paris)', T.stampTxt('2026-11-27T23:00+01:00'), 'hier 23h');
Date.now = realNow;

// Non-régression revue PR #17 (B) : carte de l'accueil la nuit du passage à l'heure d'hiver. Avant, la clé était l'heure de
// Paris : les deux « 2 h » du 25/10 se confondaient (un créneau perdu, l'autre ambigu).
const night = ['2026-10-25T01:00+02:00', '2026-10-25T02:00+02:00', '2026-10-25T02:00+01:00', '2026-10-25T03:00+01:00'];
const keys = night.map(T.hoKey);
eq('B. 25/10 : 4 heures publiées → 4 clés distinctes (aucun créneau perdu)', new Set(keys).size, 4);
eq('B. clés dans l’ordre des instants', [...keys].sort().join() === keys.join(), true);
const dayKeys = Array.from({ length: 25 }, (_, k) => new Date(Date.UTC(2026, 9, 24, 22) + k * 36e5).toISOString().slice(0, 13));
eq('B. journée du 25/10 : 25 créneaux, tous datés du 25/10 à Paris', dayKeys.filter(k => T.hoP(k).date === '2026-10-25').length, 25);
eq('B. les deux « 2 h » sont libellées sans ambiguïté', [T.hoHrTxt(keys[1], dayKeys), T.hoHrTxt(keys[2], dayKeys), T.hoHrTxt(keys[3], dayKeys)], ['2h (UTC+2)', '2h (UTC+1)', '3h']);
eq('B. Lacanau 11 h et Supertubos 10 h : même créneau', T.hoKey('2026-11-27T11:00+01:00') === T.hoKey('2026-11-27T10:00+00:00'), true);
console.log(fails ? `\nÉCHECS : ${fails}` : '\nTOUT OK');
process.exit(fails ? 1 : 0);
