"""Contrôle du site généré AVANT publication (issue #3).

    python -m tools.check_site _site --max-age-h 3

Refuse (code de sortie 1) un site incomplet, incohérent ou contenant des données de test. Les quantités attendues sont
dérivées du catalogue (pipeline/spots.json), de la configuration (zones, pages) et des données réelles du passage
(bouées présentes dans forecast.json), jamais d'un nombre figé. Une PANNE DE SOURCE (une bouée, MARC, Météo-France…) est
tolérée et signalée en avertissement ; un ARTEFACT INCOMPLET (pages, fiches de l'appli, sitemap, JSON invalides) bloque.
Si le contrôle échoue, le workflow s'arrête avant l'envoi : GitHub Pages garde la dernière version publiée.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# erreurs du robot qui signifient un artefact incomplet (les autres clés de meta.errors sont des pannes de source tolérées)
GENERATION_ERRORS = ("appdata", "seo", "seo_bouees", "seo_zones")
TEST_MARK = 'name="houlalah-test"'
SECRET_RE = re.compile(r"(?i)(apikey|api_key|token|password|secret)[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9_\-]{12,}")


def _json(path, errors, label):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{label} absent ({path.name})")
    except Exception as e:
        errors.append(f"{label} : JSON invalide ({str(e)[:80]})")
    return None


def check(site_dir, max_age_h=3.0):
    """Retourne (ok, rapport). rapport = {errors, warnings, counts}."""
    from pipeline import bouees, config, pages, zones
    from pipeline.seo import paris_now, slugify
    d = Path(site_dir)
    errors, warnings, counts = [], [], {}
    site = config.SITE_URL

    # 1. données des prévisions
    fc = _json(d / "data" / "forecast.json", errors, "forecast.json")
    catalogue = json.loads(config.SPOTS_FILE.read_text(encoding="utf-8"))
    exp_spots = {slugify(s["name"]) for s in catalogue}
    counts["spots_catalogue"] = len(exp_spots)
    if fc:
        meta = fc.get("meta") or {}
        if meta.get("_test"):
            errors.append("forecast.json : données de test (meta._test)")
        got = {slugify(s.get("name", "")) for s in fc.get("spots") or []}
        counts["spots_forecast"] = len(got)
        if got != exp_spots:
            errors.append(f"forecast.json : spots différents du catalogue (manquants {sorted(exp_spots - got)[:5]}, en trop {sorted(got - exp_spots)[:5]})")
        try:
            from datetime import datetime
            age = (paris_now() - datetime.strptime(meta["generated"][:16], "%Y-%m-%dT%H:%M")).total_seconds() / 3600
            counts["age_h"] = round(age, 2)
            if max_age_h is not None and not (-0.5 <= age <= max_age_h):
                errors.append(f"forecast.json : généré il y a {age:.1f} h (maximum {max_age_h} h)")
        except Exception:
            errors.append("forecast.json : heure de génération illisible")
        for k, v in (meta.get("errors") or {}).items():
            (errors if k in GENERATION_ERRORS else warnings).append(f"robot : {k} — {str(v)[:120]}")

    # 2. données de l'application
    idx = _json(d / "data" / "app" / "index.json", errors, "appli index.json")
    if idx:
        if idx.get("_test"):
            errors.append("appli : données de test (_test)")
        aslugs = {s.get("slug") for s in idx.get("spots") or []}
        counts["app_spots"] = len(aslugs)
        if aslugs != exp_spots:
            errors.append(f"appli : spots différents du catalogue ({len(aslugs)} / {len(exp_spots)})")
        if fc and idx.get("generated") != (fc.get("meta") or {}).get("generated"):
            errors.append("appli : génération différente de forecast.json")
        for s in aslugs:
            if s and not _json(d / "data" / "app" / "spots" / f"{s}.json", errors, f"appli fiche spot {s}"):
                break
        for b in idx.get("buoys") or []:
            if not _json(d / "data" / "app" / "bouees" / f"{b.get('slug')}.json", errors, f"appli fiche bouée {b.get('slug')}"):
                break

    # 3. pages : adresses attendues dérivées du catalogue, des zones, des pages de texte et des bouées réelles
    regions = {s["region"] for s in catalogue}
    exp_paths = {"spots"} | {f"spots/{s}" for s in exp_spots} | {z["slug"] for z in zones.ZONES if z["key"] in regions} | {p["slug"] for p in pages.ALL}
    if fc:
        bl = bouees.collect(fc)
        if bl:
            exp_paths |= {"bouees"} | {f"bouees/{b['slug']}" for b in bl}
        counts["buoy_pages_expected"] = len(bl)
    counts["pages_expected"] = len(exp_paths)
    missing = [p for p in sorted(exp_paths) if not (d / p / "index.html").exists()]
    if missing:
        errors.append(f"pages absentes : {len(missing)} (ex. {missing[:4]})")
    bad_canon, marked, local = [], [], []
    for p in sorted(exp_paths - set(missing)):
        h = (d / p / "index.html").read_text(encoding="utf-8")
        m = re.search(r'<link rel="canonical" href="([^"]+)"', h)
        if not m or m.group(1) != f"{site}/{p}/":
            bad_canon.append(p)
        if TEST_MARK in h:
            marked.append(p)
        if "localhost" in h or "127.0.0.1" in h:
            local.append(p)
    if bad_canon:
        errors.append(f"canoniques incorrectes : {len(bad_canon)} (ex. {bad_canon[:3]})")
    if marked:
        errors.append(f"pages de test (marque houlalah-test) : {len(marked)} (ex. {marked[:3]})")
    if local:
        errors.append(f"adresses locales dans les pages : {len(local)} (ex. {local[:3]})")
    # pages générées en trop (reste d'une ancienne génération ou d'un test)
    extra = [str(f.parent.relative_to(d)).replace("\\", "/") for sub in ("spots", "bouees") if (d / sub).exists() for f in (d / sub).glob("*/index.html")]
    extra = [p for p in extra if p not in exp_paths]
    if extra:
        errors.append(f"pages inattendues : {len(extra)} (ex. {extra[:3]})")

    # 4. sitemap : exactement les pages attendues, toutes sur l'adresse publique
    try:
        locs = re.findall(r"<loc>([^<]+)</loc>", (d / "sitemap.xml").read_text(encoding="utf-8"))
        counts["sitemap"] = len(locs)
        exp_urls = {f"{site}/"} | {f"{site}/{p}/" for p in exp_paths}
        if set(locs) != exp_urls:
            errors.append(f"sitemap : {len(set(locs) - exp_urls)} adresse(s) en trop, {len(exp_urls - set(locs))} manquante(s)")
        if len(locs) != len(set(locs)):
            errors.append("sitemap : adresses en double")
        if any(not u.startswith(site + "/") for u in locs):
            errors.append("sitemap : adresse hors du site public")
    except FileNotFoundError:
        errors.append("sitemap.xml absent")
    for f in ("robots.txt", "index.html"):
        if not (d / f).exists():
            errors.append(f"{f} absent")

    # 5. rapport de santé : présent, sans secret
    hp = d / "health.json"
    hj = _json(hp, errors, "health.json")
    if hj is not None:
        if hj.get("_test"):
            errors.append("health.json : données de test")
        if SECRET_RE.search(hp.read_text(encoding="utf-8")):
            errors.append("health.json : ressemble à un secret (refusé)")
    return (not errors), {"errors": errors, "warnings": warnings, "counts": counts}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("site_dir")
    ap.add_argument("--max-age-h", type=float, default=3.0)
    a = ap.parse_args()
    ok, rep = check(a.site_dir, a.max_age_h)
    lines = [f"## Contrôle avant publication : {'OK' if ok else 'REFUSÉ'}", "", "Compteurs : " + ", ".join(f"{k} {v}" for k, v in rep["counts"].items())]
    lines += [f"- ❌ {e}" for e in rep["errors"]] + [f"- ⚠️ {w}" for w in rep["warnings"]]
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    for e in rep["errors"]:
        print(f"::error::{e}")
    for w in rep["warnings"]:
        print(f"::warning::{w}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
