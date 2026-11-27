// Test des heures de l'APPLICATION (issue #2), sans réseau :   node tests/heures_app.test.mjs   (Node ≥ 23 : lit le .ts)
// Lancé sous plusieurs fuseaux de téléphone (TZ=…) : mêmes résultats partout, mêmes instants que le site et le robot.
import { hhIn, partsIn, placeTz, tMs } from '../app/src/time.ts';

let fails = 0;
const eq = (name, got, want) => { const ok = JSON.stringify(got) === JSON.stringify(want); if (!ok) fails++; console.log(`[${ok ? 'OK' : 'ÉCHEC'}] ${name} : ${JSON.stringify(got)}${ok ? '' : ' (attendu ' + JSON.stringify(want) + ')'}`); };
const Z = (y, mo, d, h, mi = 0) => Date.UTC(y, mo - 1, d, h, mi);
const devTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
console.log('fuseau du téléphone simulé :', devTz);
if (process.env.TZ && process.platform === 'linux' && devTz !== process.env.TZ) { console.error('le fuseau demandé n’est pas appliqué'); process.exit(1); }

eq('nouveau format : Lacanau 10 h = Ericeira 9 h (même instant)', [tMs('2026-11-27T10:00+01:00'), tMs('2026-11-27T09:00+00:00')], [Z(2026, 11, 27, 9), Z(2026, 11, 27, 9)]);
eq('ancien format = heure de Paris (hiver, été)', [tMs('2026-11-27T10:00'), tMs('2026-07-01T10:00')], [Z(2026, 11, 27, 9), Z(2026, 7, 1, 8)]);
eq('heure répétée du 25/10 : ancien format → la première ; avec décalage → distinctes', [tMs('2026-10-25T02:30'), tMs('2026-10-25T02:30+02:00'), tMs('2026-10-25T02:30+01:00')], [Z(2026, 10, 25, 0, 30), Z(2026, 10, 25, 0, 30), Z(2026, 10, 25, 1, 30)]);
eq('heure inexistante du 29/03 (ancien format) : décalage d’avant', tMs('2026-03-29T02:30'), Z(2026, 3, 29, 1, 30));
eq('fuseaux', [placeTz({ region: 'Portugal Sud' }), placeTz({ region: 'Gironde' }), placeTz({ tz: 'Europe/Madrid', region: 'Galice' })], ['Europe/Lisbon', 'Europe/Paris', 'Europe/Madrid']);
const i = Z(2026, 11, 27, 23, 30);
eq('même instant, jour local différent à minuit (Lisbonne / Paris)', [partsIn(i, 'Europe/Lisbon').date, partsIn(i, 'Europe/Paris').date], ['2026-11-27', '2026-11-28']);
eq('libellé d’heure au fuseau du spot', [hhIn(Z(2026, 11, 27, 9, 30), 'Europe/Lisbon'), hhIn(Z(2026, 11, 27, 9), 'Europe/Paris')], ['9 h 30', '10 h']);
// frise horaire d'une fiche : 48 h à partir de t0 (minuit local) au passage à l'heure d'hiver : 25 h le 25/10 à Paris
const t0 = tMs('2026-10-25T00:00+02:00'), hours = Array.from({ length: 26 }, (_, k) => partsIn(t0 + k * 36e5, 'Europe/Paris'));
eq('25/10 à Paris : 02 h apparaît deux fois, la journée compte 25 heures', [hours.filter(p => p.date === '2026-10-25').length, hours.filter(p => p.date === '2026-10-25' && p.h === 2).length], [25, 2]);
const t1 = tMs('2026-03-29T00:00+01:00'), spring = Array.from({ length: 24 }, (_, k) => partsIn(t1 + k * 36e5, 'Europe/Paris'));
eq('29/03 à Paris : 02 h n’existe pas, la journée compte 23 heures', [spring.filter(p => p.date === '2026-03-29').length, spring.some(p => p.date === '2026-03-29' && p.h === 2)], [23, false]);
console.log(fails ? `\nÉCHECS : ${fails}` : '\nTOUT OK');
process.exit(fails ? 1 : 0);
