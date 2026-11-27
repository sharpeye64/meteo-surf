"""Comparatif avant / après de la consommation Open-Meteo (issue #7).

    python -m tools.api_budget [--runs-cron 48] [--runs-schedule 8]

Calcule, pour une journée type, le nombre d'appels Open-Meteo :
  - AVANT : toutes les prévisions redemandées à chaque passage du robot ;
  - APRÈS : prévisions redemandées seulement quand un modèle concerné publie un nouveau run (pomcache).
Les horaires de publication viennent des métadonnées publiques d'Open-Meteo (heure du dernier run et intervalle entre
runs ; lecture non comptée dans les quotas journaliers et mensuels). Les passages du robot reproduisent le rythme mesuré :
cron-job.org toutes les 30 min (:00 et :30) et 8 passages programmés GitHub (:17, :47, :32 toutes les 3 h).
Deux hypothèses de comptage (la règle d'Open-Meteo pour plusieurs lieux dans une requête n'est pas publiée) :
  H1 « par requête » : une requête HTTP = un appel (× variables / 10 au-delà de 10 variables) ;
  H2 « par point »   : chaque lieu de la requête compte.
C'est une ESTIMATION : les vrais chiffres de chaque passage sont dans forecast.json (meta.api) et health.json.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import candhis, config, ibi_buoys, omcache, openmeteo  # noqa: E402

UTC = ZoneInfo("UTC")


def profile():
    """Requêtes d'un passage, d'après le code : (groupe, nb de requêtes, points par requête, poids H1 d'une requête)."""
    spots = json.loads(config.SPOTS_FILE.read_text(encoding="utf-8"))
    sea = len(openmeteo.grid([openmeteo.sea_point(s) for s in spots])[0])
    land = len(openmeteo.grid([(s["lat"], s["lon"]) for s in spots])[0])
    w = lambda p: omcache.weight(p)[2]
    marine_vars = "wave_height,wave_period,wave_direction,swell_wave_height,swell_wave_period,swell_wave_direction,secondary_swell_wave_height,secondary_swell_wave_period,secondary_swell_wave_direction,wind_wave_height,wind_wave_period,wind_wave_direction,sea_level_height_msl,sea_surface_temperature"
    rows = [("marine", 1, sea, w({"hourly": marine_vars, "forecast_days": 7}))]
    # AVANT (main, 27/11/2026) : une seule requête vent pour les 4 modèles, soleil compris (20 variables)
    before_wind = ("wind+sun (avant)", 1, land, w({"hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m", "daily": "sunrise,sunset",
                                                   "models": ",".join(m[2] for m in config.WIND_MODELS), "forecast_days": 7}))
    rows += [(f"wave_{k}", 1, sea, w({"hourly": "wave_height,wave_period,wave_direction", "forecast_days": 7})) for k, *_ in config.WAVE_MODELS]
    rows += [(f"wind_{k}", 1, land, w({"hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m", "models": api, "forecast_days": 7}))
             for k, _l, api in config.WIND_MODELS]
    rows.append(("sun", 1, land, w({"daily": "sunrise,sunset", "forecast_days": 7})))
    n_pts = len(ibi_buoys.STATIONS) + 1   # bouées du large + Gascogne : prévision au point de la bouée
    rows.append(("point", n_pts, 1, w({"hourly": "wave_height,wave_period,swell_wave_period,wave_direction", "forecast_days": 2, "past_days": 2})))
    arch = len(config.WAVE_MODELS) + len(candhis.STATIONS) + len(ibi_buoys.STATIONS)   # archive : un passage sur trois, inchangée
    return rows, before_wind, sea, land, n_pts, arch


def passes(day, cron, schedule):
    t0 = datetime(day.year, day.month, day.day, tzinfo=UTC)
    out = [t0 + timedelta(minutes=30 * i) for i in range(cron)]
    sched = [(0, 17), (1, 47), (2, 32)]
    out += [t0 + timedelta(hours=h + 3 * k, minutes=m) for k in range(8) for h, m in sched][:schedule]
    return sorted(out)


def events(watch, day):
    """Heures de disponibilité des runs sur la journée, d'après le dernier run connu et l'intervalle entre runs."""
    ev = []
    for kind, name in watch:
        m = omcache.model_meta(kind, name) or {}
        a, step = m.get("last_run_availability_time"), m.get("update_interval_seconds")
        if not a or not step:
            continue
        t = datetime.fromtimestamp(a, UTC)
        start = datetime(day.year, day.month, day.day, tzinfo=UTC) - timedelta(days=1)
        while t > start:
            t -= timedelta(seconds=step)
        while t < start + timedelta(days=2):
            ev.append(t)
            t += timedelta(seconds=step)
    return sorted(ev)


def simulate(watch, ps, ttl_h):
    """Nombre de requêtes d'un groupe sur la journée avec la règle du cache (nouveau run, run pas encore posé, jour, 6 h)."""
    ev = events(watch, ps[0])
    n, last, pending = 0, None, False
    for i, p in enumerate(ps):
        prev = ps[i - 1] if i else p - timedelta(minutes=30)
        new = any(prev < e <= p for e in ev)
        local_day = lambda t: t.astimezone(ZoneInfo(config.TIMEZONE)).date()
        if last is None or new or pending or local_day(p) != local_day(last) or (p - last).total_seconds() > ttl_h * 3600:
            n += 1
            last = p
            pending = any(p - timedelta(seconds=omcache.SETTLE_S) < e <= p for e in ev)   # run pas encore posé : redemandé une fois
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-cron", type=int, default=48)
    ap.add_argument("--runs-schedule", type=int, default=8)
    a = ap.parse_args()
    rows, before_wind, sea, land, n_pts, arch = profile()
    day = datetime.now(UTC) + timedelta(days=1)
    ps = passes(day, a.runs_cron, a.runs_schedule)
    R = len(ps)
    print(f"Journée type : {R} passages du robot ({a.runs_cron} cron-job.org + {a.runs_schedule} programmés) ; "
          f"{sea} points mer, {land} points terre, {n_pts} bouées au point ; archive {arch} requêtes × 8 passages (inchangée)\n")
    print("| Groupe | Requêtes par passage | Points | AVANT (requêtes/jour) | APRÈS (requêtes/jour) | AVANT H1 | APRÈS H1 | AVANT H2 | APRÈS H2 |")
    print("|---|---|---|---|---|---|---|---|---|")
    tot = dict(bq=0, aq=0, b1=0, a1=0, b2=0, a2=0)
    wind_after = {"wind_arome", "wind_icon", "wind_gfs", "wind_ecmwf", "sun"}
    for g, nreq, pts, w in [before_wind] + rows:
        if g == "wind+sun (avant)":
            after, R_g = 0, R     # remplacée par les 4 requêtes par modèle + le soleil
        else:
            after = simulate(omcache.WATCH["point" if g == "point" else g], ps, omcache.TTL_H.get(g, omcache.TTL_MAX_H))
            R_g = 0 if g in wind_after else R   # n'existaient pas avant
        bq, aq = nreq * R_g, nreq * after
        b1, a1, b2, a2 = bq * w, aq * w, bq * w * pts, aq * w * pts
        for k, v in zip(tot, (bq, aq, b1, a1, b2, a2)):
            tot[k] += v
        print(f"| {g} | {nreq} | {pts} | {bq} | {aq} | {b1:.0f} | {a1:.0f} | {b2:.0f} | {a2:.0f} |")
    ar = arch * 8
    for k in tot:
        tot[k] += ar
    print(f"| archive (inchangée) | {arch} | 1 | {ar} | {ar} | {ar} | {ar} | {ar} | {ar} |")
    print(f"| **Total / jour** | | | **{tot['bq']}** | **{tot['aq']}** | **{tot['b1']:.0f}** | **{tot['a1']:.0f}** | **{tot['b2']:.0f}** | **{tot['a2']:.0f}** |")
    print(f"\nLimite gratuite : 10 000 appels/jour, 300 000/mois. H1 : {tot['b1']:.0f} → {tot['a1']:.0f} ; "
          f"H2 : {tot['b2']:.0f} → {tot['a2']:.0f} (÷ {tot['b2'] / max(tot['a2'], 1):.1f}). "
          f"Par mois (×30) : H2 {tot['b2'] * 30 / 1e6:.2f} M → {tot['a2'] * 30 / 1e6:.2f} M.")
    archive_budget(ps)
    print(f"Métadonnées lues : {omcache.META_CHECKS}")


def archive_budget(ps):
    """Archive aux points des bouées (issue #1). AVANT : à CHAQUE passage d'une heure UTC multiple de 3 (souvent 2 ou 3 par
    heure : d'où les doublons), 1 requête par bouée (best match) + 1 par modèle à Gascogne. APRÈS : premier passage de l'heure
    seulement, 1 requête groupée par modèle (22 bouées), via le cache (nouveau run, nouveau jour, 6 h)."""
    n_b = len(candhis.STATIONS) + len(ibi_buoys.STATIONS)
    arch = [p for p in ps if p.hour % 3 == 0]
    first = []
    for p in arch:
        if not first or (p.date(), p.hour) != (first[-1].date(), first[-1].hour):
            first.append(p)
    before_q = len(arch) * (n_b + len(config.WAVE_MODELS))
    groups = [("buoys_marine", "marine", 3)] + [(f"buoys_wave_{k}", f"wave_{k}", 1) for k, *_ in config.WAVE_MODELS]
    after_q = after_pts = 0
    rows = []
    for g, w, nv in groups:
        n = simulate(omcache.WATCH[g], first, omcache.TTL_MAX_H)
        after_q += n
        after_pts += n * (n_b + 1)
        rows.append(f"{g} {n}")
    print(f"\nArchive (issue #1) : {len(arch)} passages d'archive par jour, dont {len(first)} premiers de leur heure.")
    print(f"  AVANT : {before_q} requêtes/jour = {before_q} points (H1 = H2 = {before_q}) ; doublons : {len(arch) - len(first)} passages/jour en trop")
    print(f"  APRÈS : {after_q} requêtes/jour ({', '.join(rows)}) ; H1 = {after_q}, H2 = {after_pts} (22 points par requête)")
    print(f"  Écart : H1 {after_q - before_q:+d}/jour ; H2 {after_pts - before_q:+d}/jour (limite gratuite 10 000/jour)")


if __name__ == "__main__":
    main()
